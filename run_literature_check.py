"""Stage 6 runner: published/novelty check against a real project directory.

Makes one real Semantic Scholar REST call (free, no key required) and one
real, cost-incurring `claude` CLI call -- run deliberately, not part of the
free test_stage*.py suites.

Usage:
    python run_literature_check.py <project_dir> <project_code> <pi> <target>
"""
from __future__ import annotations

import sys

# See run_idea_loop.py -- Windows' console defaults to a legacy codepage that
# can't encode characters Claude's responses commonly include.
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from literature import check_published
from state import DESCRIPTION_FILE, LITERATURE_FILE, read_state_file, write_state_file


def main() -> int:
    if len(sys.argv) < 5:
        print("Usage: python run_literature_check.py <project_dir> <project_code> <pi> <target>")
        return 1

    project_dir, project_code, pi, target = sys.argv[1:5]
    data_description = read_state_file(project_dir, DESCRIPTION_FILE)

    print(f"project_dir = {project_dir}")
    print(f"Checking publication status for {project_code} (PI: {pi}, target: {target})...\n")

    result = check_published(project_code, pi, target, data_description)

    print(result.raw)
    print(f"\nParsed verdict: {result.verdict}")

    path = write_state_file(project_dir, LITERATURE_FILE, result.raw + "\n")
    print(f"\n[DONE] wrote literature check to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
