"""Stage 10 offline unit tests (topic_lookup.py) -- zero live network/`claude` calls.

Follows Stage 3/5/6's dependency-injection pattern: the Claude call is
injectable, so topic-matching and candidate filtering can be verified for
free and deterministically. Builds a throwaway fake source repo on disk
(queue.csv + projects/<code>/) rather than pointing at the real sibling
checkout, so these tests don't depend on it existing.
"""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from topic_lookup import (
    Candidate,
    available_categories_and_keywords,
    filter_by_category_keyword,
    list_candidates,
    load_project_data,
    pick_project,
    pick_project_prompt,
)


def _write_queue(repo: Path, rows: list[dict]) -> None:
    fieldnames = ["project_code", "status", "verdict", "title", "note", "source", "added_at", "updated_at"]
    with (repo / "queue.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{k: "" for k in fieldnames}, **row})


def _write_project(repo: Path, code: str, *, title: str, pi: str, targets: list[str], description: str) -> None:
    project_dir = repo / "projects" / code
    (project_dir / "input_files").mkdir(parents=True, exist_ok=True)
    (project_dir / "input_files" / "data_description.md").write_text(description, encoding="utf-8")
    metadata = {
        "project_code": code,
        "title": title,
        "pi_name": pi,
        "mous_records": [{"target_name": t} for t in targets],
    }
    (project_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")


def test_list_candidates_filters_to_ingested_unpublished_only():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _write_queue(
            repo,
            [
                {"project_code": "A.001", "status": "done", "verdict": "unpublished", "title": "Outflows in X"},
                {"project_code": "B.002", "status": "done", "verdict": "published", "title": "Already published"},
                {"project_code": "C.003", "status": "pending", "verdict": "", "title": "Not yet ingested"},
                {"project_code": "D.004", "status": "done", "verdict": "unpublished", "title": "Missing on disk"},
            ],
        )
        # Only A.001 gets real ingest files on disk; D.004's queue row claims
        # done/unpublished but has no projects/D.004/ dir, so it must be excluded.
        _write_project(repo, "A.001", title="Outflows in X", pi="PI A", targets=["Target A"], description="desc A")

        candidates = list_candidates(repo)

        codes = [c.project_code for c in candidates]
        assert codes == ["A.001"], f"expected only A.001, got {codes}"
        print("[PASS] list_candidates filters to done+unpublished+ingested")


def test_list_candidates_publication_filter_published():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _write_queue(
            repo,
            [
                {"project_code": "A.001", "status": "done", "verdict": "unpublished", "title": "Outflows in X"},
                {"project_code": "B.002", "status": "published", "verdict": "published", "title": "Already published"},
                {"project_code": "C.003", "status": "done", "verdict": "partially published", "title": "Half published"},
            ],
        )
        for code, title in [("A.001", "Outflows in X"), ("B.002", "Already published"), ("C.003", "Half published")]:
            _write_project(repo, code, title=title, pi="PI", targets=["Target"], description="desc")

        codes = sorted(c.project_code for c in list_candidates(repo, "published"))
        assert codes == ["B.002", "C.003"], f"expected B.002 and C.003 only, got {codes}"
        print("[PASS] list_candidates('published') includes published + partially published, excludes unpublished")


def test_list_candidates_publication_filter_both():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _write_queue(
            repo,
            [
                {"project_code": "A.001", "status": "done", "verdict": "unpublished", "title": "Outflows in X"},
                {"project_code": "B.002", "status": "published", "verdict": "published", "title": "Already published"},
                {"project_code": "C.003", "status": "pending", "verdict": "", "title": "Not yet ingested"},
            ],
        )
        for code, title in [("A.001", "Outflows in X"), ("B.002", "Already published")]:
            _write_project(repo, code, title=title, pi="PI", targets=["Target"], description="desc")

        codes = sorted(c.project_code for c in list_candidates(repo, "both"))
        assert codes == ["A.001", "B.002"], f"expected both done rows regardless of verdict, got {codes}"
        print("[PASS] list_candidates('both') includes every fully-checked, ingested verdict")


def test_list_candidates_unknown_publication_filter_raises():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _write_queue(repo, [{"project_code": "A.001", "status": "done", "verdict": "unpublished", "title": "X"}])
        try:
            list_candidates(repo, "bogus")
            raise AssertionError("expected ValueError for an unknown publication_filter")
        except ValueError as exc:
            assert "bogus" in str(exc)
            print("[PASS] list_candidates rejects an unknown publication_filter")


def test_list_candidates_missing_queue_raises():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            list_candidates(Path(tmp))
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError:
            print("[PASS] missing queue.csv raises FileNotFoundError")


def test_load_project_data_dedupes_targets_and_reads_description():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _write_project(
            repo, "A.001", title="Outflows in X", pi="PI A",
            targets=["Target A", "Target A", "Target B"], description="the description text",
        )

        data = load_project_data(repo, "A.001")

        assert data["pi"] == "PI A"
        assert data["target"] == "Target A, Target B", f"expected deduped targets, got {data['target']!r}"
        assert data["data_description"] == "the description text"
        print("[PASS] load_project_data dedupes targets and reads description")


def test_pick_project_prompt_lists_all_candidates():
    candidates = [Candidate(project_code="A.001", title="Outflows in X"), Candidate(project_code="B.002", title="Disks in Y")]
    prompt = pick_project_prompt("I like protostellar outflows", candidates)
    assert "A.001: Outflows in X" in prompt
    assert "B.002: Disks in Y" in prompt
    assert "protostellar outflows" in prompt
    print("[PASS] pick_project_prompt lists all candidates and embeds the topic")


def test_pick_project_prompt_includes_keywords_categories_and_abstract():
    candidates = [Candidate(
        project_code="A.001", title="Shock Tracers in Z",
        scientific_categories=["Active galaxies"],
        science_keywords=["Merging and interacting galaxies", "Starbursts, star formation"],
        proposal_abstract="A" * 500,  # longer than the excerpt cap
    )]
    prompt = pick_project_prompt("anything", candidates)
    assert "Scientific categories: Active galaxies" in prompt
    assert "Science keywords: Merging and interacting galaxies, Starbursts, star formation" in prompt
    assert "A" * 350 in prompt and "A" * 351 not in prompt, "abstract excerpt should be capped, not the full text"
    assert "not merely the least-unrelated option" in prompt, "prompt should demand a genuine match, not a forced pick"
    print("[PASS] pick_project_prompt surfaces science keywords/categories/abstract excerpt for real matching signal")


def test_pick_project_returns_matching_candidate():
    candidates = [Candidate(project_code="A.001", title="Outflows in X"), Candidate(project_code="B.002", title="Disks in Y")]

    def fake_claude(prompt):
        assert "Outflows in X" in prompt
        return "\\begin{PICK}\nPROJECT_CODE: A.001\nMATCH_QUALITY: GOOD\nREASON: Direct topical match.\n\\end{PICK}"

    pick = pick_project("outflow-y things", candidates, call_claude_fn=fake_claude)
    assert pick.candidate.project_code == "A.001"
    assert pick.match_quality == "GOOD"
    assert "Direct topical match." in pick.reason
    print("[PASS] pick_project resolves Claude's PICK block to the matching candidate")


def test_pick_project_rejects_unknown_code():
    candidates = [Candidate(project_code="A.001", title="Outflows in X")]

    def fake_claude(prompt):
        return "\\begin{PICK}\nPROJECT_CODE: Z.999\nMATCH_QUALITY: GOOD\nREASON: n/a\n\\end{PICK}"

    try:
        pick_project("anything", candidates, call_claude_fn=fake_claude)
        raise AssertionError("expected ValueError for an out-of-list pick")
    except ValueError as exc:
        assert "Z.999" in str(exc)
        print("[PASS] pick_project rejects a code not in the candidate list")


def test_pick_project_empty_candidates_raises():
    try:
        pick_project("anything", [], call_claude_fn=lambda p: "unused")
        raise AssertionError("expected ValueError for empty candidate list")
    except ValueError:
        print("[PASS] pick_project raises on empty candidate list")


def test_available_categories_and_keywords_groups_by_category():
    candidates = [
        Candidate(project_code="A.001", title="X", scientific_categories=["Active galaxies"],
                  science_keywords=["Starbursts, star formation"]),
        Candidate(project_code="B.002", title="Y", scientific_categories=["Active galaxies"],
                  science_keywords=["AGN"]),
        Candidate(project_code="C.003", title="Z", scientific_categories=["Stars and stellar evolution"],
                  science_keywords=["Supernovae"]),
    ]
    categories, keywords_by_category = available_categories_and_keywords(candidates)
    assert categories == ["Active galaxies", "Stars and stellar evolution"]
    assert keywords_by_category["Active galaxies"] == ["AGN", "Starbursts, star formation"]
    assert keywords_by_category["Stars and stellar evolution"] == ["Supernovae"]
    print("[PASS] available_categories_and_keywords groups keywords under their real co-occurring category")


def test_filter_by_category_keyword_returns_matching_only():
    candidates = [
        Candidate(project_code="A.001", title="X", scientific_categories=["Active galaxies"],
                  science_keywords=["AGN"]),
        Candidate(project_code="B.002", title="Y", scientific_categories=["Stars and stellar evolution"],
                  science_keywords=["Supernovae"]),
        # shares the keyword but not the category -- must not match either filter
        Candidate(project_code="C.003", title="Z", scientific_categories=["ISM and star formation"],
                  science_keywords=["AGN"]),
    ]
    matches = filter_by_category_keyword(candidates, "Active galaxies", "AGN")
    assert [c.project_code for c in matches] == ["A.001"]
    print("[PASS] filter_by_category_keyword requires both the category and the keyword on the same candidate")


def test_pick_project_rejects_none_genuine_match():
    # Regression test for a real live miss: "super luminous supernovae" was
    # matched to an unrelated protostellar-outflow survey because the local
    # pool had no supernova candidate and the old prompt forced a pick
    # regardless. A NONE match_quality must raise, not silently return the
    # least-bad candidate.
    candidates = [Candidate(project_code="A.001", title="Protostellar Outflow Survey")]

    def fake_claude(prompt):
        return (
            "\\begin{PICK}\nPROJECT_CODE: NONE\nMATCH_QUALITY: NONE\n"
            "REASON: The student asked about supernovae; the only candidate is about protostellar "
            "outflows, an unrelated phenomenon.\n\\end{PICK}"
        )

    try:
        pick_project("I want to study super luminous supernovae", candidates, call_claude_fn=fake_claude)
        raise AssertionError("expected ValueError when no candidate is a genuine match")
    except ValueError as exc:
        assert "supernovae" in str(exc), "error should quote the topic that had no match"
        assert "manual mode" in str(exc), "error should point the user at the fallback"
        print("[PASS] pick_project raises rather than force-picking an unrelated candidate")


def main() -> int:
    test_list_candidates_filters_to_ingested_unpublished_only()
    test_list_candidates_publication_filter_published()
    test_list_candidates_publication_filter_both()
    test_list_candidates_unknown_publication_filter_raises()
    test_list_candidates_missing_queue_raises()
    test_load_project_data_dedupes_targets_and_reads_description()
    test_pick_project_prompt_lists_all_candidates()
    test_pick_project_prompt_includes_keywords_categories_and_abstract()
    test_pick_project_returns_matching_candidate()
    test_pick_project_rejects_unknown_code()
    test_pick_project_empty_candidates_raises()
    test_available_categories_and_keywords_groups_by_category()
    test_filter_by_category_keyword_returns_matching_only()
    test_pick_project_rejects_none_genuine_match()
    print("\n[PASS] all Stage 10 offline checks passed, $0 cost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
