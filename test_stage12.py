"""Stage 12 offline unit tests (student_plan.py, full_document.py) -- zero
live `claude` calls.

Follows Stage 3/5/6/7/8/9/11's dependency-injection pattern.
"""
from __future__ import annotations

from full_document import assemble_full_document
from student_plan import (
    achievability_caution_banner,
    generate_student_plan,
    parse_achievable,
    parse_total_weeks,
)


def test_parse_total_weeks_reads_the_reported_number():
    plan = "1. Do a thing -- 2 days\n\nTOTAL ESTIMATED TIME: 30 weeks\nACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: YES"
    assert parse_total_weeks(plan) == 30
    print("[PASS] parse_total_weeks reads the self-reported total")


def test_parse_total_weeks_missing_returns_none():
    assert parse_total_weeks("no such line here") is None
    print("[PASS] parse_total_weeks returns None rather than guessing when the line is missing")


def test_parse_achievable_reads_yes_and_no():
    assert parse_achievable("ACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: YES") is True
    assert parse_achievable("ACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: NO") is False
    assert parse_achievable("no such line") is None
    print("[PASS] parse_achievable reads YES/NO/missing correctly")


def test_achievability_banner_empty_when_plan_fits_budget():
    plan = "1. Step one -- 1 week\n\nTOTAL ESTIMATED TIME: 20 weeks\nACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: YES"
    assert achievability_caution_banner(plan) == ""
    print("[PASS] no caution banner when the plan reports it fits the thesis budget")


def test_achievability_banner_fires_on_explicit_no_verdict():
    plan = "1. Step one -- 40 weeks\n\nTOTAL ESTIMATED TIME: 45 weeks\nACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: NO"
    banner = achievability_caution_banner(plan)
    assert "Caution" in banner
    assert "NOT achievable" in banner
    print("[PASS] caution banner fires when the plan itself says NO")


def test_achievability_banner_fires_on_total_weeks_over_budget_even_if_verdict_says_yes():
    # regression guard: don't just trust a self-reported YES if the math doesn't back it up
    plan = "1. Step one -- 60 weeks\n\nTOTAL ESTIMATED TIME: 60 weeks\nACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: YES"
    banner = achievability_caution_banner(plan, max_weeks=52)
    assert "Caution" in banner
    assert "60 weeks" in banner
    print("[PASS] caution banner fires on an over-budget total even when the self-reported verdict says YES")


def test_generate_student_plan_prepends_banner_only_when_needed():
    def fake_over_budget(prompt: str) -> str:
        return (
            "\\begin{STUDENT_PLAN}\n"
            "1. Step one -- 60 weeks\n\n"
            "TOTAL ESTIMATED TIME: 60 weeks\n"
            "ACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: NO\n"
            "\\end{STUDENT_PLAN}"
        )

    result = generate_student_plan("idea", "methods", call_claude_fn=fake_over_budget)
    assert result.startswith("> **Caution")
    assert "60 weeks" in result

    def fake_fits(prompt: str) -> str:
        return (
            "\\begin{STUDENT_PLAN}\n"
            "1. Step one -- 3 weeks\n\n"
            "TOTAL ESTIMATED TIME: 20 weeks\n"
            "ACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: YES\n"
            "\\end{STUDENT_PLAN}"
        )

    result2 = generate_student_plan("idea", "methods", call_claude_fn=fake_fits)
    assert not result2.startswith(">")
    assert result2.startswith("1. Step one")
    print("[PASS] generate_student_plan only prepends the banner when the plan itself signals a problem")


def test_assemble_full_document_combines_plan_and_paper_in_order():
    calls = {"n": 0}

    def fake(prompt: str) -> str:
        calls["n"] += 1
        i = calls["n"]
        if i == 1:
            return (
                "\\begin{STUDENT_PLAN}\n1. Do the thing -- 2 weeks\n\n"
                "TOTAL ESTIMATED TIME: 10 weeks\n"
                "ACHIEVABLE IN ONE UNDERGRADUATE THESIS YEAR: YES\n\\end{STUDENT_PLAN}"
            )
        if i == 2:
            return "\\begin{TITLE}\nMy Title\n\\end{TITLE}\n\\begin{ABSTRACT}\nMy abstract.\n\\end{ABSTRACT}"
        if i == 3:
            return "\\begin{INTRODUCTION}\nMy intro.\n\\end{INTRODUCTION}"
        if i == 4:
            return "\\begin{PAPER_METHODS}\nMy methods.\n\\end{PAPER_METHODS}"
        if i == 5:
            return "\\begin{CONCLUSIONS}\nMy conclusions.\n\\end{CONCLUSIONS}"
        raise AssertionError(f"unexpected extra call #{i}")

    literature = "VERDICT: NOT_PUBLISHED\nCITATIONS:\n(none)"
    doc = assemble_full_document("idea", "methods", literature, call_claude_fn=fake)

    assert calls["n"] == 5, "1 for the plan + 4 for the paper, no more"
    plan_idx = doc.find("Step-by-Step Project Plan")
    paper_idx = doc.find("# My Title")
    assert plan_idx != -1 and paper_idx != -1
    assert plan_idx < paper_idx, "the student plan must come before the paper draft"
    assert "Do the thing" in doc
    assert "My abstract." in doc
    assert "Draft status: pre-analysis" in doc, "paper.py's placeholder-results banner must survive unchanged"
    print("[PASS] assemble_full_document puts the student plan first, then the full paper, 5 calls total")


def main() -> int:
    test_parse_total_weeks_reads_the_reported_number()
    test_parse_total_weeks_missing_returns_none()
    test_parse_achievable_reads_yes_and_no()
    test_achievability_banner_empty_when_plan_fits_budget()
    test_achievability_banner_fires_on_explicit_no_verdict()
    test_achievability_banner_fires_on_total_weeks_over_budget_even_if_verdict_says_yes()
    test_generate_student_plan_prepends_banner_only_when_needed()
    test_assemble_full_document_combines_plan_and_paper_in_order()
    print("\n[PASS] all Stage 12 offline checks passed, $0 cost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
