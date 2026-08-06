"""Stage 6 offline unit tests (literature.py) -- zero live network/`claude` calls.

Follows Stage 3/5's dependency-injection pattern: both the Semantic Scholar
search and the Claude call are injectable, so verdict parsing and prompt
construction can be verified for free and deterministically.
"""
from __future__ import annotations

from literature import PaperHit, check_published, novelty_prompt


def test_verdict_parsing_published():
    def fake_search(query):
        return [PaperHit(title="Fake Paper", year=2020, authors=["A. Test"], abstract="abc", url="http://x")]

    def fake_claude(prompt):
        assert "Fake Paper" in prompt, "search results should be formatted into the prompt"
        return (
            "\\begin{LITERATURE}\n"
            "VERDICT: PUBLISHED\n"
            "JUSTIFICATION: matches result 1\n"
            "CITATIONS:\n1. Fake Paper (2020)\n"
            "\\end{LITERATURE}"
        )

    result = check_published(
        "2020.1.00001.S", "PI Test", "Target X", "desc",
        search_fn=fake_search, call_claude_fn=fake_claude,
    )
    assert result.verdict == "PUBLISHED"
    assert "Fake Paper" in result.raw
    print("[PASS] verdict parsing: PUBLISHED")


def test_verdict_parsing_not_published():
    def fake_search(query):
        return []

    def fake_claude(prompt):
        assert "(no results found)" in prompt
        return (
            "\\begin{LITERATURE}\n"
            "VERDICT: NOT_PUBLISHED\n"
            "JUSTIFICATION: no relevant results\n"
            "CITATIONS:\n(none directly relevant)\n"
            "\\end{LITERATURE}"
        )

    result = check_published(
        "2020.1.00002.S", "PI Test", "Target Y", "desc",
        search_fn=fake_search, call_claude_fn=fake_claude,
    )
    assert result.verdict == "NOT_PUBLISHED"
    print("[PASS] verdict parsing: NOT_PUBLISHED")


def test_not_published_substring_does_not_match_as_published():
    # regression check: "NOT_PUBLISHED" contains the substring "PUBLISHED" --
    # verdict parsing must check NOT_PUBLISHED first, not fall through to PUBLISHED.
    def fake_search(query):
        return []

    def fake_claude(prompt):
        return "\\begin{LITERATURE}\nVERDICT: NOT_PUBLISHED\nJUSTIFICATION: x\nCITATIONS:\nnone\n\\end{LITERATURE}"

    result = check_published("code", "pi", "target", "desc", search_fn=fake_search, call_claude_fn=fake_claude)
    assert result.verdict == "NOT_PUBLISHED", f"expected NOT_PUBLISHED, got {result.verdict!r}"
    print("[PASS] 'NOT_PUBLISHED' substring doesn't get misparsed as PUBLISHED")


def test_search_results_formatted_into_prompt_and_abstract_truncated():
    hits = [PaperHit(title="T1", year=2021, authors=["X", "Y"], abstract="A" * 600, url="u1")]
    prompt = novelty_prompt("code", "pi", "target", "desc", hits)
    assert "T1" in prompt and "X, Y" in prompt
    # abstract truncated to 500 chars -- prompt shouldn't balloon with a huge abstract
    assert prompt.count("A") < 600
    print("[PASS] search results formatted into prompt, abstract truncated")


def main() -> int:
    test_verdict_parsing_published()
    test_verdict_parsing_not_published()
    test_not_published_substring_does_not_match_as_published()
    test_search_results_formatted_into_prompt_and_abstract_truncated()
    print("\n[PASS] all Stage 6 offline checks passed, $0 cost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
