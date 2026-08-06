"""Stage 5 + Stage 7 runner: idea-maker/idea-hater loop, then methods generation,
against a real project directory.

Makes real, cost-incurring `claude` CLI calls -- run deliberately.

Usage:
    python run_idea_and_methods.py <project_dir> [n_iterations]
"""
from __future__ import annotations

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from idea_loop import run_idea_loop, score_tractability
from methods import generate_methods
from state import DESCRIPTION_FILE, IDEA_FILE, METHODS_FILE, read_state_file, write_state_file


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_idea_and_methods.py <project_dir> [n_iterations]")
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

    idea_path = write_state_file(project_dir, IDEA_FILE, result.final_idea + "\n")
    print(f"\n[DONE] wrote final idea to {idea_path}")

    print("\nGenerating methods...")
    methods = generate_methods(data_description, result.final_idea)
    print(methods)

    methods_path = write_state_file(project_dir, METHODS_FILE, methods + "\n")
    print(f"\n[DONE] wrote methods to {methods_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
