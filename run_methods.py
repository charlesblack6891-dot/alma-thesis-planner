"""Stage 7 runner: methods generation against a real project directory that
already has a settled idea.md.

Makes one real, cost-incurring `claude` CLI call -- run deliberately.

Usage:
    python run_methods.py <project_dir>
"""
from __future__ import annotations

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from methods import generate_methods
from state import DESCRIPTION_FILE, IDEA_FILE, METHODS_FILE, read_state_file, write_state_file


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_methods.py <project_dir>")
        return 1

    project_dir = sys.argv[1]
    data_description = read_state_file(project_dir, DESCRIPTION_FILE)
    idea = read_state_file(project_dir, IDEA_FILE)

    print(f"project_dir = {project_dir}")
    print("Generating methods...\n")
    methods = generate_methods(data_description, idea)
    print(methods)

    path = write_state_file(project_dir, METHODS_FILE, methods + "\n")
    print(f"\n[DONE] wrote methods to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
