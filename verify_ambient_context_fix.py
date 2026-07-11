"""Confirm the DEFAULT_DISALLOWED_TOOLS fix actually holds repeatably, not just once.

Re-runs the exact prompt that triggered ambient file/tool-use behavior in Stage 2's
Check 4 and the ambient-context investigation, 5 times through call_claude's new
default, and flags anything that still looks like tool-use leakage.
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from llm import _invoke

AMBIENT_PROMPT = (
    "Can you help me come up with a senior thesis idea for an ALMA dataset of "
    "NGC 1365? Please format your final answer inside \\begin{IDEA}...\\end{IDEA} tags."
)

SUSPICIOUS_MARKERS = [
    "PLAN.md",
    "BUILD_PLAN.md",
    "test_stage",
    "tool call",
    "memory/MEMORY",
    "MEMORY.md",
    "check memory",
    "let me check",
]


def main() -> int:
    leaks = 0
    for i in range(1, 6):
        result = _invoke(AMBIENT_PROMPT)
        text = result.text
        hits = [m for m in SUSPICIOUS_MARKERS if m.lower() in text.lower()]
        denials = result.raw.get("permission_denials")
        num_turns = result.raw.get("num_turns")
        status = "SUSPICIOUS" if hits else "CLEAN"
        print(f"run {i}/5: [{status}] num_turns={num_turns} permission_denials={denials} hits={hits}")
        print(f"  text[:200]: {text[:200]!r}")
        if hits:
            leaks += 1
    print(f"\n{5 - leaks}/5 runs clean")
    return 1 if leaks else 0


if __name__ == "__main__":
    sys.exit(main())
