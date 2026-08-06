"""Stage 9 offline unit tests (pipeline.py) -- zero live network/`claude` calls.

Follows Stage 3/5/6/7/8's dependency-injection pattern: every Claude/network
call is injectable, so the published/unpublished branching logic itself can
be verified for free and deterministically. The key thing to prove here is
that Stage 5/7/8 are never invoked on the PUBLISHED/UNKNOWN branches --
each fake below raises if called, so any accidental invocation fails loud.
"""
from __future__ import annotations

from idea_loop import IdeaLoopResult
from literature import LiteratureResult
from pipeline import run_pipeline, short_circuit_note, tractability_caution_banner, tractability_failures


def _never_called(name):
    def _fn(*args, **kwargs):
        raise AssertionError(f"{name} should not be called on this branch")
    return _fn


def test_published_short_circuits_without_downstream_calls():
    def fake_check(*args, **kwargs):
        return LiteratureResult(verdict="PUBLISHED", raw="VERDICT: PUBLISHED\nJUSTIFICATION: x\nCITATIONS:\n1. Fake Paper")

    result = run_pipeline(
        "2020.1.00001.S", "PI Test", "Target X", "desc",
        check_published_fn=fake_check,
        run_idea_loop_fn=_never_called("run_idea_loop_fn"),
        score_tractability_fn=_never_called("score_tractability_fn"),
        generate_methods_fn=_never_called("generate_methods_fn"),
        assemble_writeup_fn=_never_called("assemble_writeup_fn"),
    )
    assert result.short_circuited is True
    assert result.idea is None and result.methods is None
    assert "Already Published" in result.writeup
    assert "Fake Paper" in result.writeup
    print("[PASS] PUBLISHED verdict short-circuits with no downstream calls")


def test_unknown_short_circuits_without_downstream_calls_and_is_not_mislabeled():
    def fake_check(*args, **kwargs):
        return LiteratureResult(verdict="UNKNOWN", raw="(unparseable response)")

    result = run_pipeline(
        "2020.1.00002.S", "PI Test", "Target Y", "desc",
        check_published_fn=fake_check,
        run_idea_loop_fn=_never_called("run_idea_loop_fn"),
        score_tractability_fn=_never_called("score_tractability_fn"),
        generate_methods_fn=_never_called("generate_methods_fn"),
        assemble_writeup_fn=_never_called("assemble_writeup_fn"),
    )
    assert result.short_circuited is True
    # regression check: UNKNOWN must not be worded as if it were confirmed published
    assert "Already Published" not in result.writeup
    assert "Publication Status Unclear" in result.writeup
    print("[PASS] UNKNOWN verdict short-circuits and is worded distinctly from PUBLISHED")


def test_not_published_runs_full_pipeline_with_correct_wiring():
    calls = {}

    def fake_check(*args, **kwargs):
        return LiteratureResult(verdict="NOT_PUBLISHED", raw="VERDICT: NOT_PUBLISHED\nCITATIONS:\n(none)")

    def fake_idea_loop(data_description, *, n_iterations=4, **kwargs):
        calls["n_iterations"] = n_iterations
        return IdeaLoopResult(final_idea="THE IDEA", iterations=[{"idea": "THE IDEA", "criticism": "c"}])

    def fake_score(data_description, idea, **kwargs):
        assert idea == "THE IDEA"
        return "SCORE: 3/3 YES"

    def fake_methods(data_description, idea, **kwargs):
        assert idea == "THE IDEA"
        return "THE METHODS"

    def fake_writeup(idea, methods, literature, **kwargs):
        assert (idea, methods) == ("THE IDEA", "THE METHODS")
        assert "NOT_PUBLISHED" in literature
        return "THE WRITEUP"

    result = run_pipeline(
        "2020.1.00003.S", "PI Test", "Target Z", "desc",
        n_iterations=2,
        check_published_fn=fake_check,
        run_idea_loop_fn=fake_idea_loop,
        score_tractability_fn=fake_score,
        generate_methods_fn=fake_methods,
        assemble_writeup_fn=fake_writeup,
    )
    assert result.short_circuited is False
    assert result.idea == "THE IDEA"
    assert result.methods == "THE METHODS"
    assert result.tractability_score == "SCORE: 3/3 YES"
    assert result.writeup == "THE WRITEUP"
    assert calls["n_iterations"] == 2
    print("[PASS] NOT_PUBLISHED verdict runs full pipeline with correct data wired through")


