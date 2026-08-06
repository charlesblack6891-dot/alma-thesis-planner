"""GUI-independent orchestration for the prompt-to-paper wizard (gui_app.py).

Wires a user-chosen Claude model through every pipeline stage, resolves the
ALMA data source either from user-supplied fields ("manual" mode) or by
matching a free-text research topic against the already-vetted,
already-unpublished candidate pool built by topic_lookup.py ("search" mode),
then runs Stage 9's idea/methods pipeline and, optionally, Stage 13's
real-data full-paper pipeline -- rendering the results as one or more PDFs.

Kept separate from gui_app.py so it can be driven directly (no GUI, no
clicking) for testing/scripting, and so gui_app.py only has to handle
presentation and threading.

Two known, deliberate scope limits (both fail loudly rather than silently
producing wrong output):
- "search" mode matches against topic_lookup's local, pre-vetted candidate
  pool (currently ~14 already-unpublished datasets), not a live search of
  the full ALMA archive or the open web.
- "full_paper" scope reuses analysis.py's real-data engine, which is only
  physically valid for an HCN(1-0) line cube (its alpha_HCN dense-gas-mass
  conversion factor is specific to that transition) -- it refuses to run on
  a cube whose rest frequency doesn't match HCN(1-0).
"""
from __future__ import annotations

import hashlib
import re
import shutil
import time
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Callable

from astropy.io import fits

from alma_download import fetch_science_products
from analysis import run_analysis
from beginner_plan import generate_beginner_plan
from blocks import extract_block
from idea_loop import run_idea_loop, score_tractability
from latex_paper import build_aastex_document, build_plain_document, compile_pdf
from literature import check_published
from llm import ClaudeCLIError, call_chatgpt, call_claude
from methods import generate_methods
from paper import assemble_paper_with_results
from pipeline import run_pipeline
from state import (
    BEGINNER_PLAN_FILE,
    DESCRIPTION_FILE,
    IDEA_FILE,
    LITERATURE_FILE,
    METHODS_FILE,
    figures_dir,
    raw_data_dir,
    write_state_file,
)
from topic_lookup import (
    default_source_repo,
    filter_by_category_keyword,
    list_candidates,
    load_project_data,
    pick_project,
)
from writeup import assemble_writeup

# (model id passed to `claude --model`, display label, cost note)
MODELS: list[tuple[str, str, str]] = [
    ("claude-sonnet-5", "Sonnet 5", "Included with your Claude subscription (no extra cost)."),
    ("claude-opus-5", "Opus 5", "Included with your Claude subscription (no extra cost)."),
    ("claude-haiku-4-5-20251001", "Haiku 4.5", "Included with your Claude subscription (no extra cost)."),
    ("claude-fable-5", "Fable 5", "Pay-per-token -- uses API credits, NOT covered by a subscription."),
]

# (scope key, display label, description)
SCOPES: list[tuple[str, str, str]] = [
    ("quick_summary", "Quick Summary (fastest)",
     "A single idea pass and a single methods pass -- no maker/critic refinement loop, no "
     "tractability re-check. One combined summary PDF. By far the fastest option, but also the "
     "least vetted -- treat it as a rough starting point, not a settled plan."),
    ("idea_methods", "Idea + Methods only",
     "Literature check, idea loop, and methods plan. Fast, no data download."),
    ("full_paper", "Full paper",
     "All of the above, plus a real ALMA data download, real analysis, and a compiled paper PDF. "
     "Slower; only works for HCN(1-0) line-cube datasets."),
]

# (publication filter key, display label, description) -- search mode only.
PUBLICATION_FILTERS: list[tuple[str, str, str]] = [
    ("unpublished", "Unpublished only (recommended)",
     "Matches only against candidates already checked and found NOT YET published -- the safest "
     "choice for a genuinely new thesis project."),
    ("published", "Published only",
     "Matches only against candidates already checked and found published (or partially "
     "published). The live publication check at generation time will normally confirm this and "
     "stop before producing any PDFs -- useful for browsing already-published topics, not for "
     "producing a new paper."),
    ("both", "Both",
     "Matches against the full local pool regardless of publication status."),
]

# (provider key, display label, description)
PROVIDERS: list[tuple[str, str, str]] = [
    ("claude", "Claude", "Uses your Claude subscription via the `claude` CLI."),
    ("chatgpt", "ChatGPT (fallback, free tier)",
     "Use this if your Claude usage/tokens are exhausted. The free version of ChatGPT is less "
     "capable and less consistent at following this pipeline's prompts than Claude, so treat "
     "anything it produces as a rougher, less reliable draft. Only supports the 'Quick Summary' "
     "and 'Idea + Methods' scopes -- 'Full paper' always requires Claude. Not implemented yet: "
     "selecting this currently raises an error instead of making a real call."),
]

