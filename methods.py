"""Methods / work-plan generation (Stage 7).

Ported from Denario's LangGraph `methods_fast_prompt`
(denario/langgraph_agents/prompts.py, methods.py), reframed to senior-thesis
scope: describe the concrete steps a thesis student would carry out, not a
professional researcher's full workflow.
"""
from __future__ import annotations

from typing import Callable

from blocks import extract_block
from llm import call_claude


def methods_prompt(data_description: str, idea: str) -> str:
    return f"""You are provided with a data description and an idea for a senior-thesis-scoped astronomy research project. Your task is to describe the methods a thesis student would use to carry it out.

Follow these instructions:
- generate a detailed description of the methodology the student will use to perform the project.
- the description should clearly outline the concrete steps, techniques, and tools, scoped to what's achievable in one thesis timeframe (a semester to a year).
- stick to the data and tools available per the data description -- do not propose new instrumentation, additional observations, or data beyond what is described.
- if you quote a wavelength, frequency, or other measurement that the data description caveated as rest-frame vs. observed-frame, approximate, or assumed, keep that same caveat -- do not present a value the data description called uncertain as if it were a settled, verified number.
- the focus should be strictly on the methods and workflow for this specific project. Do **not** include discussion of future directions, future work, project extensions, or limitations.
- write as if a senior researcher were explaining to her thesis student exactly how to carry out the work.
- just provide the methods, do not add a sentence at the beginning about your thinking process.

Data description:
{data_description}

Idea:
{idea}

Respond in the following format:

\\begin{{METHODS}}
<METHODS>
\\end{{METHODS}}

In <METHODS> put the methods you have generated."""


def generate_methods(
    data_description: str,
    idea: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    """Generate methods.md content from a settled idea and its data description.

    `call_claude_fn` is injectable (Stage 3's repair_fn pattern) so this can be unit
    tested with zero live calls; it defaults to the real Stage 1 `call_claude`, which
    makes a live, cost-incurring CLI call.
    """
    raw = call_claude_fn(methods_prompt(data_description, idea))
    return extract_block(raw, "METHODS", repair_fn=call_claude_fn)
