"""Goalpost 1's concrete pass/fail check, named explicitly by Paul (see PLAN.md,
'First milestone and its verification criteria'):

    One command runs prompt-template -> Claude CLI -> markdown output,
    twice in a row, with zero manual intervention between runs.

Pass: both runs complete unattended, each producing a valid, non-empty
markdown file derived from the Claude CLI's response.
Fail: either run requires a manual step (permission prompt, re-auth, etc.),
hangs, or produces empty/malformed output.

This makes real, cost-incurring `claude` CLI calls (see PLAN.md session log
for per-call cost/latency figures) -- run deliberately, not part of the free
test_stage*.py suites.

Usage:
    python paul_check.py [project_dir]

If project_dir is omitted, a fresh temp directory is created and printed.
"""
from __future__ import annotations

import sys
import tempfile

from blocks import extract_block
from llm import call_claude
from state import IDEA_FILE, write_state_file

PROMPT_TEMPLATE = (
    "You are helping plan a senior thesis project based on this ALMA dataset:\n\n"
    "Project code: 2019.1.01234.S\n"
    "PI: J. Smith\n"
    "Target: NGC 1365\n"
    "Band: 6 (211-275 GHz)\n\n"
    "Propose ONE concrete, senior-thesis-scoped analysis idea in 2-3 sentences. "
    "Reply with ONLY the idea, wrapped in \\begin{IDEA}...\\end{IDEA}, no preamble, "
    "no code fences."
)


def run_once(project_dir: str, run_number: int) -> None:
    print(f"--- Run {run_number}: prompt-template -> Claude CLI -> markdown ---")
    raw = call_claude(PROMPT_TEMPLATE)
    idea = extract_block(raw, "IDEA")
    if not idea.strip():
        raise SystemExit(f"[FAIL] run {run_number}: extracted idea is empty")
    path = write_state_file(project_dir, IDEA_FILE, idea + "\n")
    print(f"[PASS] run {run_number}: wrote {len(idea)} chars to {path}")


def main() -> int:
    project_dir = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="paul_check_")
    print(f"project_dir = {project_dir}")
    run_once(project_dir, 1)
    run_once(project_dir, 2)
    print(
        "\n[PASS] both runs completed unattended, each wrote a valid non-empty "
        "markdown file -- Goalpost 1's named check is satisfied"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
