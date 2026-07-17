"""Project markdown state-file primitives (Stage 3).

Plain read/write helpers for the pipeline's markdown state files, following
Denario's project-directory convention (denario/config.py): every project
directory has an `input_files/` subfolder holding `data_description.md`,
`idea.md`, `methods.md`, `literature.md`.
"""
from __future__ import annotations

from pathlib import Path

INPUT_FILES_DIRNAME = "input_files"

DESCRIPTION_FILE = "data_description.md"
IDEA_FILE = "idea.md"
METHODS_FILE = "methods.md"
LITERATURE_FILE = "literature.md"


def input_files_dir(project_dir: str | Path) -> Path:
    return Path(project_dir) / INPUT_FILES_DIRNAME


def read_state_file(project_dir: str | Path, filename: str) -> str:
    """Read one of the project's markdown state files. Raises FileNotFoundError
    with the resolved path if it doesn't exist."""
    return (input_files_dir(project_dir) / filename).read_text(encoding="utf-8")


def write_state_file(project_dir: str | Path, filename: str, content: str) -> Path:
    """Write `content` to one of the project's markdown state files, creating
    `input_files/` if needed. Returns the path written."""
    path = input_files_dir(project_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