def test_tractability_failures_ignores_no_inside_justification_text():
    score = (
        "1. YES -- no new instrumentation is required, tightly scoped\n"
        "2. YES -- stays within the described data\n"
        "3. YES -- a domain expert would agree\n"
    )
    assert tractability_failures(score) == [], (
        "a justification sentence containing the word 'no' (e.g. 'no new instrumentation') "
        "must not be misread as a failed NO verdict"
    )
    assert tractability_caution_banner(score) == ""
    print("[PASS] 'no' inside a YES justification is not misparsed as a failure")


def test_tractability_failures_detects_real_no_verdicts():
    score = (
        "1. YES -- bounded to one semester\n"
        "2. NO -- substitutes unrelated data beyond what's described\n"
        "3. NO -- a domain expert would flag the epoch mismatch\n"
    )
    failures = tractability_failures(score)
    assert len(failures) == 2
    assert failures[0].startswith("2. NO")
    assert failures[1].startswith("3. NO")
    banner = tractability_caution_banner(score)
    assert "Caution" in banner
    assert "2. NO" in banner and "3. NO" in banner
    print("[PASS] real NO verdicts are detected and included in the caution banner")


def test_not_published_pipeline_prepends_caution_banner_on_failing_score():
    def fake_check(*args, **kwargs):
        return LiteratureResult(verdict="NOT_PUBLISHED", raw="VERDICT: NOT_PUBLISHED\nCITATIONS:\n(none)")

    def fake_idea_loop(data_description, *, n_iterations=4, **kwargs):
        return IdeaLoopResult(final_idea="THE IDEA", iterations=[])

    def fake_score(data_description, idea, **kwargs):
        return "1. YES -- ok\n2. NO -- substitutes unrelated data\n3. YES -- ok\n"

    def fake_methods(data_description, idea, **kwargs):
        return "THE METHODS"

    def fake_writeup(idea, methods, literature, **kwargs):
        return "THE WRITEUP"

    result = run_pipeline(
        "code", "pi", "target", "desc",
        check_published_fn=fake_check,
        run_idea_loop_fn=fake_idea_loop,
        score_tractability_fn=fake_score,
        generate_methods_fn=fake_methods,
        assemble_writeup_fn=fake_writeup,
    )
    assert result.writeup.startswith("> **Caution")
    assert "THE WRITEUP" in result.writeup
    assert "2. NO" in result.writeup
    print("[PASS] a failing tractability score prepends a caution banner to the final writeup")


def test_not_published_pipeline_no_banner_on_passing_score():
    def fake_check(*args, **kwargs):
        return LiteratureResult(verdict="NOT_PUBLISHED", raw="VERDICT: NOT_PUBLISHED\nCITATIONS:\n(none)")

    def fake_idea_loop(data_description, *, n_iterations=4, **kwargs):
        return IdeaLoopResult(final_idea="THE IDEA", iterations=[])

    def fake_score(data_description, idea, **kwargs):
        return "1. YES -- ok\n2. YES -- ok\n3. YES -- ok\n"

    def fake_methods(data_description, idea, **kwargs):
        return "THE METHODS"

    def fake_writeup(idea, methods, literature, **kwargs):
        return "THE WRITEUP"

    result = run_pipeline(
        "code", "pi", "target", "desc",
        check_published_fn=fake_check,
        run_idea_loop_fn=fake_idea_loop,
        score_tractability_fn=fake_score,
        generate_methods_fn=fake_methods,
        assemble_writeup_fn=fake_writeup,
    )
    assert result.writeup == "THE WRITEUP", "a fully-passing score must not get a caution banner prepended"
    print("[PASS] a fully-passing tractability score leaves the writeup untouched")