HCN10_REST_FREQ_HZ = 88.631601e9
_REST_FREQ_TOLERANCE_HZ = 0.5e9

# analysis.py's dense-gas-mass conversion (luminosity distance -> L'_HCN via
# Solomon & Vanden Bout, then alpha_HCN from Gao & Solomon 2004) is built for
# nearby-galaxy science; below this, a target is Galactic (e.g. a Milky Way
# star-forming region/protostellar outflow), where "distance" and "systemic
# velocity" mean something entirely different and the conversion is physically
# meaningless. 0.03 Mpc = 30 kpc comfortably exceeds the Milky Way's ~15 kpc
# radius while sitting safely below even the closest true satellite galaxies
# (LMC ~0.05 Mpc, SMC ~0.06 Mpc) -- confirmed necessary live: an LLM distance
# lookup for a Galactic SMORES target (BHR 71 et al.) returned 0.0002 Mpc
# (~200 pc, a real Galactic distance) with nothing catching that it was being
# fed into an extragalactic-only formula.
MIN_EXTRAGALACTIC_DISTANCE_MPC = 0.03

# llm.py's call_claude defaults to a 120s timeout, tuned for short,
# single-shot calls -- too tight for this wizard, where a run makes up to
# ~15-20 chained calls (idea loop, methods, paper sections) and killing one
# on a slow response discards everything already spent on it. This is a
# background, non-interactive tool, so waiting longer costs only wall-clock
# time, not correctness -- generous is the safe direction here.
#
# Live-verified (2026-08-01, GS1354-645 / 2013.1.00222.T, Sonnet 5): 6
# consecutive real calls all completed in 18-71s. A 7th then hung for over
# 1400s before dying -- well beyond normal model latency, looking like a
# genuine stall rather than "just needed more time." A single retry on
# timeout (fresh subprocess, same prompt) is cheap insurance against that
# class of failure without waiting arbitrarily long on a truly stuck call.
CLAUDE_CALL_TIMEOUT_S = 300.0
CLAUDE_CALL_MAX_ATTEMPTS = 2


