"""Stage 11 runner: full paper-draft assembly against a real project directory
that already has idea.md, methods.md, and literature.md.

Makes four real, cost-incurring `claude` CLI calls (title+abstract,
introduction, methods, conclusions) -- run deliberately. See paper.py's
module docstring for why the Results section is a fixed placeholder instead
of a fifth call.

Usage:
    python run_paper.py <project_dir>
"""
from __future__ import annotations

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from paper import assemble_paper
from state import (
    IDEA_FILE,
    LITERATURE_FILE,
    METHODS_FILE,
    PAPER_FILE,
    read_state_file,
    write_state_file,
)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_paper.py <project_dir>")
        return 1

    project_dir = sys.argv[1]
    idea = read_state_file(project_dir, IDEA_FILE)
    methods = read_state_file(project_dir, METHODS_FILE)
    literature = read_state_file(project_dir, LITERATURE_FILE)

    print(f"project_dir = {project_dir}")
    print("Assembling full paper draft (title+abstract, introduction, methods, conclusions)...\n")
    paper = assemble_paper(idea, methods, literature)
    print(paper)

    path = write_state_file(project_dir, PAPER_FILE, paper)
    word_count = len(paper.split())
    print(f"\n[DONE] wrote paper draft to {path} ({word_count} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