def test_include_writeup_false_skips_the_writeup_call_entirely():
    # Regression test for a live failure: assemble_writeup_fn's call is the
    # single largest prompt in the chain (idea+methods+literature folded
    # together) and a caller that never reads .writeup (wizard.py's GUI flow
    # only uses .idea/.methods) was paying for and risking it for nothing.
    def fake_check(*args, **kwargs):
        return LiteratureResult(verdict="NOT_PUBLISHED", raw="VERDICT: NOT_PUBLISHED\nCITATIONS:\n(none)")

    def fake_idea_loop(data_description, *, n_iterations=4, **kwargs):
        return IdeaLoopResult(final_idea="THE IDEA", iterations=[])

    def fake_score(data_description, idea, **kwargs):
        return "1. YES -- ok\n2. YES -- ok\n3. YES -- ok\n"

    def fake_methods(data_description, idea, **kwargs):
        return "THE METHODS"

    result = run_pipeline(
        "code", "pi", "target", "desc",
        check_published_fn=fake_check,
        run_idea_loop_fn=fake_idea_loop,
        score_tractability_fn=fake_score,
        generate_methods_fn=fake_methods,
        assemble_writeup_fn=_never_called("assemble_writeup_fn"),
        include_writeup=False,
    )
    assert result.idea == "THE IDEA" and result.methods == "THE METHODS"
    assert result.writeup == ""
    print("[PASS] include_writeup=False skips assemble_writeup_fn entirely, idea/methods still returned")


def test_on_stage_complete_fires_after_each_stage_before_writeup():
    # Regression test for a live failure: 11 already-paid-for Claude calls
    # (idea loop + tractability + methods) were silently discarded because
    # nothing was persisted to disk until the whole pipeline -- including the
    # writeup call -- succeeded. This proves the checkpoint hook fires with
    # real content for literature/idea/methods, in order, before the pipeline
    # even reaches the writeup step.
    seen = []

    def fake_check(*args, **kwargs):
        return LiteratureResult(verdict="NOT_PUBLISHED", raw="VERDICT: NOT_PUBLISHED\nCITATIONS:\n(none)")

    def fake_idea_loop(data_description, *, n_iterations=4, **kwargs):
        return IdeaLoopResult(final_idea="THE IDEA", iterations=[])

    def fake_score(data_description, idea, **kwargs):
        return "1. YES -- ok\n2. YES -- ok\n3. YES -- ok\n"

    def fake_methods(data_description, idea, **kwargs):
        return "THE METHODS"

    def failing_writeup(idea, methods, literature, **kwargs):
        raise RuntimeError("simulated late-stage CLI failure")

    try:
        run_pipeline(
            "code", "pi", "target", "desc",
            check_published_fn=fake_check,
            run_idea_loop_fn=fake_idea_loop,
            score_tractability_fn=fake_score,
            generate_methods_fn=fake_methods,
            assemble_writeup_fn=failing_writeup,
            on_stage_complete=lambda stage, content: seen.append((stage, content)),
        )
        raise AssertionError("expected the simulated writeup failure to propagate")
    except RuntimeError as exc:
        assert "simulated" in str(exc)

    assert seen == [
        ("literature", "VERDICT: NOT_PUBLISHED\nCITATIONS:\n(none)"),
        ("idea", "THE IDEA"),
        ("methods", "THE METHODS"),
    ], f"expected literature/idea/methods checkpointed before the writeup failure, got {seen}"
    print("[PASS] on_stage_complete checkpoints literature/idea/methods before a writeup failure can lose them")


def test_short_circuit_note_wording_differs_by_verdict():
    published = short_circuit_note("code", "PUBLISHED", "block")
    unknown = short_circuit_note("code", "UNKNOWN", "block")
    assert "Already Published" in published
    assert "Already Published" not in unknown
    assert "block" in published and "block" in unknown
    print("[PASS] short_circuit_note wording differs between PUBLISHED and non-PUBLISHED verdicts")


def main() -> int:
    test_published_short_circuits_without_downstream_calls()
    test_unknown_short_circuits_without_downstream_calls_and_is_not_mislabeled()
    test_not_published_runs_full_pipeline_with_correct_wiring()
    test_tractability_failures_ignores_no_inside_justification_text()
    test_tractability_failures_detects_real_no_verdicts()
    test_not_published_pipeline_prepends_caution_banner_on_failing_score()
    test_not_published_pipeline_no_banner_on_passing_score()
    test_include_writeup_false_skips_the_writeup_call_entirely()
    test_on_stage_complete_fires_after_each_stage_before_writeup()
    test_short_circuit_note_wording_differs_by_verdict()
    print("\n[PASS] all Stage 9 offline checks passed, $0 cost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
