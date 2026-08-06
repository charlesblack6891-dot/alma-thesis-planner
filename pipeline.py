"""End-to-end orchestration with published/unpublished short-circuit (Stage 9).

Wires Stages 5-8 (idea loop, methods, writeup) behind Stage 6's
published/novelty check: if the verdict is PUBLISHED, short-circuits to a
citation-only note; if NOT_PUBLISHED, runs the full idea -> methods ->
writeup pipeline. A verdict of UNKNOWN (the check couldn't parse a clean
verdict) also short-circuits, rather than silently treating it as either
published or unpublished.

All Claude/network calls are injectable (Stage 3/5/6/7/8's pattern) so the
branching logic itself can be unit tested for $0, with zero live calls.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from idea_loop import IdeaLoopResult, run_idea_loop, score_tractability
from literature import LiteratureResult, check_published
from methods import generate_methods
from state import IDEA_FILE, LITERATURE_FILE, METHODS_FILE, WRITEUP_FILE, write_state_file
from writeup import assemble_writeup


def tractability_failures(score: str) -> list[str]:
    """Return the SCORE block lines that answered NO. Empty if all YES or unparseable.

    Splits each line on '--' before checking for a whole-word "NO" so a
    justification sentence that happens to contain "NO" (e.g. "no new
    instrumentation") never gets misread as a failed verdict.
    """
    failures = []
    for line in score.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        verdict_part = stripped.split("--", 1)[0]
        if re.search(r"\bNO\b", verdict_part.upper()):
            failures.append(stripped)
    return failures


def tractability_caution_banner(score: str) -> str:
    """A caution banner to prepend to the writeup if the idea failed any tractability
    check. Empty string if the idea passed everything (or the score is unparseable).

    This is a soft flag, not a hard gate: PROJECT_BRIEF.md's own framing is that the
    output is a plan for a *human* to execute, not an automated pipeline, so a weak idea
    is still surfaced -- just with an explicit warning up front -- rather than silently
    discarded or silently presented as fully vetted.
    """
    failures = tractability_failures(score)
    if not failures:
        return ""
    failure_lines = "\n".join(f"> - {f}" for f in failures)
    return (
        "> **Caution: this idea did not pass all of Stage 5's own tractability checks.** "
        "Review the failed item(s) below before treating this as a ready-to-execute thesis "
        "plan.\n"
        f"{failure_lines}\n\n"
    )


def short_circuit_note(project_code: str, verdict: str, literature_block: str) -> str:
    if verdict == "PUBLISHED":
        header = (
            f"# {project_code} -- Already Published\n\n"
            "This dataset's publication/novelty check determined it has already been "
            "used in a peer-reviewed publication, so no new thesis-project plan was "
            "generated. See the citation below.\n\n"
        )
    else:
        header = (
            f"# {project_code} -- Publication Status Unclear\n\n"
            "This dataset's publication/novelty check could not confidently determine "
            "a PUBLISHED/NOT_PUBLISHED verdict from the available evidence. No "
            "thesis-project plan was generated automatically -- review the evidence "
            "below and re-run manually once the verdict is resolved.\n\n"
        )
    return header + literature_block + "\n"


@dataclass
class PipelineResult:
    literature: LiteratureResult
    short_circuited: bool
    writeup: str
    idea: str | None = None
    methods: str | None = None
    tractability_score: str | None = None


def run_pipeline(
    project_code: str,
    pi: str,
    target: str,
    data_description: str,
    *,
    n_iterations: int = 4,
    check_published_fn: Callable[..., LiteratureResult] = check_published,
    run_idea_loop_fn: Callable[..., IdeaLoopResult] = run_idea_loop,
    score_tractability_fn: Callable[..., str] = score_tractability,
    generate_methods_fn: Callable[..., str] = generate_methods,
    assemble_writeup_fn: Callable[..., str] = assemble_writeup,
    include_writeup: bool = True,
    on_stage_complete: Callable[[str, str], None] | None = None,
) -> PipelineResult:
    """Run the full Stage 9 pipeline for one project, branching on Stage 6's verdict.

    Only calls Stage 5/7/8 functions on the NOT_PUBLISHED branch -- callers relying on
    the default (real) functions should expect zero Stage 5/7/8 cost on the other two
    verdicts.

    `include_writeup=False` skips the final assemble_writeup_fn call entirely --
    added after a live failure where that call (the single largest prompt in the
    whole chain, since it folds idea+methods+literature together) failed with a
    bare CLI exit code and no stderr, and callers that never use `.writeup`
    (wizard.py's GUI flow only reads `.idea`/`.methods`) were paying for and risking
    it anyway. Default stays True so existing CLI callers (run_pipeline.py,
    run_auto.py) that do write writeup.md are unaffected.

    `on_stage_complete(stage_name, content)`, if given, is called with
    ("literature"|"idea"|"methods", <raw text>) the moment each stage finishes --
    lets a caller checkpoint to disk immediately rather than only after the whole
    pipeline (writeup included) succeeds. Confirmed live to matter: without it, a
    late-stage failure discarded 11 already-paid-for Claude calls' worth of idea
    and methods work with nothing written anywhere.
    """
    lit_result = check_published_fn(project_code, pi, target, data_description)
    if on_stage_complete:
        on_stage_complete("literature", lit_result.raw)

    if lit_result.verdict != "NOT_PUBLISHED":
        return PipelineResult(
            literature=lit_result,
            short_circuited=True,
            writeup=short_circuit_note(project_code, lit_result.verdict, lit_result.raw),
        )

    idea_result = run_idea_loop_fn(data_description, n_iterations=n_iterations)
    if on_stage_complete:
        on_stage_complete("idea", idea_result.final_idea)

    score = score_tractability_fn(data_description, idea_result.final_idea)

    methods = generate_methods_fn(data_description, idea_result.final_idea)
    if on_stage_complete:
        on_stage_complete("methods", methods)

    if include_writeup:
        writeup = tractability_caution_banner(score) + assemble_writeup_fn(
            idea_result.final_idea, methods, lit_result.raw
        )
    else:
        writeup = ""

    return PipelineResult(
        literature=lit_result,
        short_circuited=False,
        writeup=writeup,
        idea=idea_result.final_idea,
        methods=methods,
        tractability_score=score,
    )


def report_pipeline_result(project_dir: str, result: PipelineResult) -> None:
    """Print a PipelineResult and persist its stages to `project_dir`'s state files.

    Shared by every entrypoint that runs the full Stage 9 pipeline (currently
    run_pipeline.py and run_auto.py) so they stay in lockstep rather than
    each hand-rolling their own copy of this print/write sequence.
    """
    print(result.literature.raw)
    write_state_file(project_dir, LITERATURE_FILE, result.literature.raw + "\n")
    print(f"\nParsed verdict: {result.literature.verdict}")

    if result.short_circuited:
        print("\n[SHORT-CIRCUIT] Skipping idea/methods/writeup stages.")
        path = write_state_file(project_dir, WRITEUP_FILE, result.writeup)
        print(f"[DONE] wrote short-circuit note to {path}")
        return

    print("\nStage 5: idea loop settled on:\n")
    print(result.idea)
    print("\nTractability score:\n" + result.tractability_score)
    write_state_file(project_dir, IDEA_FILE, result.idea + "\n")

    print("\nStage 7: methods\n")
    print(result.methods)
    write_state_file(project_dir, METHODS_FILE, result.methods + "\n")

    print("\nStage 8: writeup\n")
    print(result.writeup)
    path = write_state_file(project_dir, WRITEUP_FILE, result.writeup + "\n")
    word_count = len(result.writeup.split())
    print(f"\n[DONE] wrote full pipeline output to {path} ({word_count} words)")
