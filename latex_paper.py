"""AASTeX PDF assembly (Stage 13 support).

Takes the section dict from paper.assemble_paper_with_results (or the plain
markdown string from paper.assemble_paper) plus a list of real figures and
renders an actual AASTeX-formatted (American Astronomical Society journal
class) LaTeX document, then compiles it to PDF with pdflatex. This is the
first place in this repo that produces a PDF -- everything upstream only
ever wrote markdown.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

AASTEX_CLASS = "aastex701"


def _escape_latex(text: str) -> str:
    # Backslash first, then the rest, so we don't double-escape our own
    # inserted backslashes.
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    # LLM-written prose routinely includes raw Unicode symbols (Greek
    # letters, dashes, primes) that the default LaTeX text font can't
    # render as plain glyphs -- map the common astronomy ones to their
    # math-mode LaTeX equivalents rather than depending on a specific
    # Unicode-complete font being installed. Done after the ASCII escaping
    # pass above so the inserted "$...$" isn't itself re-escaped.
    unicode_replacements = [
        ("α", r"$\alpha$"), ("β", r"$\beta$"), ("γ", r"$\gamma$"), ("δ", r"$\delta$"),
        ("ε", r"$\epsilon$"), ("θ", r"$\theta$"), ("λ", r"$\lambda$"), ("μ", r"$\mu$"),
        ("ν", r"$\nu$"), ("π", r"$\pi$"), ("ρ", r"$\rho$"), ("σ", r"$\sigma$"),
        ("τ", r"$\tau$"), ("φ", r"$\phi$"), ("χ", r"$\chi$"), ("ψ", r"$\psi$"), ("ω", r"$\omega$"),
        ("Δ", r"$\Delta$"), ("Σ", r"$\Sigma$"), ("Ω", r"$\Omega$"),
        ("⊙", r"$\odot$"),
        ("≳", r"$\gtrsim$"), ("≲", r"$\lesssim$"), ("≥", r"$\geq$"), ("≤", r"$\leq$"),
        ("≈", r"$\approx$"), ("≡", r"$\equiv$"),
        ("±", r"$\pm$"), ("×", r"$\times$"), ("→", r"$\rightarrow$"), ("√", r"$\sqrt{}$"),
        ("°", r"$^\circ$"),
        ("′", r"$^\prime$"),
        ("″", r"$^{\prime\prime}$"),
        ("–", "--"),
        ("—", "---"),
        ("−", "-"),
    ]
    for old, new in unicode_replacements:
        text = text.replace(old, new)
    # Unicode superscript/subscript digits and signs (routinely used for
    # exponents/isotope labels like 10^-3 or H_2 in LLM-written prose)
    # aren't glyphs every LaTeX font ships -- render each as an explicit
    # math-mode super-/subscript instead of hoping the font has them.
    superscripts = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻"
    superscript_targets = "0123456789+-"
    subscripts = "₀₁₂₃₄₅₆₇₈₉₊₋"
    subscript_targets = "0123456789+-"
    for ch, target in zip(superscripts, superscript_targets):
        text = text.replace(ch, f"$^{{{target}}}$")
    for ch, target in zip(subscripts, subscript_targets):
        text = text.replace(ch, f"$_{{{target}}}$")
    return text


def _inline_markdown(text: str) -> str:
    """Convert inline **bold** (and *italic*, applied after bold so the
    single-asterisk pass doesn't eat the double-asterisk markers) in
    already-escaped text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\\textit{\1}", text)
    return text


def markdown_to_latex(text: str) -> str:
    """Light, deliberately narrow markdown->LaTeX converter for the plain-
    prose (headers/bold/bullets, no tables/links/code) output this
    project's prompts ask the model to produce."""
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    in_itemize = False

    def close_list():
        nonlocal in_itemize
        if in_itemize:
            out.append(r"\end{itemize}")
            in_itemize = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        header_match = re.match(r"^(#{2,4})\s+(.*)$", stripped)
        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)

        if header_match:
            close_list()
            level = len(header_match.group(1))
            heading = _inline_markdown(_escape_latex(header_match.group(2)))
            cmd = {2: "subsection", 3: "subsubsection", 4: "paragraph"}.get(level, "subsubsection")
            out.append(f"\\{cmd}{{{heading}}}")
            continue

        if bullet_match:
            if not in_itemize:
                out.append(r"\begin{itemize}")
                in_itemize = True
            item = _inline_markdown(_escape_latex(bullet_match.group(1)))
            out.append(f"\\item {item}")
            continue

        close_list()
        if not stripped:
            out.append("")
        else:
            out.append(_inline_markdown(_escape_latex(stripped)))

    close_list()
    return "\n".join(out)


def references_to_latex(references_text: str, extra_citations: list[str] | None = None) -> str:
    """Render the Stage 6 citations block (plain numbered-list text, not
    BibTeX) plus any manually-verified extra citations as a simple LaTeX
    enumerate-style reference list."""
    items: list[str] = []
    for line in references_text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("(none"):
            continue
        line = re.sub(r"^\d+\.\s*", "", line)
        items.append(line)
    items.extend(extra_citations or [])

    if not items:
        return "No directly relevant prior publications were found for this specific dataset."

    body = "\n".join(f"\\item {_inline_markdown(_escape_latex(item))}" for item in items)
    return f"\\begin{{enumerate}}\n{body}\n\\end{{enumerate}}"


