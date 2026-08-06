"""Combined deliverable (Stage 12): the undergraduate-readable, time-estimated
step-by-step plan (student_plan.py) followed by the full paper draft (paper.py),
in one document.

Two audiences, two sections, no shared content duplicated: the plan is *how
to do the work* (plain language, one time estimate per step, an achievability
check against a one-year thesis budget); the paper is *what the finished
write-up looks like* (formal prose, Stage 11's DRAFT_BANNER and placeholder
Results carried through unchanged -- this module does not touch that
decision, it only appends the paper after the plan).
"""
from __future__ import annotations

from typing import Callable

from llm import call_claude
from paper import assemble_paper
from student_plan import generate_student_plan


def assemble_full_document(
    idea: str,
    methods: str,
    literature: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    """Assemble the student plan and the full paper draft into one document.

    Every `claude` call is routed through `call_claude_fn` (Stage 3/5/7/8/11's
    injection pattern) so this can be unit tested for $0; it defaults to the
    real Stage 1 `call_claude`, which makes five live, cost-incurring CLI
    calls total (one for the plan, four for the paper -- see paper.py).
    """
    plan = generate_student_plan(idea, methods, call_claude_fn=call_claude_fn)
    paper = assemble_paper(idea, methods, literature, call_claude_fn=call_claude_fn)

    return (
        "# Step-by-Step Project Plan (Student Guide)\n\n"
        f"{plan}\n\n"
        "---\n\n"
        f"{paper}"
    )
