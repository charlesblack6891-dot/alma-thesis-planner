"""One-page writeup assembly (Stage 8).

No direct Denario prompt to port here -- Denario writes a full paper, not a
one-pager -- so this prompt is original, designed directly from
PROJECT_BRIEF.md's spec: an abstract, a description of work to be carried
out with anticipated key results/plots, and a background-reading list,
combined into one coherent ~1-page document (not three stapled fragments).
"""
from __future__ import annotations

from typing import Callable

from blocks import extract_block
from llm import call_claude


def writeup_prompt(idea: str, methods: str, literature: str) -> str:
    return f"""You are assembling a senior-thesis project proposal from three pieces of already-generated content: a settled project idea, a methods/work plan, and a background-reading list. Combine them into a single coherent one-page document -- not three stapled-together fragments.

The final document must have exactly these three sections, in this order:
1. **Abstract** -- a tight paragraph (condensed from the idea below) stating the scientific question and the bounded thesis-scoped approach.
2. **Work Plan** -- a condensed description of work to be carried out (condensed from the methods below), including the anticipated key results/plots the student should expect to produce along the way. Preserve the concrete steps and tools named below; cut narrative padding, not substance.
3. **Background Reading** -- the citation list (from the literature below), as a short bulleted list.

Constraints:
- The whole document should read as roughly one page (guideline: under 700 words total).
- Do not invent new content, numbers, or citations beyond what's given below.
- Do not add commentary about the assembly process itself.

Idea:
{idea}

Methods:
{methods}

Literature:
{literature}

Respond in the following format:

\\begin{{WRITEUP}}
<WRITEUP>
\\end{{WRITEUP}}

In <WRITEUP> put the assembled one-page document, in markdown, starting with a title line."""


def assemble_writeup(
    idea: str,
    methods: str,
    literature: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    """Assemble idea.md + methods.md + literature.md into the one-page deliverable.

    `call_claude_fn` is injectable (Stage 3/5/7's pattern) so this can be unit
    tested with zero live calls; it defaults to the real Stage 1 `call_claude`,
    which makes a live, cost-incurring CLI call.
    """
    raw = call_claude_fn(writeup_prompt(idea, methods, literature))
    return extract_block(raw, "WRITEUP", repair_fn=call_claude_fn)
