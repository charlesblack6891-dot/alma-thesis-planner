"""Stage 5 runner: idea-maker/idea-hater loop against a real project directory.

Makes real, cost-incurring `claude` CLI calls (n_iterations * 2, plus one for
the tractability score) -- run deliberately, not part of the free
test_stage*.py suites.

Usage:
    python run_idea_loop.py <project_dir> [n_iterations]
"""
from __future__ import annotations

import sys

# Windows' console defaults to a legacy codepage (e.g. cp1252) that can't encode
# characters Claude's responses commonly include (arcsec marks, en-dashes, degree
# signs). Force UTF-8 so printing the raw response text doesn't crash mid-run.
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from idea_loop import run_idea_loop, score_tractability
from state import DESCRIPTION_FILE, IDEA_FILE, read_state_file, write_state_file


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_idea_loop.py <project_dir> [n_iterations]")
        return 1

    project_dir = sys.argv[1]
    n_iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    data_description = read_state_file(project_dir, DESCRIPTION_FILE)

    print(f"project_dir = {project_dir}")
    print(f"Running idea loop ({n_iterations} iterations)...\n")
    result = run_idea_loop(data_description, n_iterations=n_iterations)

    for i, step in enumerate(result.iterations, 1):
        print(f"--- Iteration {i} ---")
        print("IDEA:\n" + step["idea"])
        print("\nCRITIC:\n" + step["criticism"])
        print()

    print("=== Final idea ===")
    print(result.final_idea)

    print("\nScoring final idea for tractability...")
    score = score_tractability(data_description, result.final_idea)
    print(score)

    path = write_state_file(project_dir, IDEA_FILE, result.final_idea + "\n")
    print(f"\n[DONE] wrote final idea to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
