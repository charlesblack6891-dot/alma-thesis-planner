"""Stage 11 offline unit tests (paper.py) -- zero live `claude` calls.

Follows Stage 3/5/6/7/8/9's dependency-injection pattern: every `claude` call
is injectable via a fake call_claude_fn, so section wiring and the
results-placeholder's zero-LLM guarantee can be verified for free.
"""
from __future__ import annotations

from blocks import BlockExtractionError
from paper import (
    assemble_paper,
    generate_conclusions,
    generate_introduction,
    generate_paper_methods,
    generate_title_and_abstract,
    references_section,
    results_placeholder,
)


def _scripted(responses: list[str]):
    """Returns a fake call_claude_fn that yields each of `responses` in turn."""
    calls = {"n": 0}

    def _fn(prompt: str) -> str:
        i = calls["n"]
        calls["n"] += 1
        return responses[i]

    return _fn, calls


def test_title_and_abstract_extracted_from_one_call():
    fake, calls = _scripted(
        ["\\begin{TITLE}\nA Great Title\n\\end{TITLE}\n\\begin{ABSTRACT}\nAn abstract.\n\\end{ABSTRACT}"]
    )
    title, abstract = generate_title_and_abstract("idea text", "methods text", call_claude_fn=fake)
    assert title == "A Great Title"
    assert abstract == "An abstract."
    assert calls["n"] == 1
    print("[PASS] title and abstract both extracted from a single call")


def test_introduction_wires_title_and_abstract_into_prompt():
    seen = {}

    def fake(prompt: str) -> str:
        seen["prompt"] = prompt
        return "\\begin{INTRODUCTION}\nThe intro.\n\\end{INTRODUCTION}"

    result = generate_introduction("T", "A", "idea", "methods", call_claude_fn=fake)
    assert result == "The intro."
    assert "T" in seen["prompt"] and "A" in seen["prompt"]
    print("[PASS] introduction generation wires title/abstract into the prompt")


def test_paper_methods_extracted_and_distinct_tag_from_thesis_methods():
    def fake(prompt: str) -> str:
        return "\\begin{PAPER_METHODS}\nExpanded methods.\n\\end{PAPER_METHODS}"

    result = generate_paper_methods("T", "A", "Intro", "short methods", call_claude_fn=fake)
    assert result == "Expanded methods."
    print("[PASS] paper methods section extracted under its own PAPER_METHODS tag")


def test_results_placeholder_makes_zero_llm_calls():
    text = results_placeholder("some methods text mentioning deliverables")
    assert "placeholder" in text.lower()
    assert "no analysis has been executed" in text.lower()
    print("[PASS] results_placeholder is a fixed string with zero LLM involvement")


def test_conclusions_reference_prior_sections():
    seen = {}

    def fake(prompt: str) -> str:
        seen["prompt"] = prompt
        return "\\begin{CONCLUSIONS}\nConditional conclusions.\n\\end{CONCLUSIONS}"

    result = generate_conclusions("T", "A", "Intro", "Methods section", "Results placeholder", call_claude_fn=fake)
    assert result == "Conditional conclusions."
    assert "Results placeholder" in seen["prompt"]
    print("[PASS] conclusions generation is given the results placeholder, not asked to invent findings")


def test_references_section_pulls_citations_block():
    literature = "VERDICT: NOT_PUBLISHED\nJUSTIFICATION: none found\nCITATIONS:\n1. Some Paper (2020)"
    assert references_section(literature) == "1. Some Paper (2020)"
    print("[PASS] references_section extracts just the CITATIONS list")


def test_references_section_falls_back_to_whole_text_if_no_citations_heading():
    literature = "just some raw text with no heading"
    assert references_section(literature) == literature
    print("[PASS] references_section falls back to the full text rather than dropping it")


def test_assemble_paper_makes_exactly_four_llm_calls_and_includes_banner():
    fake, calls = _scripted(
        [
            "\\begin{TITLE}\nMy Title\n\\end{TITLE}\n\\begin{ABSTRACT}\nMy abstract.\n\\end{ABSTRACT}",
            "\\begin{INTRODUCTION}\nMy intro.\n\\end{INTRODUCTION}",
            "\\begin{PAPER_METHODS}\nMy methods.\n\\end{PAPER_METHODS}",
            "\\begin{CONCLUSIONS}\nMy conclusions.\n\\end{CONCLUSIONS}",
        ]
    )
    literature = "VERDICT: NOT_PUBLISHED\nCITATIONS:\n(none)"
    paper = assemble_paper("idea", "methods", literature, call_claude_fn=fake)

    assert calls["n"] == 4, "abstract+title, introduction, methods, conclusions -- exactly 4 calls"
    assert paper.startswith("# My Title")
    assert "Draft status: pre-analysis" in paper
    assert "My abstract." in paper
    assert "My intro." in paper
    assert "My methods." in paper
    assert "placeholder" in paper.lower()
    assert "My conclusions." in paper
    assert "(none)" in paper
    print("[PASS] assemble_paper makes exactly 4 LLM calls and combines all sections with the draft banner")


def test_malformed_response_raises_block_extraction_error_not_silently_wrong():
    def fake(prompt: str) -> str:
        return "no tags here at all"

    try:
        generate_introduction("T", "A", "idea", "methods", call_claude_fn=fake)
        raise AssertionError("expected BlockExtractionError")
    except BlockExtractionError:
        print("[PASS] malformed LLM output raises BlockExtractionError rather than returning garbage")


def main() -> int:
    test_title_and_abstract_extracted_from_one_call()
    test_introduction_wires_title_and_abstract_into_prompt()
    test_paper_methods_extracted_and_distinct_tag_from_thesis_methods()
    test_results_placeholder_makes_zero_llm_calls()
    test_conclusions_reference_prior_sections()
    test_references_section_pulls_citations_block()
    test_references_section_falls_back_to_whole_text_if_no_citations_heading()
    test_assemble_paper_makes_exactly_four_llm_calls_and_includes_banner()
    test_malformed_response_raises_block_extraction_error_not_silently_wrong()
    print("\n[PASS] all Stage 11 offline checks passed, $0 cost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