def _make_call_claude(model: str | None, progress: Callable[[str], None]) -> Callable[[str], str]:
    """Wrap call_claude with the model pinned, a longer timeout, a retry on
    any CLI failure, and per-call progress logging (call number, prompt size,
    elapsed time, attempt number) -- so if a call ever fails, the progress
    log shows exactly which one, rather than the whole literature+idea+
    methods block failing as one opaque unit with no indication of how far
    it got.

    Retries on ANY ClaudeCLIError, not just a timeout -- confirmed live
    (2026-08-02) that a late-chain call can fail fast (~8s) with a bare
    non-zero exit code and empty stderr, looking exactly like a transient
    CLI hiccup rather than a deterministic, content-driven rejection. That
    class of failure previously wasn't retried at all and discarded 11
    already-paid-for prior calls in the same run (see pipeline.py's
    on_stage_complete, added the same day, for the other half of the fix --
    checkpointing so a retry exhausting itself doesn't lose that work either)."""
    call_count = 0

    def _cc(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        n = call_count
        for attempt in range(1, CLAUDE_CALL_MAX_ATTEMPTS + 1):
            suffix = f", attempt {attempt}/{CLAUDE_CALL_MAX_ATTEMPTS}" if attempt > 1 else ""
            progress(f"  [claude call {n}] sending ({len(prompt)} chars, model={model or 'default'}{suffix})...")
            start = time.monotonic()
            try:
                result = call_claude(prompt, model=model, timeout=CLAUDE_CALL_TIMEOUT_S)
            except ClaudeCLIError as exc:
                elapsed = time.monotonic() - start
                if attempt < CLAUDE_CALL_MAX_ATTEMPTS:
                    progress(f"  [claude call {n}] failed after {elapsed:.0f}s ({exc}) -- retrying")
                    continue
                progress(f"  [claude call {n}] FAILED after {elapsed:.0f}s")
                raise
            progress(f"  [claude call {n}] done in {time.monotonic() - start:.0f}s")
            return result
        raise AssertionError("unreachable")  # loop always returns or raises

    return _cc


def _make_call_chatgpt(progress: Callable[[str], None]) -> Callable[[str], str]:
    """Same per-call progress logging as _make_call_claude, above, wrapping
    llm.call_chatgpt instead. That function isn't implemented yet (see its own
    docstring), so every call made through this wrapper raises -- this exists so the
    provider selection has a real seam to plumb through the rest of the wizard now,
    ready for a real ChatGPT integration to drop in later without touching callers."""
    call_count = 0

    def _cc(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        progress(f"  [chatgpt call {call_count}] sending ({len(prompt)} chars)...")
        return call_chatgpt(prompt)

    return _cc


def _make_call_llm(provider: str, model: str | None, progress: Callable[[str], None]) -> Callable[[str], str]:
    """Pick the right per-call wrapper for cfg.provider ("claude" or "chatgpt")."""
    if provider == "chatgpt":
        return _make_call_chatgpt(progress)
    return _make_call_claude(model, progress)


def slugify(text: str, max_len: int = 24) -> str:
    """Turn arbitrary source text (an ALMA project code, or a target name --
    which can be a long comma-joined list of every pointing in a multi-target
    proposal, confirmed live to run past 60 characters on its own) into a
    short, bounded directory-name fragment. Capped regardless of input
    length: an uncapped slug here produced a 106-character project directory
    name that, combined with the repo path and a typical ~90-character
    ALMA-archive FITS filename inside it, exceeded Windows' path-length
    limit (WinError 206, 'The filename or extension is too long')."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip()).strip("_").lower()
    slug = slug[:max_len].rstrip("_")
    return slug or "project"


def _short_hash(*parts: str, length: int = 6) -> str:
    """A short, deterministic disambiguator derived from the *full,
    untruncated* source strings -- not the truncated slugs -- so two
    different (project_code, target) pairs that happen to share the same
    first `max_len` characters (e.g. two multi-target proposals whose
    target lists start the same way) still get different directory names.
    Deterministic (not random/time-based) so re-running the same project
    lands on the same directory each time, matching download()'s existing
    skip-if-already-downloaded behavior."""
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:length]


# --- Data-source resolution ------------------------------------------------

@dataclass
class ResolvedSource:
    project_code: str
    pi: str
    target: str
    data_description: str
    source_note: str  # how this was found -- shown to the user before anything is spent on it


def resolve_source_manual(project_code: str, pi: str, target: str, data_description: str) -> ResolvedSource:
    for name, value in [
        ("ALMA project code", project_code),
        ("PI name", pi),
        ("target name", target),
        ("data description", data_description),
    ]:
        if not value or not value.strip():
            raise ValueError(f"Manual mode requires a {name}.")
    return ResolvedSource(
        project_code=project_code.strip(),
        pi=pi.strip(),
        target=target.strip(),
        data_description=data_description.strip(),
        source_note="Entered manually.",
    )


# Human-readable description of the candidate pool for each publication_filter
# choice, used in resolve_source_search's user-facing messages below.
_POOL_LABELS: dict[str, str] = {
    "unpublished": "already-vetted, already-unpublished",
    "published": "already-vetted, already-published (or partially published)",
    "both": "already-vetted (published and unpublished)",
}


def resolve_source_search(
    topic: str,
    *,
    category: str = "",
    keyword: str = "",
    publication_filter: str = "unpublished",
    call_claude_fn: Callable[[str], str] = call_claude,
    source_repo: Path | None = None,
) -> ResolvedSource:
    """Resolve a search-mode data source, optionally focused by a scientific
    category + science keyword pair (both required together, from the local
    pool's own vocabulary -- see topic_lookup.available_categories_and_keywords).
    `topic` alone (category/keyword blank) still works, unchanged, for
    existing callers like run_auto.py's plain topic-sentence flow.

    `publication_filter` ("unpublished" (default), "published", or "both")
    selects which slice of the local candidate pool to match against -- see
    topic_lookup.list_candidates. Note that picking "published" here doesn't
    skip the live publication check `generate()` runs at generation time; it
    will normally still find the dataset published and stop there with no
    PDFs, so it's meant for browsing already-published topics, not producing
    a new paper."""
    if bool(category) != bool(keyword):
        raise ValueError("Give both a scientific category and a science keyword, or neither.")
    if not topic.strip() and not (category and keyword):
        raise ValueError(
            "Search mode requires a research-interest prompt, or a scientific category + science "
            "keyword pair."
        )

    pool_label = _POOL_LABELS.get(publication_filter, publication_filter)
    repo = source_repo or default_source_repo()
    candidates = list_candidates(repo, publication_filter)
    if not candidates:
        raise ValueError(
            f"No {pool_label} candidates found in {repo}. Search mode matches against this "
            "pre-vetted local pool, not a live archive/web search -- try a different publication-"
            "status filter, or use manual mode instead."
        )

    pool = candidates
    focus_note = ""
    if category and keyword:
        pool = filter_by_category_keyword(candidates, category, keyword)
        if not pool:
            raise ValueError(
                f"No {pool_label} candidate has both scientific category {category!r} and science "
                f"keyword {keyword!r} -- pick a different combination."
            )
        focus_note = f"Focused on scientific category \"{category}\" + science keyword \"{keyword}\". "

    if category and keyword and len(pool) == 1:
        # An exact, deterministic match on category+keyword alone -- no LLM
        # call needed, and no risk of a model second-guessing a match this
        # precise (the free-text prompt, if any, becomes moot with one
        # candidate left).
        picked = pool[0]
        data = load_project_data(repo, picked.project_code)
        return ResolvedSource(
            project_code=data["project_code"], pi=data["pi"], target=data["target"],
            data_description=data["data_description"],
            source_note=(
                f"{focus_note}The only {pool_label} candidate with both "
                f"(title: \"{data['title']}\"). Not a live archive/web search."
            ),
        )

    pick = pick_project(topic, pool, call_claude_fn=call_claude_fn)
    data = load_project_data(repo, pick.candidate.project_code)
    quality_flag = "" if pick.match_quality == "GOOD" else " -- WEAK MATCH, read the reason below carefully"
    return ResolvedSource(
        project_code=data["project_code"],
        pi=data["pi"],
        target=data["target"],
        data_description=data["data_description"],
        source_note=(
            f"{focus_note}Matched out of {len(pool)} {pool_label} ALMA "
            f"candidate(s) (title: \"{data['title']}\"){quality_flag}. Why this was picked: {pick.reason} "
            "Not a live archive/web search -- double-check this is really what you wanted before "
            "spending tokens on it."
        ),
    )


# --- Distance / systemic-velocity lookup (full-paper scope only) ----------

def _distance_velocity_prompt(target: str, data_description: str) -> str:
    return f"""You are looking up two specific astrophysical facts about the ALMA target "{target}" needed for a flux-to-luminosity conversion: its distance in megaparsecs, and its systemic (heliocentric or similar standard) velocity in km/s. Use the data description below plus your own knowledge/research; if the data description already states a distance or velocity, prefer that value over your own recollection.

Data description:
{data_description}

Respond in the following format:

\\begin{{DISTVEL}}
DISTANCE_MPC: <number only>
SYSTEMIC_VEL_KMS: <number only>
SOURCE: <one or two sentences citing where each number came from>
\\end{{DISTVEL}}

If you cannot find a confident value for one of the two, still give your best estimate but say so plainly in SOURCE."""


@dataclass
class DistanceVelocity:
    distance_mpc: float
    systemic_velocity_kms: float
    source_note: str


def lookup_distance_velocity(
    target: str,
    data_description: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> DistanceVelocity:
    raw = call_claude_fn(_distance_velocity_prompt(target, data_description))
    block = extract_block(raw, "DISTVEL", repair_fn=call_claude_fn)

    distance_mpc = None
    systemic_velocity_kms = None
    source_parts: list[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("DISTANCE_MPC:"):
            nums = re.findall(r"[-+]?\d*\.?\d+", stripped.split(":", 1)[1])
            if nums:
                distance_mpc = float(nums[0])
        elif upper.startswith("SYSTEMIC_VEL_KMS:"):
            nums = re.findall(r"[-+]?\d*\.?\d+", stripped.split(":", 1)[1])
            if nums:
                systemic_velocity_kms = float(nums[0])
        elif upper.startswith("SOURCE:"):
            source_parts.append(stripped.split(":", 1)[1].strip())

    if distance_mpc is None or systemic_velocity_kms is None:
        raise ValueError(f"Could not parse a distance/velocity pair from the model's response:\n{block}")
    return DistanceVelocity(distance_mpc, systemic_velocity_kms, " ".join(source_parts) or "(no source given)")


def _ensure_output_paths_writable(paths: list[Path]) -> None:
    """Fail fast, before any Claude calls are made, rather than after several
    minutes and several dollars of them. Opens each expected output PDF path
    in append mode -- this creates the file if it doesn't exist yet but,
    unlike 'wb', does not truncate/destroy it if it does -- purely to detect
    whether the path is unwritable (e.g. the PDF from a previous run is
    currently open in a viewer, which holds an exclusive lock on Windows) up
    front. The real write later in `generate()` still goes through
    `Path.write_bytes`/`compile_pdf` as before; this is a writability probe,
    not the actual output step."""
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "ab"):
                pass
        except OSError as exc:
            raise RuntimeError(
                f"Can't write to {path} -- if it's open in another program (e.g. a PDF viewer), "
                f"close it and try again. ({exc})"
            ) from exc


def _cube_rest_freq_hz(cube_fits: Path) -> float:
    header = fits.getheader(cube_fits)
    for key in ("RESTFRQ", "RESTFREQ"):
        if key in header:
            return float(header[key])
    raise KeyError("no RESTFRQ/RESTFREQ keyword in the downloaded cube's header")


# --- Wizard config / result -------------------------------------------------

@dataclass
class WizardConfig:
    mode: str  # "manual" or "search"
    scope: str  # "quick_summary", "idea_methods", or "full_paper"
    model: str  # one of MODELS[i][0], or "" for the claude CLI's own default
    provider: str = "claude"  # one of PROVIDERS[i][0]
    prompt_text: str = ""  # search-mode topic; optional if category+keyword are given; kept for the record in manual mode too
    category: str = ""  # search-mode scientific category (required together with keyword)
    keyword: str = ""  # search-mode science keyword (required together with category)
    publication_filter: str = "unpublished"  # search-mode: one of PUBLICATION_FILTERS[i][0]
    project_code: str = ""
    pi: str = ""
    target: str = ""
    data_description: str = ""
    distance_mpc: float | None = None
    systemic_velocity_kms: float | None = None
    project_dir: str = ""
    n_iterations: int = 4
    beginner_plan: bool = False  # also generate a plain-language plan for beginner readers, alongside whatever scope was picked


@dataclass
class WizardResult:
    status: str  # "short_circuited" or "done"
    project_dir: str
    resolved: ResolvedSource
    literature_verdict: str
    pdfs: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def resolve(cfg: WizardConfig, *, call_claude_fn: Callable[[str], str]) -> ResolvedSource:
    """Cheap, no-download step: figure out which ALMA project/PI/target to
    use. Callers should show this to the user for confirmation before
    calling `generate`, which is where real time/tokens/downloads start."""
    if cfg.mode == "search":
        return resolve_source_search(
            cfg.prompt_text, category=cfg.category, keyword=cfg.keyword,
            publication_filter=cfg.publication_filter, call_claude_fn=call_claude_fn,
        )
    return resolve_source_manual(cfg.project_code, cfg.pi, cfg.target, cfg.data_description)


_STAGE_FILES = {"literature": LITERATURE_FILE, "idea": IDEA_FILE, "methods": METHODS_FILE}


def _checkpoint_stage(project_dir: str, stage: str, content: str, progress: Callable[[str], None]) -> None:
    """run_pipeline's on_stage_complete callback: persist a stage's output to
    disk the moment it's available, not only after the whole pipeline
    (including the writeup call) finishes. Confirmed live (2026-08-02) that
    without this, a late-stage Claude CLI failure discarded 11
    already-paid-for calls' worth of idea/methods work with nothing written
    to disk at all -- see run_pipeline's own docstring for the fuller story."""
    write_state_file(project_dir, _STAGE_FILES[stage], content + "\n")
    progress(f"  (checkpointed {_STAGE_FILES[stage]})")


def generate(
    cfg: WizardConfig,
    resolved: ResolvedSource,
    *,
    progress: Callable[[str], None] = print,
) -> WizardResult:
    """The expensive step: literature check, idea/methods loop, PDF
    rendering, and (for full_paper scope) real ALMA download + analysis +
    compiled paper PDF."""
    if cfg.provider == "chatgpt" and cfg.scope == "full_paper":
        raise ValueError(
            "The ChatGPT provider only supports the 'Quick Summary' and 'Idea + Methods' scopes -- "
            "'Full paper' needs Claude for the real-data analysis writeup. Switch the provider back "
            "to Claude, or pick a different scope."
        )
    cc = _make_call_llm(cfg.provider, cfg.model or None, progress)

    project_dir = cfg.project_dir.strip() or (
        f"project_{slugify(resolved.project_code)}_{slugify(resolved.target)}"
        f"_{_short_hash(resolved.project_code, resolved.target)}"
    )
    Path(project_dir).mkdir(parents=True, exist_ok=True)

    # Determine the final output filenames now and confirm they're writable
    # before spending a single Claude call on this run -- see
    # _ensure_output_paths_writable's docstring for why this matters.
    if cfg.scope == "quick_summary":
        output_paths = [Path(project_dir) / "summary.pdf"]
    else:
        output_paths = [Path(project_dir) / "idea.pdf", Path(project_dir) / "methods.pdf"]
        if cfg.scope == "full_paper":
            output_paths.append(Path(project_dir) / "paper.pdf")
    _ensure_output_paths_writable(output_paths)

    write_state_file(project_dir, DESCRIPTION_FILE, resolved.data_description + "\n")

    progress(f"Project directory: {project_dir}")
    progress(f"Data source: {resolved.project_code} / PI {resolved.pi} / target {resolved.target}")
    progress(resolved.source_note)

    # quick_summary trades thoroughness for speed: one maker/critic pass instead of
    # cfg.n_iterations (the default 4 means 8 idea-loop calls alone), and the
    # tractability score is skipped outright -- nothing downstream in this function
    # ever reads it (not even the other two scopes), so for the fastest path it's
    # a call worth cutting rather than just retrying/checkpointing around.
    if cfg.scope == "quick_summary":
        n_iterations = 1
        score_tractability_fn = lambda *a, **k: ""
        progress("Checking publication status, then running a single-pass idea + methods summary...")
    else:
        n_iterations = cfg.n_iterations
        score_tractability_fn = partial(score_tractability, call_claude_fn=cc)
        progress("Checking publication status, then running the idea + methods loop (this makes several Claude calls)...")

    result = run_pipeline(
        resolved.project_code, resolved.pi, resolved.target, resolved.data_description,
        n_iterations=n_iterations,
        check_published_fn=partial(check_published, call_claude_fn=cc),
        run_idea_loop_fn=partial(run_idea_loop, call_claude_fn=cc),
        score_tractability_fn=score_tractability_fn,
        generate_methods_fn=partial(generate_methods, call_claude_fn=cc),
        assemble_writeup_fn=partial(assemble_writeup, call_claude_fn=cc),
        # Neither idea_methods nor full_paper scope ever reads result.writeup
        # below -- only .idea/.methods -- so the writeup call (the single
        # largest prompt in the chain, folding idea+methods+literature
        # together) is pure wasted cost/risk here. Skipped entirely rather
        # than just retried/checkpointed around.
        include_writeup=False,
        on_stage_complete=lambda stage, content: _checkpoint_stage(project_dir, stage, content, progress),
    )
    progress(f"Publication verdict: {result.literature.verdict}")

    if result.short_circuited:
        progress(
            "This dataset is already published (or its status is unclear) -- stopping here, no "
            "idea/methods/paper PDFs were generated. See literature.md in the project folder."
        )
        return WizardResult(
            status="short_circuited",
            project_dir=project_dir,
            resolved=resolved,
            literature_verdict=result.literature.verdict,
            notes=[result.literature.raw],
        )

    write_state_file(project_dir, IDEA_FILE, result.idea + "\n")
    write_state_file(project_dir, METHODS_FILE, result.methods + "\n")
    progress("Idea and methods settled. Rendering PDFs...")

    pdf_build_dir = Path(project_dir) / "pdf_build"
    pdfs: list[str] = []

    if cfg.beginner_plan:
        # Runs regardless of scope -- the idea/methods text above is settled
        # by this point for quick_summary, idea_methods, and full_paper
        # alike, and this companion document just re-explains the same
        # project in plain language rather than depending on anything
        # scope-specific (e.g. full_paper's real-data results).
        progress("Writing a beginner-friendly plan (goal, skills needed, first week walkthrough)...")
        beginner_text = generate_beginner_plan(
            resolved.data_description, result.idea, result.methods, resolved.target, call_claude_fn=cc,
        )
        write_state_file(project_dir, BEGINNER_PLAN_FILE, beginner_text + "\n")
        beginner_tex = build_plain_document(f"Beginner's Guide: {resolved.target}", beginner_text)
        beginner_pdf = compile_pdf(beginner_tex, pdf_build_dir, basename="beginner_plan")
        beginner_out = Path(project_dir) / "beginner_plan.pdf"
        beginner_out.write_bytes(beginner_pdf.read_bytes())
        pdfs.append(str(beginner_out))
        progress(f"Wrote {beginner_out}")

    if cfg.scope == "quick_summary":
        summary_body = f"## Idea\n\n{result.idea}\n\n## Methods\n\n{result.methods}\n"
        summary_tex = build_plain_document(f"Summary Plan: {resolved.target}", summary_body)
        summary_pdf = compile_pdf(summary_tex, pdf_build_dir, basename="summary")
        summary_out = Path(project_dir) / "summary.pdf"
        summary_out.write_bytes(summary_pdf.read_bytes())
        pdfs.append(str(summary_out))
        progress(f"Wrote {summary_out}")
        return WizardResult(
            status="done", project_dir=project_dir, resolved=resolved,
            literature_verdict=result.literature.verdict, pdfs=pdfs,
        )

    idea_tex = build_plain_document(f"Research Idea: {resolved.target}", result.idea)
    idea_pdf = compile_pdf(idea_tex, pdf_build_dir, basename="idea")
    idea_out = Path(project_dir) / "idea.pdf"
    idea_out.write_bytes(idea_pdf.read_bytes())
    pdfs.append(str(idea_out))

    methods_tex = build_plain_document(f"Methods: {resolved.target}", result.methods)
    methods_pdf = compile_pdf(methods_tex, pdf_build_dir, basename="methods")
    methods_out = Path(project_dir) / "methods.pdf"
    methods_out.write_bytes(methods_pdf.read_bytes())
    pdfs.append(str(methods_out))
    progress(f"Wrote {idea_out} and {methods_out}")

    if cfg.scope == "idea_methods":
        return WizardResult(
            status="done", project_dir=project_dir, resolved=resolved,
            literature_verdict=result.literature.verdict, pdfs=pdfs,
        )

    # --- scope == "full_paper" ---------------------------------------
    distance_mpc = cfg.distance_mpc
    systemic_velocity_kms = cfg.systemic_velocity_kms
    distance_source_note = "User-provided value."
    if distance_mpc is None or systemic_velocity_kms is None:
        progress("Looking up this target's distance and systemic velocity...")
        dv = lookup_distance_velocity(resolved.target, resolved.data_description, call_claude_fn=cc)
        distance_mpc, systemic_velocity_kms = dv.distance_mpc, dv.systemic_velocity_kms
        distance_source_note = dv.source_note
        progress(f"Adopted distance={distance_mpc} Mpc, systemic velocity={systemic_velocity_kms} km/s ({distance_source_note})")

    if distance_mpc < MIN_EXTRAGALACTIC_DISTANCE_MPC:
        raise RuntimeError(
            f"Adopted distance ({distance_mpc} Mpc = {distance_mpc * 1000:.1f} kpc) is Galactic-scale, "
            f"not extragalactic -- below {MIN_EXTRAGALACTIC_DISTANCE_MPC} Mpc, comfortably inside even "
            "the Milky Way's disk. 'Full paper' mode's analysis (HCN(1-0) dense-gas mass via a "
            "luminosity-distance formula, alpha_HCN calibrated by Gao & Solomon 2004) is built for "
            "nearby-galaxy science and is physically meaningless applied to a Galactic target (e.g. a "
            "protostellar outflow or star-forming region) -- the mass/luminosity numbers would be "
            "nonsense even if the download succeeded. Try 'Idea + Methods only' instead, which doesn't "
            "depend on this distance conversion."
        )

    # resolved.target may be a comma-joined list of every pointing in a
    # multi-target proposal (topic_lookup.py's convention, used for display
    # and in the data description) -- the archive query needs one exact
    # target_name, so use the first entry, which is a real archive value
    # (topic_lookup.load_project_data derives it from the project's own
    # mous_records, not invented). Confirmed live: passing the full joined
    # string here always fails with "No public member OUS found".
    download_target = resolved.target.split(",")[0].strip()
    if download_target != resolved.target:
        progress(
            f"Target is a multi-pointing list ('{resolved.target}') -- downloading the first pointing "
            f"('{download_target}') only. Use manual mode with a specific target for a different one."
        )

    progress(f"Downloading real ALMA science products for {resolved.project_code} / {download_target}...")
    fetched = fetch_science_products(resolved.project_code, download_target, raw_data_dir(project_dir))
    if not fetched.continuum_fits or not fetched.cube_fits:
        raise RuntimeError(
            "This dataset's public products don't include both a continuum image and a spectral-line "
            "cube -- the real-data analysis (moment maps + aperture photometry) needs both, so "
            "'Full paper' can't continue for this dataset. Try 'Idea + Methods only' instead."
        )
    progress(f"Downloaded: {fetched.continuum_fits.name}, {fetched.cube_fits.name}")

    try:
        rest_freq_hz = _cube_rest_freq_hz(fetched.cube_fits)
    except KeyError as exc:
        raise RuntimeError(
            f"Could not determine the downloaded cube's spectral line ({exc}). 'Full paper' mode's "
            "analysis is only validated for HCN(1-0) data, so it refuses to guess. Try 'Idea + Methods "
            "only' instead."
        ) from exc
    if abs(rest_freq_hz - HCN10_REST_FREQ_HZ) > _REST_FREQ_TOLERANCE_HZ:
        raise RuntimeError(
            f"The downloaded line cube's rest frequency ({rest_freq_hz / 1e9:.4f} GHz) does not match "
            f"HCN(1-0) ({HCN10_REST_FREQ_HZ / 1e9:.4f} GHz). This pipeline's real-data analysis (moment "
            "maps, aperture photometry, and the alpha_HCN dense-gas-mass conversion) is only physically "
            "valid for HCN(1-0) and can't be safely applied to a different tracer. Try 'Idea + Methods "
            "only' instead, or pick a project whose delivered line cube is HCN(1-0)."
        )

    with fits.open(fetched.continuum_fits) as hdul:
        header = hdul[0].header
        ra_deg, dec_deg = header["CRVAL1"], header["CRVAL2"]

    progress("Running real analysis (moment maps, aperture photometry, luminosity/mass conversion)...")
    results = run_analysis(
        # download_target, not resolved.target -- the FITS data downloaded and
        # analyzed below covers only that one pointing, so the paper must be
        # described (and its Results/Introduction grounded) as being about that
        # specific target, not the full multi-pointing proposal it came from.
        project_dir, fetched.continuum_fits, fetched.cube_fits, ra_deg, dec_deg, download_target,
        distance_mpc=distance_mpc, systemic_velocity_kms=systemic_velocity_kms,
    )
    progress(f"Continuum RMS: {results['continuum']['rms_mjy_beam']:.4f} mJy/beam")
    progress(f"HCN central-depression interpretation: {results['hcn']['central_depression_interpretation']}")

    progress("Writing real-results paper sections (several more Claude calls)...")
    sections = assemble_paper_with_results(result.idea, result.methods, result.literature.raw, results, call_claude_fn=cc)

    progress("Assembling AASTeX document and compiling the paper PDF...")
    figs_dir = figures_dir(project_dir)
    figures = [
        {"path": str(figs_dir / "continuum.png"), "label": "fig:continuum",
         "caption": "ALMA continuum image with the beam-scaled photometry apertures overlaid."},
        {"path": str(figs_dir / "hcn_moments.png"), "label": "fig:moments",
         "caption": "HCN(1-0) moment 0 (integrated intensity), moment 1 (velocity), and moment 2 "
                    "(velocity dispersion) maps."},
        {"path": str(figs_dir / "hcn_pv_diagram.png"), "label": "fig:pv",
         "caption": "Position-velocity cut through the nucleus."},
    ]
    tex = build_aastex_document(
        title=sections["title"],
        abstract=sections["abstract"],
        introduction=sections["introduction"],
        methods=sections["methods"],
        results=sections["results"],
        conclusions=sections["conclusions"],
        references_text=sections["references"],
        figures=figures,
        extra_citations=[
            "Gao, Y. & Solomon, P. M. 2004, ApJS, 152, 63 (dense-gas mass conversion factor, alpha_HCN)",
            f"Adopted distance ({distance_mpc} Mpc) and systemic velocity ({systemic_velocity_kms} km/s): "
            f"{distance_source_note}",
        ],
        software_note=(
            "This paper's Abstract, Introduction, Methods, Results, and Conclusions text was drafted by "
            "an LLM-based automated pipeline, conditioned strictly on real measurements from the "
            "analysis code described in Methods -- no simulated or placeholder numbers appear in the "
            "Results section. This is a pilot/demonstration output and has not been independently peer "
            "reviewed; a domain expert should verify every quantitative claim before any further use."
        ),
    )
    pdf_build_dir.mkdir(parents=True, exist_ok=True)
    for fig in figures:
        shutil.copy(fig["path"], pdf_build_dir / Path(fig["path"]).name)
    pdf_path = compile_pdf(tex, pdf_build_dir, basename="paper")
    final_pdf = Path(project_dir) / "paper.pdf"
    shutil.copy(pdf_path, final_pdf)
    pdfs.append(str(final_pdf))
    progress(f"Wrote {final_pdf}")

    return WizardResult(
        status="done", project_dir=project_dir, resolved=resolved,
        literature_verdict=result.literature.verdict, pdfs=pdfs,
    )
