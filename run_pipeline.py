"""Stage 9 runner: single end-to-end entrypoint, no manual stage-by-stage
invocation. Always runs Stage 6 (publication check); runs Stages 5/7/8
(idea -> methods -> writeup) only if the verdict is NOT_PUBLISHED, otherwise
short-circuits to a citation-only note.

Makes real, cost-incurring `claude` CLI calls -- run deliberately.

Usage:
    python run_pipeline.py <project_dir> <project_code> <pi> <target> [n_iterations]
"""
from __future__ import annotations

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pipeline import report_pipeline_result, run_pipeline
from state import DESCRIPTION_FILE, read_state_file


def main() -> int:
    if len(sys.argv) < 5:
        print("Usage: python run_pipeline.py <project_dir> <project_code> <pi> <target> [n_iterations]")
        return 1

    project_dir, project_code, pi, target = sys.argv[1:5]
    n_iterations = int(sys.argv[5]) if len(sys.argv) > 5 else 4

    data_description = read_state_file(project_dir, DESCRIPTION_FILE)

    print(f"project_dir = {project_dir}")
    print(f"Stage 6: checking publication status for {project_code} (PI: {pi}, target: {target})...\n")

    result = run_pipeline(project_code, pi, target, data_description, n_iterations=n_iterations)
    report_pipeline_result(project_dir, result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