def build_aastex_document(
    *,
    title: str,
    abstract: str,
    introduction: str,
    methods: str,
    results: str,
    conclusions: str,
    references_text: str,
    figures: list[dict],
    author: str = "ALMA Thesis Planner (automated pipeline)",
    affiliation: str = "Automated analysis pipeline output -- not peer reviewed",
    email: str = "noreply@example.invalid",
    extra_citations: list[str] | None = None,
    software_note: str = "",
) -> str:
    """Build a complete AASTeX .tex document string. `figures` is a list of
    {"path": <fits-relative path to the PNG>, "caption": <str>, "label": <str>}."""
    figure_blocks = []
    for fig in figures:
        fname = Path(fig["path"]).name
        figure_blocks.append(
            "\\begin{figure}[htbp]\n"
            "\\centering\n"
            f"\\includegraphics[width=\\linewidth]{{{fname}}}\n"
            f"\\caption{{{_inline_markdown(_escape_latex(fig['caption']))}}}\n"
            f"\\label{{{fig['label']}}}\n"
            "\\end{figure}\n"
        )
    figures_tex = "\n".join(figure_blocks)

    references_tex = references_to_latex(references_text, extra_citations)

    return f"""\\documentclass[twocolumn]{{{AASTEX_CLASS}}}

\\usepackage{{graphicx}}

\\shorttitle{{{_escape_latex(title[:60])}}}
\\shortauthors{{{_escape_latex(author)}}}

\\begin{{document}}

\\title{{{_inline_markdown(_escape_latex(title))}}}

\\author{{{_escape_latex(author)}}}
\\affiliation{{{_escape_latex(affiliation)}}}
\\email{{{email}}}

\\begin{{abstract}}
{markdown_to_latex(abstract)}
\\end{{abstract}}

\\section{{Introduction}}
{markdown_to_latex(introduction)}

\\section{{Methods}}
{markdown_to_latex(methods)}

\\section{{Results}}
{markdown_to_latex(results)}

{figures_tex}

\\section{{Conclusions}}
{markdown_to_latex(conclusions)}

\\section{{Software and Data}}
{markdown_to_latex(software_note)}

\\section{{References}}
{references_tex}

\\end{{document}}
"""


def build_plain_document(
    title: str,
    body_markdown: str,
    *,
    author: str = "ALMA Thesis Planner (automated pipeline)",
) -> str:
    """Build a minimal, non-AASTeX LaTeX document (plain `article` class) for
    standalone deliverables that aren't full papers -- e.g. rendering idea.md
    or methods.md to their own PDF. Reuses the same markdown->LaTeX converter
    and Unicode-safe escaping as the AASTeX path above, compiled the same way
    via `compile_pdf` (xelatex)."""
    return f"""\\documentclass[11pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{parskip}}

\\title{{{_inline_markdown(_escape_latex(title))}}}
\\author{{{_escape_latex(author)}}}
\\date{{}}

\\begin{{document}}
\\maketitle

{markdown_to_latex(body_markdown)}

\\end{{document}}
"""


def compile_pdf(tex_content: str, out_dir: str | Path, basename: str = "paper", n_passes: int = 2) -> Path:
    """Write the .tex file and compile it with pdflatex. Runs pdflatex
    twice (cross-references/page numbers settle on the second pass) inside
    out_dir, non-interactively, and raises with the log tail on failure."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_path = out_dir / f"{basename}.tex"
    tex_path.write_text(tex_content, encoding="utf-8")

    # xelatex (not pdflatex) -- LLM-written prose routinely contains raw
    # Unicode (sigma, en/em dashes, primes, degree signs) that pdftex's
    # legacy 8-bit engine can't typeset without a large manual
    # character-substitution table; xelatex handles UTF-8 natively.
    xelatex = shutil.which("xelatex")
    if xelatex is None:
        # Freshly-installed MiKTeX may not yet be on PATH for a process
        # that started before the installer updated it -- fall back to the
        # well-known per-user install location before giving up.
        fallback = Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/xelatex.exe"
        if fallback.exists():
            xelatex = str(fallback)
        else:
            raise RuntimeError("xelatex not found on PATH -- is MiKTeX/TeX Live installed?")

    last_result = None
    for _ in range(n_passes):
        last_result = subprocess.run(
            [xelatex, "-interaction=nonstopmode", "-halt-on-error", f"{basename}.tex"],
            cwd=out_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )

    pdf_path = out_dir / f"{basename}.pdf"
    if not pdf_path.exists():
        log_tail = (last_result.stdout or "")[-4000:] if last_result else "(no output captured)"
        raise RuntimeError(f"xelatex did not produce a PDF. Log tail:\n{log_tail}")
    return pdf_path
