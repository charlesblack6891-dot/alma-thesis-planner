"""Full-paper draft assembly (Stage 11).

Ports the paper-writing prompts from the original Denario's LangGraph paper
agent (denario/paper_agents/prompts.py: abstract_prompt, introduction_prompt,
methods_prompt, conclusions_prompt), reframed from LaTeX + per-node JSON
output into this repo's plain-markdown \\begin{TAG}...\\end{TAG}
extract_block convention (Stage 3), with each section independently
call_claude_fn-injectable per Stage 5/7/8's pattern.

One deliberate divergence from the original, and it's the whole point of
this module's design: Denario's results_node/plots_node write the Results
section by reading real figures produced by an earlier `denario.get_results()`
run that actually executed analysis code against real data. Nothing in this
repo ever does that -- every project_*/ directory here stops at a thesis
*plan* -- no CASA reduction, no real ALMA analysis, no plots exist anywhere
in this repo. Asking an LLM to invent a Results section anyway would fabricate
findings, so `results_placeholder()` below is a fixed, clearly-labeled
placeholder with zero LLM involvement, not a generated section. Abstract,
Introduction, Methods, and Conclusions are all written *prospectively*
("registered report" style: what the study aims to determine and how success
will be judged) rather than asserting outcomes that don't exist. Denario's
citations_node (Perplexity-based citation injection) and keywords_node
(AAS-keyword-list selection) are not ported here -- out of scope for this
stage; literature.md's existing citation list (from Stage 6) is reused
verbatim as the References section instead.
"""
from __future__ import annotations

from typing import Callable

from blocks import extract_block
from llm import call_claude

DRAFT_BANNER = (
    "> **Draft status: pre-analysis.** This paper was assembled by the automated "
    "planning pipeline before any data analysis was carried out. The Abstract, "
    "Introduction, Methods, and Conclusions below are written prospectively -- "
    "describing what this study aims to determine and how -- and the Results "
    "section is an explicit placeholder. Every section must be revised once the "
    "student has actually executed the methods below against real ALMA data.\n"
)


def title_abstract_prompt(idea: str, methods: str) -> str:
    return f"""You are an astrophysicist drafting the title and abstract for a paper describing a planned study, before the analysis has been carried out. Given the idea and methods below, write a title and an abstract.

Follow these guidelines:
- Briefly describe the scientific problem and why it matters.
- Briefly describe the approach used to address it (the dataset and methods).
- Describe prospectively what the study is designed to determine -- do NOT invent specific numerical results, measurements, or findings, since no analysis has been performed yet.
- Write the abstract in plain markdown prose (no LaTeX, no citations).
- The abstract should be a single paragraph, no sections or line breaks.
- Make sure it reads smoothly and is well-motivated.

Idea:
{idea}

Methods:
{methods}

Respond in the following format:

\\begin{{TITLE}}
<TITLE>
\\end{{TITLE}}

\\begin{{ABSTRACT}}
<ABSTRACT>
\\end{{ABSTRACT}}

In <TITLE> put the paper's title. In <ABSTRACT> put the single-paragraph abstract."""


