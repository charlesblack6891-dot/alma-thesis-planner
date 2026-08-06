# Goalpost 4 Review — Small-Batch Calibration

**For:** Paul **From:** [your name] **Date:** 2026-07-22
**Ask:** ~15 minutes to read this and answer the 5 questions at the bottom. Full detail (all 8 writeups, per-axis scores, prompts) is in the repo if you want to go deeper than this summary.

## What this is

Goalpost 4 in the build plan: run the full pipeline (idea → methods → literature check → one-pager) across a small batch of real ALMA datasets, score the output against a lightweight rubric, and fix whatever it surfaces before trusting the pipeline at any larger scale. This is the first review checkpoint since Goalpost 0 — everything below (the rubric itself, the datasets, the scoring) was done without your input, so treat all of it as a draft for your review, not a finished decision.

## What was run

8 real ALMA datasets, deliberately spanning a mix of published/unpublished and easy/hard cases:

| Dataset | Science case | Ground truth | Pipeline verdict |
|---|---|---|---|
| NGC 4061 | Galaxy dynamics, CO kinematics → SMBH mass | Published | ✅ Correct (short-circuit) |
| W49A (2024.1.00717.S) | Galactic HII regions, H21α line | Unpublished (proprietary) | ✅ Correct |
| W49A variability (VLA, companion dataset) | Flux-density variability | Published | ✅ Correct |
| MP Mus (PDS 66) | Protoplanetary disk continuum | Published | ✅ Correct |
| HD 138813 | Debris disk continuum | Unpublished — **same target and PI as an already-published survey (ARKS), different project code** | ✅ Correct |
| HOPS 315 | Protostellar outflow, line kinematics | Published | ❌ Initially wrong (see Issue 1) → ✅ after fix |
| IC 443 clump G | Supernova-remnant shock chemistry | Unpublished, genuinely no prior ALMA data | ✅ Correct |
| M87 (2025.1.00830.V) | AGN jet, VLBI-affiliated | Unpublished — **one of the most ALMA-published AGN targets in existence**, hardest case in the batch | ✅ Correct |

**Bottom line: 8/8 correct on published/unpublished status**, after one fix (below). Three of these were deliberately constructed to be hard — same target as an existing publication, but a different, unreleased project code — specifically to stress-test whether the novelty check can tell "this target has been studied" apart from "this specific project's data has been published." All three passed.

## The rubric used

Four axes, scored per dataset (full definitions and per-dataset scores in `eval_rubric.md`):
1. **Abstract quality** (1-5) — clear, accurate, dataset-specific, not boilerplate.
2. **Thesis-scope feasibility** (1-5) — genuinely completable by one student in a semester-to-a-year, no hidden dependencies.
3. **Reading-list relevance** (1-5) — citations are actually relevant, not padding.
4. **Published/unpublished accuracy** (pass/fail, no partial credit) — this is the one that matters most; a wrong verdict here means the pipeline's core claim is broken.

Across the 6 datasets that generated a full idea (not a published-short-circuit), scores ranged 2-5 on axes 1-3, median around 4-5. Two datasets (W49A unpublished, and M87 on its first pass) scored low on thesis-scope feasibility specifically because the idea leaned on data not genuinely available — see Issue 2.

## Two issues found, both addressed

**Issue 1 — inconsistent handling of self-reported citations.** When a dataset's own description names its source publication (with a DOI), the pipeline sometimes trusted that as sufficient evidence of "published" and sometimes didn't, even with functionally identical evidence. This caused the one wrong verdict in the batch (HOPS 315). **Fixed**: added an explicit rule — a specific, well-formed self-citation is trusted unless something actively contradicts it. Re-verified live; now correct.

**Issue 2 — the idea generator sometimes substitutes in unrelated data.** When a dataset's real data isn't usable yet (proprietary) and the target has other public data available, the idea-generation step would sometimes reach for that other data even when it didn't actually address the same scientific question — including, on one pass, inventing a dataset that wasn't even mentioned in the project's own description. **Fixed** (two rounds of tightening the prompt); verified live that the pipeline no longer fabricates data sources outside what's actually described. One edge case (M87) still scores 2/3 rather than 3/3 on its own honesty-check, but that's arguably correct: for that one dataset we never actually confirmed what its real science goal is, so any substitute idea is honestly incomplete — not a bug to fix, just a hard case.

**New safety feature added as a result**: if an idea doesn't pass all three of its own tractability checks, the final one-pager now opens with an explicit caution banner quoting exactly which check failed, rather than silently presenting a shaky idea as fully vetted.

## Questions for you

1. **Aggregate threshold** — what should count as "the batch passed"? My working placeholder (not yet applied to anything): average ≥3.5/5 on axes 1-3, and zero failures on axis 4 (no partial credit for a wrong published/unpublished call). Does that bar feel right, too strict, or too loose?
2. **Is Semantic Scholar enough** for the published-check, or do we need NASA ADS / the ALMA archive's own publication-linkage field as a backup? It missed real papers in a couple of cases here (the pipeline still got the right answer via the dataset's own citation, but Semantic Scholar itself came up empty both times).
3. **How rigorously does "already published" need to be verified** before you'd trust the pipeline to skip a dataset unattended, vs. flagging it for human review? This shapes the review-queue design later on.
4. **Any hard constraint on cost/volume** to design around? Realistic numbers now: roughly $0.4-0.6 and a few minutes per dataset for the full unpublished-branch pipeline; a few cents and seconds for a published short-circuit.
5. **Should the novelty-check be allowed to use web search**, or should it stay limited to the explicit Semantic Scholar call for reproducibility? (Currently: no web search.)

Happy to adjust the rubric, re-run against more datasets, or dig into any of the 8 writeups in detail if useful before you answer these.
