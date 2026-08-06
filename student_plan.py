"""Undergraduate-readable, time-estimated step-by-step plan (Stage 12).

methods.md (Stage 7) is written in CASA/astronomy-research shorthand for
someone who already knows the field. This module rewrites it into a plain-
language, numbered checklist for a student who has never done this kind of
work before -- one estimated completion time per step, explaining jargon
inline rather than assuming it -- and then actually checks the achievability
claim it's given, rather than trusting the model's self-report at face
value: `achievability_caution_banner` parses the plan's own stated total time
and YES/NO verdict and prepends a warning if either one signals a plan that
doesn't fit a one-year undergraduate thesis, mirroring pipeline.py's existing
`tractability_caution_banner` pattern for the idea-loop's own scope check.
"""
from __future__ import annotations

import re
from typing import Callable

from blocks import extract_block
from llm import call_claude

MAX_THESIS_WEEKS = 52  # "a semester to a year" per this repo's own thesis-scope framing


def student_plan_prompt(idea: str, methods: str) -> str:
    return f"""You are a senior researcher rewriting a technical methods plan into a step-by-step guide for an undergraduate student who has never done astronomy research like this before. The student knows basic physics and some Python, but has not used CASA or worked with ALMA data before.

Given the idea and the technical methods below, rewrite it as a numbered list of concrete steps. Follow these rules:
- Number each step in the order it should be done.
- For each step, explain in plain English what to do and why it matters. When you use a technical term or tool name (e.g. `tclean`, moment map, self-calibration), briefly explain what it is in parentheses the first time it appears.
- For each step, give a realistic estimated time to complete it, assuming a student working on this project part-time (about 10-15 hours per week) who is learning the tools as they go. Use days or weeks, whichever fits (e.g. "about 3-5 days", "roughly 2 weeks").
- Do not drop or water down any concrete step, tool, number, or parameter from the technical methods below -- your job is to make it clearer and add time estimates, not to simplify away real content.
- Where a step is genuinely hard or open-ended (e.g. imaging quality, self-calibration convergence), say so honestly and suggest a fallback or a way to cap the time spent (e.g. "if this doesn't converge after 2 attempts, do X instead").
- Group steps under short section headers if that helps readability (e.g. "Getting the data", "Making the first images", "Measuring the results").

Idea:
{idea}

Technical methods:
{methods}

Respond in the following format:

\\begin{{STUDENT_PLAN}}
<STUDENT_PLAN>
\\end{{STUDENT_PLAN}}

In <STUDENT_PLAN>, put the full numbered plan. End it with exactly these two lines, filled in, and nothing after them:
TOTAL ESTIMATED TIME: <N> weeks
ACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: YES or NO"""


def parse_total_weeks(plan: str) -> int | None:
    """Pull the integer out of the plan's own 'TOTAL ESTIMATED TIME: N weeks' line."""
    for line in plan.splitlines():
        if line.strip().upper().startswith("TOTAL ESTIMATED TIME:"):
            match = re.search(r"\d+", line)
            if match:
                return int(match.group())
    return None


def parse_achievable(plan: str) -> bool | None:
    """Pull the YES/NO out of the plan's own achievability verdict line. None if missing."""
    for line in plan.splitlines():
        if line.strip().upper().startswith("ACHIEVABLE"):
            upper = line.upper()
            if "YES" in upper:
                return True
            if "NO" in upper:
                return False
    return None


def achievability_caution_banner(plan: str, *, max_weeks: int = MAX_THESIS_WEEKS) -> str:
    """A caution banner to prepend to the plan if its own self-reported time/verdict signals
    it doesn't fit a one-year undergraduate thesis. Empty string if it looks achievable (or
    the fields are missing/unparseable -- this is a soft, non-blocking flag, not a hard gate).
    """
    weeks = parse_total_weeks(plan)
    achievable = parse_achievable(plan)

    problems = []
    if achievable is False:
        problems.append(
            "the plan itself states it is NOT achievable in one undergraduate thesis year"
        )
    if weeks is not None and weeks > max_weeks:
        problems.append(
            f"the total estimated time ({weeks} weeks) exceeds a {max_weeks}-week (~1 year) thesis budget"
        )
    if not problems:
        return ""

    bullets = "\n".join(f"> - {p}" for p in problems)
    return (
        "> **Caution: this step-by-step plan may not fit one undergraduate thesis year.** "
        "Review the flagged issue(s) below before treating this as a ready-to-execute schedule "
        "-- consider cutting scope or extending the timeline.\n"
        f"{bullets}\n\n"
    )


def generate_student_plan(
    idea: str,
    methods: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    """Generate the undergraduate-readable, time-estimated plan, with a caution banner
    prepended if the plan's own self-reported time/verdict signals a scope problem.

    `call_claude_fn` is injectable (Stage 3/5/7/8's pattern) so this can be unit tested
    with zero live calls; it defaults to the real Stage 1 `call_claude`, which makes a
    live, cost-incurring CLI call.
    """
    raw = call_claude_fn(student_plan_prompt(idea, methods))
    plan = extract_block(raw, "STUDENT_PLAN", repair_fn=call_claude_fn)
    return achievability_caution_banner(plan) + plan
