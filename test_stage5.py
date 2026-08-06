"""Stage 5 offline unit tests (idea_loop.py) -- zero live `claude` calls.

Follows Stage 3's dependency-injection pattern (see test_stage3.py's repair_fn
usage): run_idea_loop/score_tractability take an injectable call_claude_fn, so
loop mechanics -- iteration count, previous-ideas accumulation, criticism
feeding into the next round -- can be verified for free and deterministically,
before any real cost is spent on Stage 2's stress-tested primitive.
"""
from __future__ import annotations

from idea_loop import run_idea_loop, score_tractability


def _fake_call_claude(log: list[str]):
    """Canned responses for maker/hater/score prompts, keyed off text unique to
    each prompt type, with a per-type call counter baked into the reply so
    ordering and content-propagation can be asserted on."""
    counters = {"maker": 0, "hater": 0}

    def fn(prompt: str) -> str:
        log.append(prompt)
        if "Your goal is to propose" in prompt:
            counters["maker"] += 1
            n = counters["maker"]
            return f"\\begin{{IDEA}}\nidea-{n}\n\\end{{IDEA}}"
        if "Your goal is to critique" in prompt:
            counters["hater"] += 1
            n = counters["hater"]
            return f"\\begin{{CRITIC}}\ncritic-{n}\n\\end{{CRITIC}}"
        if "reviewing a proposed" in prompt:
            return "\\begin{SCORE}\n1. YES -- ok\n2. YES -- ok\n3. YES -- ok\n\\end{SCORE}"
        raise AssertionError(f"unexpected prompt: {prompt[:80]}")

    return fn


def test_loop_mechanics_and_call_count():
    log: list[str] = []
    fake = _fake_call_claude(log)
    result = run_idea_loop("synthetic toy dataset description", n_iterations=3, call_claude_fn=fake)

    assert len(result.iterations) == 3
    assert [step["idea"] for step in result.iterations] == ["idea-1", "idea-2", "idea-3"]
    assert [step["criticism"] for step in result.iterations] == ["critic-1", "critic-2", "critic-3"]
    assert result.final_idea == "idea-3"
    assert len(log) == 6, "3 iterations should be exactly 3 maker + 3 hater = 6 calls"
    print("[PASS] loop mechanics + call count (3 iterations -> 6 calls)")


def test_criticism_feeds_into_next_maker_prompt():
    log: list[str] = []
    fake = _fake_call_claude(log)
    run_idea_loop("synthetic toy dataset description", n_iterations=2, call_claude_fn=fake)

    # log order: maker1, hater1, maker2, hater2
    maker2_prompt = log[2]
    assert "critic-1" in maker2_prompt, "iteration 2's maker prompt should see iteration 1's criticism"
    assert "idea-1" in maker2_prompt, "iteration 2's maker prompt should see iteration 1's idea in previous_ideas"
    print("[PASS] criticism/previous-ideas propagate into next maker prompt")


def test_previous_ideas_accumulate_across_iterations():
    log: list[str] = []
    fake = _fake_call_claude(log)
    run_idea_loop("synthetic toy dataset description", n_iterations=3, call_claude_fn=fake)

    # log order: maker1, hater1, maker2, hater2, maker3, hater3
    maker3_prompt = log[4]
    assert "idea-1" in maker3_prompt and "idea-2" in maker3_prompt, (
        "iteration 3's maker prompt should carry both prior ideas in previous_ideas"
    )
    print("[PASS] previous_ideas accumulates across all prior iterations")


def test_score_tractability_parses_score_block():
    log: list[str] = []
    fake = _fake_call_claude(log)
    score = score_tractability("synthetic toy dataset description", "idea-3", call_claude_fn=fake)
    assert "YES" in score and "1." in score
    print("[PASS] score_tractability parses SCORE block")


def main() -> int:
    test_loop_mechanics_and_call_count()
    test_criticism_feeds_into_next_maker_prompt()
    test_previous_ideas_accumulate_across_iterations()
    test_score_tractability_parses_score_block()
    print("\n[PASS] all Stage 5 offline checks passed, $0 cost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
