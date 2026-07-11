"""Stage 2 stress test: find out how the claude CLI behaves under repeated and
adversarial conditions before anything is built on top of it.

Run directly (no pytest dependency needed):
    python test_stage2.py

This is a validation log, not a strict pass/fail suite -- several checks are
observational (web search triggering, model routing) and print raw JSON for
manual interpretation rather than asserting one "correct" answer.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time

from llm import ClaudeCLIError, _invoke

REALISTIC_PROMPT = (
    "You are helping plan a senior thesis project based on this ALMA dataset:\n\n"
    "Project code: 2019.1.01234.S\n"
    "PI: J. Smith\n"
    "Target: NGC 1365\n"
    "Band: 6 (211-275 GHz)\n"
    "Observation date: 2019-11-02\n"
    "Array config: C43-4, 45 antennas\n"
    "Proposal abstract: We propose ALMA Band 6 observations of the circumnuclear disk "
    "in NGC 1365 to trace molecular gas inflow onto the central AGN via CO(2-1) and "
    "dense-gas tracers (HCN, HCO+), testing whether gas transport is driven by the "
    "large-scale stellar bar or by nuclear-scale instabilities.\n"
    "Data products: calibrated visibilities, CO(2-1) cube, HCN(1-0) cube, continuum map.\n\n"
    "In 3-4 sentences, suggest one concrete senior-thesis-scoped analysis a student "
    "could do with this dataset."
)


def _summarize_latencies(samples: list[float]) -> str:
    sorted_samples = sorted(samples)
    p50 = statistics.median(sorted_samples)
    p95_index = min(len(sorted_samples) - 1, int(round(0.95 * (len(sorted_samples) - 1))))
    p95 = sorted_samples[p95_index]
    return f"P50={p50:.2f}s P95={p95:.2f}s min={sorted_samples[0]:.2f}s max={sorted_samples[-1]:.2f}s"


def check_repeated_calls(n: int = 10) -> None:
    print(f"\n--- Check 1: {n} back-to-back calls ---")
    wall_clocks = []
    costs = []
    failures = 0
    for i in range(1, n + 1):
        try:
            result = _invoke("Reply with exactly the single word: PONG")
            text = result.text.strip()
            ok = text == "PONG"
            wall_clocks.append(result.wall_clock_s)
            costs.append(result.cost_usd or 0.0)
            status = "PASS" if ok else "FAIL (unexpected text)"
            print(f"  [{status}] call {i}/{n}: {text!r} wall_clock={result.wall_clock_s:.2f}s")
            if not ok:
                failures += 1
        except ClaudeCLIError as exc:
            failures += 1
            print(f"  [FAIL] call {i}/{n}: {exc}")
    if wall_clocks:
        print(f"  Latency: {_summarize_latencies(wall_clocks)}")
        print(f"  Total cost: ${sum(costs):.4f} across {len(costs)} calls")
    print(f"  {n - failures}/{n} calls succeeded with exact PONG match")


def check_growing_context_loop(n: int = 4) -> None:
    print(f"\n--- Check 2: simulated growing-context loop ({n} iterations) ---")
    previous_ideas: list[str] = []
    wall_clocks = []
    costs = []
    for i in range(1, n + 1):
        context = "\n".join(f"- Idea {j+1}: {idea}" for j, idea in enumerate(previous_ideas))
        prompt = (
            "Given this ALMA dataset (NGC 1365, Band 6, CO(2-1)/HCN/HCO+ observations of "
            "circumnuclear gas inflow), and these previously proposed thesis ideas:\n"
            f"{context if context else '(none yet)'}\n\n"
            "Propose ONE new, different senior-thesis-scoped idea in exactly one sentence, "
            "wrapped in \\begin{IDEA}...\\end{IDEA}."
        )
        try:
            result = _invoke(prompt)
            wall_clocks.append(result.wall_clock_s)
            costs.append(result.cost_usd or 0.0)
            previous_ideas.append(result.text.strip())
            print(
                f"  iter {i}/{n}: prompt_len={len(prompt)} chars, "
                f"wall_clock={result.wall_clock_s:.2f}s, cost=${result.cost_usd:.4f}, "
                f"duration_ms={result.duration_ms}"
            )
        except ClaudeCLIError as exc:
            print(f"  [FAIL] iter {i}/{n}: {exc}")
            break
    if len(wall_clocks) >= 2:
        growth = wall_clocks[-1] - wall_clocks[0]
        print(f"  Wall-clock delta from iter 1 to iter {len(wall_clocks)}: {growth:+.2f}s")
        cost_growth = costs[-1] - costs[0]
        print(f"  Cost delta from iter 1 to iter {len(costs)}: {cost_growth:+.4f} USD")


def check_json_output() -> None:
    print("\n--- Check 3: raw-JSON-format response prompt ---")
    prompt = (
        "Reply with ONLY a raw JSON object (no markdown code fences, no prose before or "
        "after) with exactly this shape: "
        '{"verdict": "PUBLISHED" or "NOT_PUBLISHED", "citations": [list of strings]}. '
        "For this response, use verdict NOT_PUBLISHED and citations as an empty list."
    )
    try:
        result = _invoke(prompt)
        print(f"  raw text: {result.text!r}")
        try:
            parsed = json.loads(result.text.strip())
            print(f"  [PASS] parsed cleanly: {parsed}")
        except json.JSONDecodeError as exc:
            print(f"  [INFO] did not parse as raw JSON ({exc}); fallback-repair path needed")
    except ClaudeCLIError as exc:
        print(f"  [FAIL] {exc}")


def check_messy_output() -> None:
    print("\n--- Check 4: loosely-worded prompt (preamble risk) ---")
    prompt = (
        "Can you help me come up with a senior thesis idea for an ALMA dataset of "
        "NGC 1365? Please format your final answer inside \\begin{IDEA}...\\end{IDEA} tags."
    )
    try:
        result = _invoke(prompt)
        text = result.text
        has_tags = "\\begin{IDEA}" in text and "\\end{IDEA}" in text
        before = text.split("\\begin{IDEA}")[0].strip() if has_tags else text
        print(f"  has_tags={has_tags}")
        print(f"  text before opening tag ({len(before)} chars): {before!r}")
        print(f"  full text: {text!r}")
    except ClaudeCLIError as exc:
        print(f"  [FAIL] {exc}")


def check_timeout_kills_tree() -> None:
    print("\n--- Check 5: hard timeout enforcement ---")
    start = time.monotonic()
    try:
        _invoke("Reply with exactly the single word: PONG", timeout=2)
        print("  [FAIL] expected a timeout, call completed instead")
    except ClaudeCLIError as exc:
        elapsed = time.monotonic() - start
        print(f"  [PASS] timed out and raised cleanly after {elapsed:.2f}s: {exc}")

    time.sleep(2)
    for image in ("claude.exe", "node.exe"):
        proc = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image}"],
            capture_output=True,
            text=True,
        )
        lines = [l for l in proc.stdout.splitlines() if image in l]
        print(f"  post-timeout {image} processes still running: {len(lines)}")
        for l in lines:
            print(f"    {l}")


def check_tool_tempting_prompt() -> None:
    print("\n--- Check 6: prompt that might tempt file/tool use ---")
    prompt = (
        "Please read the file named secret_notes.txt in the current directory and "
        "tell me what it says. If you can't access it, just say so in one sentence."
    )
    try:
        result = _invoke(prompt)
        print(f"  text: {result.text!r}")
        print(f"  raw num_turns={result.raw.get('num_turns')}, "
              f"tool-related keys present: "
              f"{[k for k in result.raw if 'tool' in k.lower()]}")
    except ClaudeCLIError as exc:
        print(f"  [FAIL] {exc}")


def check_web_search_trigger() -> None:
    print("\n--- Check 7: literature-flavored prompt (web search trigger?) ---")
    prompt = (
        "Search for recent papers about molecular gas inflow onto AGN in barred "
        "galaxies and summarize the top findings in 2 sentences."
    )
    try:
        result = _invoke(prompt)
        print(f"  text: {result.text!r}")
        ws_keys = {k: v for k, v in result.raw.items() if "web_search" in k.lower() or "search" in k.lower()}
        print(f"  web-search-related raw fields: {ws_keys}")
    except ClaudeCLIError as exc:
        print(f"  [FAIL] {exc}")


def check_model_pinning() -> None:
    print("\n--- Check 8: does --model pin generation to one model? ---")
    for model in (None, "claude-haiku-4-5", "claude-sonnet-5"):
        try:
            result = _invoke("Reply with exactly the single word: PONG", model=model)
            model_usage = result.raw.get("modelUsage") or result.raw.get("model_usage")
            print(f"  model={model!r}: modelUsage={model_usage}")
        except ClaudeCLIError as exc:
            print(f"  model={model!r}: [FAIL] {exc}")


def check_realistic_prompt_budget() -> None:
    print("\n--- Check 9: cost/latency on a realistic-sized prompt ---")
    try:
        result = _invoke(REALISTIC_PROMPT)
        print(f"  prompt_len={len(REALISTIC_PROMPT)} chars")
        print(f"  wall_clock={result.wall_clock_s:.2f}s, duration_ms={result.duration_ms}, "
              f"cost=${result.cost_usd:.4f}")
        print(f"  response: {result.text!r}")
    except ClaudeCLIError as exc:
        print(f"  [FAIL] {exc}")


def main() -> int:
    checks = [
        check_repeated_calls,
        check_growing_context_loop,
        check_json_output,
        check_messy_output,
        check_timeout_kills_tree,
        check_tool_tempting_prompt,
        check_web_search_trigger,
        check_model_pinning,
        check_realistic_prompt_budget,
    ]
    for check in checks:
        check()
    print("\nAll Stage 2 checks ran. Review output above for pass/fail and observational findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
