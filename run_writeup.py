"""Stage 8 runner: one-page writeup assembly against a real project directory
that already has idea.md, methods.md, and literature.md.

Makes one real, cost-incurring `claude` CLI call -- run deliberately.

Usage:
    python run_writeup.py <project_dir>
"""
from __future__ import annotations

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from state import (
    IDEA_FILE,
    LITERATURE_FILE,
    METHODS_FILE,
    WRITEUP_FILE,
    read_state_file,
    write_state_file,
)
from writeup import assemble_writeup


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_writeup.py <project_dir>")
        return 1

    project_dir = sys.argv[1]
    idea = read_state_file(project_dir, IDEA_FILE)
    methods = read_state_file(project_dir, METHODS_FILE)
    literature = read_state_file(project_dir, LITERATURE_FILE)

    print(f"project_dir = {project_dir}")
    print("Assembling one-page writeup...\n")
    writeup = assemble_writeup(idea, methods, literature)
    print(writeup)

    path = write_state_file(project_dir, WRITEUP_FILE, writeup + "\n")
    word_count = len(writeup.split())
    print(f"\n[DONE] wrote writeup to {path} ({word_count} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
