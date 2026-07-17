"""Output-parsing primitive (Stage 3): pull a \\begin{TAG}...\\end{TAG} block out
of raw Claude text, with a repair fallback for malformed output.

Ported from Denario's `extract_latex_block`/`fixer` pair
(denario/paper_agents/tools.py): on a failed match, ask Claude to reformat the
text into a well-formed block and retry once, rather than crashing outright.
"""
from __future__ import annotations

import re
from typing import Callable

from llm import call_claude


class BlockExtractionError(RuntimeError):
    """Raised when a \\begin{TAG}...\\end{TAG} block can't be extracted, even after repair."""


def _pattern(tag: str) -> re.Pattern[str]:
    return re.compile(rf"\\begin{{{re.escape(tag)}}}(.*?)\\end{{{re.escape(tag)}}}", re.DOTALL)


def extract_block(
    text: str,
    tag: str,
    *,
    repair: bool = True,
    repair_fn: Callable[[str], str] = call_claude,
) -> str:
    r"""Extract TEXT from \begin{tag}TEXT\end{tag} in `text`.

    If no well-formed block is found and `repair` is True, calls `repair_fn`
    (a prompt -> text function, `call_claude` by default) once, asking it to
    reformat `text` into a well-formed block, and retries the match against
    its output. Raises BlockExtractionError if that also fails, or if
    `repair` is False.
    """
    match = _pattern(tag).search(text)
    if match:
        return match.group(1).strip()

    if not repair:
        raise BlockExtractionError(f"no \\begin{{{tag}}}...\\end{{{tag}}} block found")

    fixed = repair_fn(
        f"The following text was supposed to contain a block wrapped in "
        f"\\begin{{{tag}}} ... \\end{{{tag}}}, but the tags are missing or malformed. "
        f"Reformat it to wrap the relevant content in exactly those tags, changing "
        f"nothing else about the content. Reply with ONLY the reformatted text, "
        f"no preamble, no code fences.\n\n---\n{text}\n---"
    )
    match = _pattern(tag).search(fixed)
    if match:
        return match.group(1).strip()

    raise BlockExtractionError(
        f"no \\begin{{{tag}}}...\\end{{{tag}}} block found, even after repair attempt"
    )
