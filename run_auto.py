"""Stage 10 runner: topic-only entrypoint -- no project code, PI, or target needed.

Give it a sentence or two describing a research interest; it picks a
matching already-vetted-unpublished ALMA project from the sibling
alma_thesis_planning checkout's queue (see topic_lookup.py) and hands it
straight to the existing Stage 9 pipeline (literature -> idea -> methods ->
writeup), exactly as if those had been typed in by hand for run_pipeline.py.

Makes real, cost-incurring `claude` CLI calls -- run deliberately.

Usage:
    python run_auto.py ["<topic sentence or two>"] [n_iterations]

If <topic> is omitted, prompts for it interactively. Set $ALMA_QUEUE_REPO to
point at a different alma_thesis_planning checkout than the default sibling
directory.
"""
from __future__ import annotations

import re
import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pipeline import report_pipeline_result, run_pipeline
from state import DESCRIPTION_FILE, write_state_file
from topic_lookup import default_source_repo, list_candidates, load_project_data, pick_project


def slugify(project_code: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", project_code.lower()).strip("_")


def main() -> int:
    args = sys.argv[1:]
    n_iterations = 4
    if args and args[-1].isdigit():
        n_iterations = int(args[-1])
        args = args[:-1]

    topic = " ".join(args).strip()
    if not topic:
        topic = input("Describe the kind of project you're interested in (a sentence or two): ").strip()
    if not topic:
        print("No topic given.")
        return 1

    source_repo = default_source_repo()
    print(f"Looking for unpublished candidates in {source_repo}...")
    candidates = list_candidates(source_repo)
    print(f"{len(candidates)} already-vetted unpublished candidates available.\n")

    print("Matching topic against candidates...")
    pick = pick_project(topic, candidates)
    print(f"Picked {pick.candidate.project_code}: {pick.candidate.title}")
    print(f"Match quality: {pick.match_quality} -- {pick.reason}\n")

    project = load_project_data(source_repo, pick.candidate.project_code)
    project_dir = f"project_{slugify(pick.candidate.project_code)}_auto"
    write_state_file(project_dir, DESCRIPTION_FILE, project["data_description"])

    print(f"project_dir = {project_dir}")
    print(
        f"Stage 6: checking publication status for {project['project_code']} "
        f"(PI: {project['pi']}, target: {project['target']})...\n"
    )

    result = run_pipeline(
        project["project_code"],
        project["pi"],
        project["target"],
        project["data_description"],
        n_iterations=n_iterations,
    )
    report_pipeline_result(project_dir, result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