def generate_title_and_abstract(
    idea: str,
    methods: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> tuple[str, str]:
    raw = call_claude_fn(title_abstract_prompt(idea, methods))
    title = extract_block(raw, "TITLE", repair_fn=call_claude_fn)
    abstract = extract_block(raw, "ABSTRACT", repair_fn=call_claude_fn)
    return title, abstract


def introduction_prompt(title: str, abstract: str, idea: str, methods: str) -> str:
    return f"""Given the title, abstract, idea, and methods below, write an introduction for a scientific paper describing a planned (not yet executed) study.

Paper title:
{title}

Paper abstract:
{abstract}

Paper idea:
{idea}

Paper methods:
{methods}

Respond in the following format:

\\begin{{INTRODUCTION}}
<INTRODUCTION>
\\end{{INTRODUCTION}}

In <INTRODUCTION> place the introduction. Follow these guidelines:
- Write in plain markdown prose, no LaTeX commands.
- Expand on the key points in the abstract, providing background and context.
- Describe what the problem is and why it is difficult.
- Describe how this study attempts to address it.
- Describe how the study will verify whether it has succeeded, without asserting a specific outcome.
- Do not create subsections.
- Do not add citations.
- Do not claim specific results -- none exist yet."""


def generate_introduction(
    title: str,
    abstract: str,
    idea: str,
    methods: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    raw = call_claude_fn(introduction_prompt(title, abstract, idea, methods))
    return extract_block(raw, "INTRODUCTION", repair_fn=call_claude_fn)


def paper_methods_prompt(title: str, abstract: str, introduction: str, methods: str) -> str:
    return f"""Given the paper title, abstract, and introduction below, expand the short methods description into the full Methods section of a scientific paper. Describe in detail the dataset and each analysis step.

Paper title:
{title}

Paper abstract:
{abstract}

Paper introduction:
{introduction}

Short description of methods:
{methods}

Respond in the following format:

\\begin{{PAPER_METHODS}}
<PAPER_METHODS>
\\end{{PAPER_METHODS}}

In <PAPER_METHODS> put the Methods section. Follow these guidelines:
- Write in plain markdown prose, using subheadings (###) where useful, no LaTeX commands.
- Describe in detail the dataset, the analysis steps, and the tools used, preserving every concrete step and number in the short description above -- do not invent new steps or drop existing ones.
- Do not write citations.
- Connect the text with the introduction above.
- Do not claim any step has already been executed or produced a result -- describe the plan, not completed work."""


def generate_paper_methods(
    title: str,
    abstract: str,
    introduction: str,
    methods: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    raw = call_claude_fn(paper_methods_prompt(title, abstract, introduction, methods))
    return extract_block(raw, "PAPER_METHODS", repair_fn=call_claude_fn)


def results_placeholder(methods: str) -> str:
    """A fixed, non-LLM-generated placeholder for the Results section.

    No analysis has actually been run anywhere in this pipeline, so unlike
    every other section in this module, this one makes zero `claude` calls
    and asserts zero findings -- an LLM asked to fill this in would have no
    real data to describe and would necessarily fabricate numbers.
    """
    return (
        "*This section is a placeholder.* No analysis has been executed against "
        "real data yet -- the Methods section above describes the planned "
        "analysis, not completed work. Once the student has carried out that "
        "analysis, this section should report the actual measurements, figures, "
        "and statistical tests obtained, and should be rewritten (not "
        "auto-generated) from those real results.\n\n"
        "Anticipated deliverables to report here, per the Methods section: "
        "the concrete outputs described in its final step(s) (e.g. maps, "
        "spectra, fitted parameters, tables) once produced."
    )


def conclusions_prompt(
    title: str, abstract: str, introduction: str, methods_section: str, results_section: str
) -> str:
    return f"""Below is the title, abstract, introduction, methods, and results (a placeholder, since no analysis has been executed yet) for a planned scientific study. Write a Conclusions section appropriate for this pre-results stage.

Paper title:
{title}

Paper abstract:
{abstract}

Paper introduction:
{introduction}

Paper methods:
{methods_section}

Results:
{results_section}

Respond in the following format:

\\begin{{CONCLUSIONS}}
<CONCLUSIONS>
\\end{{CONCLUSIONS}}

In <CONCLUSIONS> put the Conclusions section. Follow these guidelines:
- Write in plain markdown prose, no LaTeX commands.
- Briefly restate the problem and the planned approach.
- Describe, conditionally, what different possible outcomes of the analysis would each imply -- do not assert which outcome will occur.
- Explicitly state that this section must be rewritten once real results exist; do not present it as a finished summary of findings.
- Do not add citations."""


def generate_conclusions(
    title: str,
    abstract: str,
    introduction: str,
    methods_section: str,
    results_section: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    raw = call_claude_fn(
        conclusions_prompt(title, abstract, introduction, methods_section, results_section)
    )
    return extract_block(raw, "CONCLUSIONS", repair_fn=call_claude_fn)


def references_section(literature: str) -> str:
    """Pull just the CITATIONS list out of literature.md's VERDICT/JUSTIFICATION/
    CITATIONS block (Stage 6's format) for use as the paper's References section.
    Falls back to the whole literature text if that heading isn't found, rather
    than silently dropping it."""
    marker = "CITATIONS:"
    idx = literature.find(marker)
    if idx == -1:
        return literature.strip()
    return literature[idx + len(marker):].strip()


def format_results_for_prompt(results: dict) -> str:
    """Render the analysis.py results dict as a compact, human-readable text
    block for the prompts below -- the single source of truth those prompts
    are told to draw every number from."""
    cont = results["continuum"]
    hcn = results["hcn"]
    lines = [
        f"Target: {results['target']}",
        f"Adopted distance: {results['distance_mpc']} Mpc (Virgo Cluster mean, NGVS SBF catalog)",
        f"Adopted systemic velocity: {results['systemic_velocity_kms']:.0f} km/s (heliocentric, NED)",
        f"alpha_HCN dense-gas conversion factor used: {results['alpha_hcn_msun_per_K_kms_pc2']} Msun / (K km/s pc^2) (Gao & Solomon 2004)",
        "",
        "--- Band 3 continuum ---",
        f"Synthesized beam: {cont['beam_arcsec'][0]:.2f} x {cont['beam_arcsec'][1]:.2f} arcsec, PA {cont['beam_arcsec'][2]:.1f} deg",
        f"RMS noise: {float(cont['rms_mjy_beam']):.4f} mJy/beam",
    ]
    for ap in cont["apertures"]:
        kind = "3-sigma upper limit" if ap["is_limit"] else "detection"
        lines.append(
            f"  Aperture r={ap['radius_beams']:.0f} beam ({ap['radius_arcsec']:.2f} arcsec = {ap['radius_pc']:.0f} pc): "
            f"{ap['value']:.3f} +/- {ap['error']:.3f} mJy ({kind}, S/N={ap['snr']:.1f})"
        )
    lines += [
        "",
        "--- HCN(1-0) cube ---",
        f"Rest frequency: {hcn['rest_freq_ghz']:.4f} GHz",
        f"Channel width: {hcn['channel_width_kms']:.1f} km/s; searched +/-{hcn['line_search_window_kms']:.0f} km/s "
        f"around systemic ({hcn['n_channels_in_line_window']} channels)",
        f"Synthesized beam: {hcn['beam_arcsec'][0]:.2f} x {hcn['beam_arcsec'][1]:.2f} arcsec, PA {hcn['beam_arcsec'][2]:.1f} deg",
        f"Per-channel RMS: {hcn['rms_mjy_beam_per_channel']:.3f} mJy/beam",
    ]
    for ap in hcn["apertures"]:
        kind = "3-sigma upper limit" if ap["is_limit"] else "detection"
        lines.append(
            f"  Aperture r={ap['radius_beams']:.0f} beam ({ap['radius_arcsec']:.2f} arcsec = {ap['radius_pc']:.0f} pc): "
            f"integrated flux {ap['flux_jy_kms']:.3f} +/- {ap['flux_err_jy_kms']:.3f} Jy km/s ({kind}, S/N={ap['snr']:.2f}); "
            f"L'_HCN = {ap['l_hcn_K_kms_pc2']:.3e} K km/s pc^2; dense-gas mass = {ap['mass_dense_gas_msun']:.3e} Msun"
        )
    lines += [
        f"1-3 beam annulus: {hcn['central_annulus_flux_jy_kms']:.3f} Jy km/s "
        f"({'3-sigma upper limit' if hcn['central_annulus_is_limit'] else 'detection'})",
        f"Central-depression log10 ratio (1-beam / 1-3-beam-annulus): "
        f"{hcn['central_depression_log_ratio']:.3f}" if hcn["central_depression_log_ratio"] is not None else
        "Central-depression log10 ratio: not computable (a value was non-positive)",
        f"Interpretation: {hcn['central_depression_interpretation']}",
        f"Kinematic note: {hcn['kinematic_note']}",
    ]
    return "\n".join(lines)


def real_methods_prompt(methods_plan: str, results_text: str) -> str:
    return f"""Given the planned methods description and the actual measured analysis results below, write the Methods section of a scientific paper describing analysis that has ALREADY BEEN CARRIED OUT (past tense) -- this is not a plan, the analysis below was actually executed against real downloaded ALMA FITS data.

Planned methods (the plan that was followed):
{methods_plan}

Actual measured results (proof the analysis was executed; also given to you in full for the Results section separately):
{results_text}

Respond in the following format:

\\begin{{PAPER_METHODS}}
<PAPER_METHODS>
\\end{{PAPER_METHODS}}

In <PAPER_METHODS> put the Methods section. Follow these guidelines:
- Write in plain markdown prose, past tense, using subheadings (###) where useful, no LaTeX commands.
- Describe the dataset, the analysis steps actually taken (moment maps, beam-scaled aperture photometry, detection/limit rule, HCN luminosity and dense-gas-mass conversion, the central-depression metric, the position-velocity cut, the continuum cross-check), and the tools used (spectral-cube, astropy, photutils, radio_beam), preserving every concrete step and number from the planned methods above -- do not invent new steps or drop existing ones.
- State plainly that this was executed against the two named FITS products, not merely planned.
- Do not write citations other than the two explicitly given external constants (adopted distance and alpha_HCN), and cite those exactly as named in the results text.
- Do not report specific numeric results here -- those belong in the Results section; this section describes what was done and how."""


def generate_real_methods(
    methods_plan: str,
    results_text: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    raw = call_claude_fn(real_methods_prompt(methods_plan, results_text))
    return extract_block(raw, "PAPER_METHODS", repair_fn=call_claude_fn)


def real_results_prompt(results_text: str) -> str:
    return f"""Below is a complete, exact set of measured results from a real analysis of downloaded ALMA FITS data (a Band 3 continuum image and an HCN(1-0) spectral-line cube). Write the Results section of a scientific paper reporting these findings.

Measured results (the ONLY numbers you may use -- do not invent, round in a way that loses meaning, or add any number not given here):
{results_text}

There are three figures available, refer to them by these exact labels:
- Figure 1: the Band 3 continuum image with the three photometry apertures overlaid.
- Figure 2: the HCN(1-0) moment 0/1/2 maps.
- Figure 3: the HCN(1-0) position-velocity cut through the nucleus.

Respond in the following format:

\\begin{{RESULTS}}
<RESULTS>
\\end{{RESULTS}}

In <RESULTS> put the Results section. Follow these guidelines:
- Write in plain markdown prose, past tense, using subheadings (###) where useful, no LaTeX commands.
- Report the continuum nuclear detection (flux, S/N, at each aperture radius) and reference Figure 1.
- Report the HCN(1-0) aperture measurements/limits, the derived luminosities and dense-gas masses, and reference Figure 2.
- Report the central-depression metric and state its interpretation exactly as given -- do not overstate a non-detection as a confirmed hole, and do not understate a real detection.
- Report the kinematic note and reference Figure 3, honestly reflecting whether the data support any statement about rotation given how few (if any) pixels were significantly detected.
- State every number with its uncertainty or upper-limit status exactly as given (detection vs. 3-sigma upper limit).
- Do not draw broader physical conclusions here (e.g. about AGN feedback or the black hole) -- that belongs in Conclusions; this section reports measurements only."""


def generate_real_results(
    results_text: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    raw = call_claude_fn(real_results_prompt(results_text))
    return extract_block(raw, "RESULTS", repair_fn=call_claude_fn)


def real_conclusions_prompt(title: str, abstract: str, introduction: str, methods_section: str, results_section: str) -> str:
    return f"""Below is the title, abstract, introduction, methods, and results (all real -- the analysis was actually executed) for a completed pilot study. Write a Conclusions section.

Paper title:
{title}

Paper abstract:
{abstract}

Paper introduction:
{introduction}

Paper methods:
{methods_section}

Paper results:
{results_section}

Respond in the following format:

\\begin{{CONCLUSIONS}}
<CONCLUSIONS>
\\end{{CONCLUSIONS}}

In <CONCLUSIONS> put the Conclusions section. Follow these guidelines:
- Write in plain markdown prose, no LaTeX commands.
- Draw conclusions genuinely supported by the actual Results above -- do not overclaim a firm detection of a circumnuclear hole from what may be a beam-limited, sensitivity-limited non-detection; state clearly what was and was not established.
- Explicitly state the two main limitations: the coarse (>1.6 arcsec / >130 pc) beam relative to the ~10-100 pc scale of the phenomenon under study, and the narrow "representative bandwidth" velocity coverage of the delivered cube.
- Suggest concretely what additional data (e.g. a wider-bandwidth or higher-resolution follow-up) would be needed to resolve the ambiguity, without asserting that follow-up already happened.
- Do not add citations."""


def generate_real_conclusions(
    title: str,
    abstract: str,
    introduction: str,
    methods_section: str,
    results_section: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    raw = call_claude_fn(
        real_conclusions_prompt(title, abstract, introduction, methods_section, results_section)
    )
    return extract_block(raw, "CONCLUSIONS", repair_fn=call_claude_fn)


def real_title_abstract_prompt(idea: str, methods_plan: str, results_text: str) -> str:
    return f"""You are an astrophysicist drafting the title and abstract for a paper reporting a completed pilot analysis (real data, real measurements -- not a proposal). Given the idea, planned methods, and actual measured results below, write a title and an abstract.

Idea:
{idea}

Planned methods:
{methods_plan}

Actual measured results:
{results_text}

Respond in the following format:

\\begin{{TITLE}}
<TITLE>
\\end{{TITLE}}

\\begin{{ABSTRACT}}
<ABSTRACT>
\\end{{ABSTRACT}}

In <TITLE> put the paper's title. In <ABSTRACT> put a single-paragraph abstract, past tense, that: briefly motivates the problem, briefly describes the dataset and method, and reports the actual headline finding(s) (including if the headline finding is a non-detection / upper limit -- state that honestly, do not imply a stronger result than was found). Do not invent any number not given above. Plain markdown prose, no LaTeX, no citations."""


def generate_real_title_and_abstract(
    idea: str,
    methods_plan: str,
    results_text: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> tuple[str, str]:
    raw = call_claude_fn(real_title_abstract_prompt(idea, methods_plan, results_text))
    title = extract_block(raw, "TITLE", repair_fn=call_claude_fn)
    abstract = extract_block(raw, "ABSTRACT", repair_fn=call_claude_fn)
    return title, abstract


def assemble_paper_with_results(
    idea: str,
    methods: str,
    literature: str,
    results: dict,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    """Like assemble_paper, but for a project where real analysis was
    actually executed (analysis.py) against downloaded ALMA FITS data.
    Every section is written in completed/past tense and grounded in the
    real `results` dict -- there is no placeholder Results section here."""
    results_text = format_results_for_prompt(results)

    title, abstract = generate_real_title_and_abstract(idea, methods, results_text, call_claude_fn=call_claude_fn)
    introduction = generate_introduction(title, abstract, idea, methods, call_claude_fn=call_claude_fn)
    methods_section = generate_real_methods(methods, results_text, call_claude_fn=call_claude_fn)
    results_section = generate_real_results(results_text, call_claude_fn=call_claude_fn)
    conclusions = generate_real_conclusions(
        title, abstract, introduction, methods_section, results_section, call_claude_fn=call_claude_fn
    )
    references = references_section(literature)

    return {
        "title": title,
        "abstract": abstract,
        "introduction": introduction,
        "methods": methods_section,
        "results": results_section,
        "conclusions": conclusions,
        "references": references,
    }


def assemble_paper(
    idea: str,
    methods: str,
    literature: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    """Assemble a full paper draft from a settled idea, methods, and literature.

    Every `claude` call is routed through `call_claude_fn` (Stage 3/5/7/8's
    injection pattern) so this can be unit tested for $0; it defaults to the
    real Stage 1 `call_claude`, which makes several live, cost-incurring CLI
    calls (one each for title+abstract, introduction, methods, conclusions).
    """
    title, abstract = generate_title_and_abstract(idea, methods, call_claude_fn=call_claude_fn)
    introduction = generate_introduction(title, abstract, idea, methods, call_claude_fn=call_claude_fn)
    methods_section = generate_paper_methods(
        title, abstract, introduction, methods, call_claude_fn=call_claude_fn
    )
    results_section = results_placeholder(methods)
    conclusions = generate_conclusions(
        title, abstract, introduction, methods_section, results_section, call_claude_fn=call_claude_fn
    )
    references = references_section(literature)

    return (
        f"# {title}\n\n"
        f"{DRAFT_BANNER}\n"
        f"## Abstract\n\n{abstract}\n\n"
        f"## 1. Introduction\n\n{introduction}\n\n"
        f"## 2. Methods\n\n{methods_section}\n\n"
        f"## 3. Results\n\n{results_section}\n\n"
        f"## 4. Conclusions\n\n{conclusions}\n\n"
        f"## References\n\n{references}\n"
    )
