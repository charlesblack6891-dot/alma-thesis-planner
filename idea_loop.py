"""Idea-maker / idea-hater loop (Stage 5).

Ported from Denario's LangGraph idea_maker/idea_hater prompts
(denario/langgraph_agents/idea.py, prompts.py), reframed to senior-thesis
scope, and replacing LangGraph's router with a plain Python loop driving
Claude via the Stage 1 `call_claude` primitive -- no LangChain, no API keys.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from blocks import extract_block
from llm import call_claude


def idea_maker_prompt(data_description: str, previous_ideas: str, criticism: str, iteration: int) -> str:
    return f"""Your goal is to propose a senior-thesis-scoped astronomy research project idea based on the data description below. If criticism from a previous round is provided, revise the idea to address it. Stick to the guidelines in the data description.

The idea must be:
- completable by one student in one thesis timeframe (a semester to a year), not a full research paper's worth of work
- achievable using only the data and tools described below -- do not propose new instrumentation, additional observations, or data beyond what is described
- something a domain expert would call tractable, not merely novel or ambitious

Substitute-data rule: if the description says this project's own dataset is not yet usable (proprietary, unreleased, or not yet observed/calibrated) and separately mentions other, already-public data on the same target as background context, you may only build the idea around that alternative data if you can state, in the idea itself, a specific reason it addresses the same kind of scientific question the assigned project's own data was for -- not merely that it happens to be public and about the same target. "It's public and about the same star/galaxy/field" is not by itself a valid justification. Only use external datasets, papers, or catalogs that are explicitly named in the data description above -- do not introduce a specific external dataset from your own general knowledge just because you happen to know it exists and seems relevant; if the description doesn't name it, treat it as unavailable to you, the same as if it didn't exist. If no genuine, description-named substitute exists, say so plainly and propose an idea honestly scoped around what the available public information actually supports instead -- e.g. a literature-based reanalysis, or a methods proposal contingent on the assigned data's eventual release -- rather than reaching for an unnamed dataset to make the idea seem more complete.

Frequency/measurement provenance rule: if the data description quotes a wavelength, frequency, or other numeric measurement -- especially one already labeled there as rest-frame vs. observed-frame, or as approximate/assumed -- and you repeat that number in the idea, you must preserve that same framing (e.g. "SiO(5-4), observed frequency ~216.06 GHz assuming z~0.00537; verify against Splatalogue before imaging," not a bare "SiO(5-4) ~216.06 GHz"). Do not compress a caveated number into one that reads as a certain, rest-frame, or already-verified value -- that misrepresents the data description's own stated uncertainty. If the data description doesn't say whether a value is rest-frame or observed-frame, say so explicitly rather than presenting it as either.

Iteration {iteration}

Data description:
{data_description}

Previous ideas:
{previous_ideas or "(none yet)"}

Criticism:
{criticism or "(none yet)"}

Respond in the following format:

\\begin{{IDEA}}
<IDEA>
\\end{{IDEA}}

In <IDEA>, put the idea together with a brief description. Do not explain how you addressed the criticism."""


def idea_hater_prompt(data_description: str, previous_ideas: str, idea: str) -> str:
    return f"""Your goal is to critique a proposed senior-thesis astronomy project idea. You are given the idea and the data description it's based on. Be a harsh critic, but weigh feasibility and tractability within a single thesis timeframe above novelty or ambition -- an idea that is impactful but requires more time, data, or expertise than a thesis student has is a bad idea, even if a research-paper reviewer would like it. Take into account:
- is the scope bounded to what's completable in one thesis timeframe?
- does it avoid requiring new instrumentation or data beyond what's in the data description?
- would a domain expert call it tractable, not just novel?
- if the idea uses different/alternative data than the project's own assigned dataset (e.g. because the assigned dataset is proprietary or not yet available), does the idea explicitly justify why that alternative data addresses the same scientific question the assigned dataset was for -- or has it just swapped in unrelated public data on the same target without a real justification? Reject the latter explicitly and name it as the problem, not as a vague scope concern.
- is every specific external dataset, paper, or catalog the idea relies on actually named in the data description itself? If the idea introduces a specific external dataset/catalog (e.g. a named survey, a named paper's tabulated values) that is NOT mentioned anywhere in the data description, reject this explicitly by name -- this is a separate, more concrete failure than general "beyond what's described" vagueness, and iterating toward a *different* unnamed substitute is not a fix.
- if the idea quotes a wavelength/frequency/other measurement that the data description caveated as rest-frame vs. observed-frame, approximate, or assumed, did the idea drop that caveat and present the number as certain? Reject this explicitly and name the specific value -- a number that was uncertain in the source material must stay uncertain in the idea.

If the idea is not feasible at thesis scope, say so plainly and suggest a new idea instead of a minor tweak. Take into account any guidelines in the data description.

Data description:
{data_description}

Previous ideas:
{previous_ideas or "(none yet)"}

Current idea:
{idea}

Respond in the following format:

\\begin{{CRITIC}}
<CRITIC>
\\end{{CRITIC}}

In <CRITIC>, put your criticism. Try to be brief."""


def tractability_prompt(data_description: str, idea: str) -> str:
    return f"""You are reviewing a proposed senior-thesis astronomy project idea for tractability. Answer these three questions plainly, each with YES or NO and one sentence of justification:

1. Is the task bounded to something completable in one thesis timeframe (a semester to a year)?
2. Does it avoid requiring new instrumentation or data beyond what's in the data description?
3. Would a domain expert plausibly agree it's tractable, not just novel or impactful?

Data description:
{data_description}

Idea:
{idea}

Respond in the following format:

\\begin{{SCORE}}
1. YES/NO -- <justification>
2. YES/NO -- <justification>
3. YES/NO -- <justification>
\\end{{SCORE}}"""


@dataclass
class IdeaLoopResult:
    final_idea: str
    iterations: list[dict]  # [{"idea": str, "criticism": str}, ...] for iteration-to-iteration diffing


def run_idea_loop(
    data_description: str,
    *,
    n_iterations: int = 4,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> IdeaLoopResult:
    """Run N maker<->hater iterations, settling on one final thesis-scoped idea.

    `call_claude_fn` is injectable (Stage 3's repair_fn pattern) so this can be unit
    tested with zero live calls; it defaults to the real Stage 1 `call_claude`, which
    makes live, cost-incurring CLI calls.
    """
    previous_ideas = ""
    criticism = ""
    idea = ""
    history: list[dict] = []

    for i in range(1, n_iterations + 1):
        maker_raw = call_claude_fn(idea_maker_prompt(data_description, previous_ideas, criticism, i))
        idea = extract_block(maker_raw, "IDEA", repair_fn=call_claude_fn)

        hater_raw = call_claude_fn(idea_hater_prompt(data_description, previous_ideas, idea))
        criticism = extract_block(hater_raw, "CRITIC", repair_fn=call_claude_fn)

        history.append({"idea": idea, "criticism": criticism})
        previous_ideas += f"\n\nIteration {i}:\nIdea: {idea}\n"

    return IdeaLoopResult(final_idea=idea, iterations=history)


def score_tractability(
    data_description: str,
    idea: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    """Score a settled idea against the 3-question tractability rubric.

    PLAN.md Stage 5: 'early scope check, do not defer to batch calibration' --
    run this right after the loop settles, not deferred to later batch work.
    """
    raw = call_claude_fn(tractability_prompt(data_description, idea))
    return extract_block(raw, "SCORE", repair_fn=call_claude_fn)
