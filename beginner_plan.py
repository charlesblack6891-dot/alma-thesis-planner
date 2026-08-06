"""Beginner-friendly plan generation.

The idea/methods text this pipeline otherwise produces (idea_loop.py,
methods.py) is written at the level of an experienced thesis student -- it
assumes familiarity with jargon (moment maps, dense-gas tracers, aperture
photometry) and gives no sense of what doing the project would actually feel
like day to day. This module generates a separate, plain-language companion
document aimed at someone just starting out (an undergraduate new to
astrophysics, or even a strong high-school student): what the project is
for, what background it assumes, and what the first week of actually doing
it looks like.
"""
from __future__ import annotations

from typing import Callable

from blocks import extract_block
from llm import call_claude


def beginner_plan_prompt(data_description: str, idea: str, methods: str, target: str) -> str:
    return f"""You are a patient mentor explaining an astronomy research project to a complete beginner -- an undergraduate who has never done research before, or even a motivated high-school student. You are given the data description, the research idea, and the methods plan that were already generated for this project (written for an experienced thesis student). Your job is NOT to summarize those documents -- it is to translate the same project into a plan a beginner could actually follow and understand.

Write in plain, everyday language. Avoid jargon; when you must use a technical term (e.g. "moment map", "dense gas", "spectral line cube"), define it in one simple sentence the first time you use it, using an analogy if that helps. Do not assume the reader knows calculus, radio astronomy, or how to code -- explain things as if teaching someone for the first time. Do not add a sentence at the beginning about your thinking process; just write the plan.

Cover exactly these three parts, using these headings:

## 1. The Goal
In a few plain-language paragraphs, explain what this project is actually trying to find out, why it matters (in terms a beginner would find motivating, not just academically important), and what the student should have actually accomplished by the end -- be concrete about the end product (e.g. "a plot showing X", "an answer to the question of whether Y").

## 2. Skills You'll Need
List the basic skills and background knowledge this project requires, and briefly say what level is actually needed (not the deepest possible expertise, just what's needed to start). Cover at least: whether Python is needed and for what kind of tasks, what basic astrophysical concepts the student should understand (e.g. what a galaxy/protostar/molecular cloud is, what "flux" or "distance" mean in this context -- pick whatever is actually relevant to this specific project), and any other tools or math background involved. For each skill, briefly note how a beginner could pick it up if they don't already have it (e.g. a specific type of online tutorial, course, or textbook topic -- no need to name specific URLs).

## 3. Your First Week
Walk through what a typical day would look like across the first week of actually starting this project, day by day (Day 1, Day 2, etc.). Be concrete and realistic: what would the student read, install, run, or try each day; when would they likely get stuck; what's a reasonable amount of progress to expect by the end of the week. This should read like a mentor's actual advice, not a generic project-management timeline.

Data description:
{data_description}

Research idea (written for an experienced thesis student -- translate it, don't just repeat it):
{idea}

Methods plan (written for an experienced thesis student -- translate it, don't just repeat it):
{methods}

Target: {target}

Respond in the following format:

\\begin{{BEGINNERPLAN}}
<BEGINNERPLAN>
\\end{{BEGINNERPLAN}}

In <BEGINNERPLAN> put the beginner-friendly plan you have written, using the three headings above."""


def generate_beginner_plan(
    data_description: str,
    idea: str,
    methods: str,
    target: str,
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> str:
    """Generate a plain-language companion plan (goal, prerequisite skills,
    first-week walkthrough) from an already-settled idea and methods plan.

    `call_claude_fn` is injectable (Stage 3's repair_fn pattern) so this can be unit
    tested with zero live calls; it defaults to the real Stage 1 `call_claude`, which
    makes a live, cost-incurring CLI call.
    """
    raw = call_claude_fn(beginner_plan_prompt(data_description, idea, methods, target))
    return extract_block(raw, "BEGINNERPLAN", repair_fn=call_claude_fn)
