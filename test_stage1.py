"""Stage 1 verification: call_claude(prompt) -> str, proven on synthetic prompts.

Run directly (no pytest dependency needed):
    python test_stage1.py
"""
from __future__ import annotations

import os
import sys

from llm import _invoke, call_claude, ClaudeCLIError

IDEA_PROMPT = (
    "Reply with exactly the following, and nothing else, no preamble:\n"
    "\\begin{IDEA}\n"
    "This is a test idea.\n"
    "It has two lines.\n"
    "\\end{IDEA}"
)


def check_no_api_keys() -> None:
    leaked = [k for k in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY") if os.environ.get(k)]
    assert not leaked, f"expected these unset, found: {leaked}"
    print("[PASS] no API keys present in environment")


def check_pong(n: int = 3) -> None:
    for i in range(1, n + 1):
        result = _invoke("Reply with exactly the single word: PONG")
        text = result.text.strip()
        assert text == "PONG", f"call {i}: expected 'PONG', got {text!r}"
        print(
            f"[PASS] call {i}/{n}: PONG exact match "
            f"(wall_clock={result.wall_clock_s:.2f}s, duration_ms={result.duration_ms}, "
            f"cost_usd={result.cost_usd})"
        )


def check_idea_block() -> None:
    result = _invoke(IDEA_PROMPT)
    text = result.text
    assert "\\begin{IDEA}" in text, f"missing opening tag in: {text!r}"
    assert "\\end{IDEA}" in text, f"missing closing tag in: {text!r}"
    assert "This is a test idea." in text
    assert "It has two lines." in text
    print(f"[PASS] IDEA block round-tripped intact:\n{text}")


def check_call_claude_signature() -> None:
    text = call_claude("Reply with exactly the single word: PONG")
    assert text.strip() == "PONG", f"expected 'PONG', got {text!r}"
    print("[PASS] call_claude(prompt) -> str public signature works")


def main() -> int:
    checks = [
        check_no_api_keys,
        check_pong,
        check_idea_block,
        check_call_claude_signature,
    ]
    failures = 0
    for check in checks:
        try:
            check()
        except (AssertionError, ClaudeCLIError) as exc:
            failures += 1
            print(f"[FAIL] {check.__name__}: {exc}")
    print(f"\n{len(checks) - failures}/{len(checks)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
