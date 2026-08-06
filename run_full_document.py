"""Stage 12 runner: student plan + full paper draft, combined, against a real
project directory that already has idea.md, methods.md, and literature.md.

Makes five real, cost-incurring `claude` CLI calls (student plan, then
paper.py's title+abstract/introduction/methods/conclusions) -- run
deliberately.

Usage:
    python run_full_document.py <project_dir>
"""
from __future__ import annotations

import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from full_document import assemble_full_document
from state import (
    FULL_DOCUMENT_FILE,
    IDEA_FILE,
    LITERATURE_FILE,
    METHODS_FILE,
    read_state_file,
    write_state_file,
)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_full_document.py <project_dir>")
        return 1

    project_dir = sys.argv[1]
    idea = read_state_file(project_dir, IDEA_FILE)
    methods = read_state_file(project_dir, METHODS_FILE)
    literature = read_state_file(project_dir, LITERATURE_FILE)

    print(f"project_dir = {project_dir}")
    print("Assembling student plan + full paper draft...\n")
    document = assemble_full_document(idea, methods, literature)
    print(document)

    path = write_state_file(project_dir, FULL_DOCUMENT_FILE, document)
    word_count = len(document.split())
    print(f"\n[DONE] wrote combined document to {path} ({word_count} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
