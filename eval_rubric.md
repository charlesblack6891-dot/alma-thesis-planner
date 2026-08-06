# Goalpost 4 — Small-Batch Calibration Eval Rubric

**Status:** draft, scored by Claude/the user in place of Paul (no domain-expert astronomer in the
loop yet). Treat every score below as provisional pending Paul's review — the point of writing it
down now is to have a consistent, repeatable instrument, not to certify these scores as
domain-expert-approved.

Per `PROJECT_ROADMAP.md`'s Goalpost 4 spec, this rubric scores each dataset's pipeline output on
four axes. Scored per dataset after a live `run_pipeline.py` run.

## 1. Abstract quality (1-5)

Does `writeup.md`'s Abstract section accurately and clearly state the scientific question and the
bounded approach, without overclaiming or vague hand-waving?

- **5** — Precise, scientifically sound, states a clear testable question and why the dataset can
  answer it.
- **3** — Correct but generic; reads as boilerplate more than a dataset-specific pitch.
- **1** — Vague, scientifically questionable, or doesn't match the actual data description.

## 2. Thesis-scope feasibility (1-5)

Independent re-check of Stage 5's own tractability rubric, applied to the *final* writeup, not the
raw idea — does the Work Plan describe something a single student could plausibly complete in a
thesis timeframe (a semester to a year), using only the data/tools in `data_description.md`?

- **5** — Clearly bounded, concrete steps, no hidden dependencies on data/instruments not already
  in hand.
- **3** — Plausible but risks scope creep (e.g. a "fallback track" that's really a second thesis, an
  open-ended parameter sweep with no stated stopping point).
- **1** — Reads as a multi-year research program, or silently assumes results/data that don't exist
  yet.

Cross-check against the pipeline's own `tractability_score` from Stage 5 (`idea.md`'s scoring, or
`PipelineResult.tractability_score`) — note explicitly if this rubric's score disagrees with Stage
5's self-reported score, since a persistent gap between the two would mean Stage 5's rubric is
miscalibrated, not just this one idea.

## 3. Reading-list relevance (1-5)

Are the citations in `literature.md` / the Background Reading section actually relevant background
for the proposed idea, not padding or tangential hits?

- **5** — Every citation is either the source paper for a published dataset, or genuinely relevant
  background/method literature for the proposed idea.
- **3** — Mostly relevant, one or two borderline/generic inclusions.
- **1** — Citations are off-target (wrong subfield, wrong instrument, or clearly a keyword-match
  false positive from the Semantic Scholar search).

## 4. Published/unpublished accuracy (binary, ground-truth cases only)

Does the Stage 6 verdict in `literature.md` match known ground truth? Only scoreable for datasets
where ground truth is independently known (confirmed published DOI, or confirmed proprietary/
unreleased in the ALMA archive) — mark `N/A` otherwise, do not guess a "probably correct" score.

- **Pass** — verdict matches ground truth.
- **Fail** — verdict contradicts ground truth (this is the one axis with a hard bar; a Fail here
  should block the batch from being called calibrated, regardless of the other three scores).

## Per-dataset scoring table

| Dataset | Abstract quality | Thesis-scope feasibility | Reading-list relevance | Published/unpublished accuracy | Notes |
|---|---|---|---|---|---|
| `project_ngc4061` | N/A (short-circuit) | N/A (short-circuit) | 4/5 | Pass | Correctly short-circuited via `run_pipeline.py` 2026-07-22. Single self-referential citation (Nguyen et al. 2026), correct but unverified by Semantic Scholar (0 results) -- asserted from the data description text alone. |
| `project_w49a_unpublished` | 2/5 | 2/5 | 3/5 | Pass | Full pipeline run via `run_pipeline.py` 2026-07-22. Agrees with Stage 5's own self-score (1/3 YES) -- the idea substitutes the actual (proprietary, unexecuted) dataset with older VLA/ALMA archival data whose availability is unconfirmed, and the 3-way contingency (Track A/B/C) risks scope creep, especially Track C reading as a literature reanalysis rather than original thesis work. Single reading-list citation, thin but genuinely relevant. |
| `project_w49a_variability_2018` | 5/5 | 5/5 | 4/5 | Pass | **Caveat: predates Stage 9, not run via `run_pipeline.py`.** Built directly via Stage 5/7/8 runners in the 2026-07-21 session, before the short-circuit existed -- since this dataset is actually PUBLISHED, re-running it through `run_pipeline.py` today would (correctly) short-circuit instead of producing this writeup. Scored here as a Stage 5-8 prompt-quality sample, not a Stage 9 branching test. Best writeup of the three: bounded methods-correction framing, concrete validation checkpoint against the paper's own published numbers, agrees with Stage 5's self-score (3/3 YES). |

| `project_mp_mus_disk` | N/A (short-circuit) | N/A (short-circuit) | 5/5 | Pass | Correctly short-circuited 2026-07-22. First case where Semantic Scholar returned real hits: correctly identified the matching Aguayo et al. 2025 paper *and* explicitly distinguished it from a different, earlier (2023) paper on the same target rather than conflating the two. |
| `project_hd138813_unpublished` | 5/5 | 5/5 | 5/5 | Pass | Deliberately hard case: same target *and* overlapping PI (Matra) already published via ARKS (2022.1.00338.L), but this project code (2025.1.00062.S) is a distinct, unreleased follow-up. Stage 6 correctly resisted the trap (NOT_PUBLISHED, explicitly reasoning the ARKS citation is a different project code). Stage 5's idea loop independently discovered the same nuance unprompted -- built its own literature-audit gate before committing scope and explicitly excluded the proprietary dataset. Best-scoring writeup of the batch so far; agrees with Stage 5's own 3/3 YES self-score. |

| `project_hops315_outflow` | N/A (short-circuit) | N/A (short-circuit) | 4/5 | **Pass (fixed 2026-07-22)** | Ground truth PUBLISHED (Dutta 2025, ApJ 991, 45, DOI 10.3847/1538-4357/adf8d6). Originally a Fail (NOT_PUBLISHED) -- re-run after the `novelty_prompt` self-citation fix now correctly returns PUBLISHED and short-circuits, citing the fix's own rule by name in its justification. See Known Issues below. |
| `project_ic443g_shock` | 5/5 | 5/5 | 4/5 | Pass | Genuinely un-ALMA-published target (well-studied at other wavelengths, but no prior ALMA publication found during sourcing). Idea loop explicitly abandoned the proprietary dataset and pivoted to a fully archival single-dish reanalysis -- strong, well-grounded result, agrees with Stage 5's 3/3 YES self-score. |
| `project_m87_unpublished` | 3/5 | 4/5 | 4/5 | Pass | Hardest case in the whole project: M87 is one of the most ALMA-published AGN targets in existence. Stage 6 correctly resisted every confusable prior publication across all 3 runs. Stage 5's idea loop was re-run twice after `idea_maker_prompt`/`idea_hater_prompt` fixes -- run 2 (first fix) still fabricated an unnamed external dataset (VLBA/MOJAVE, never mentioned in the description), correctly caught and named by the strengthened hater; run 3 (second, stricter fix) no longer introduces any unnamed dataset, confining itself entirely to the one paper actually named in the description. Still scores 2/3 YES on Stage 5's own rubric (not 3/3), because that named paper was itself framed as "unrelated" in this test case's own data description -- a tension in how *this specific dataset* was authored (see Known Issues), not a remaining prompt-logic bug. Also has a minor, unexplained text artifact in the abstract's opening clause ("Villar-Martin data situation aside") -- noted but not investigated further. |

| `project_hd66811_masslos` | N/A (short-circuit) | N/A (short-circuit) | 4/5 | Pass | Correctly short-circuited 2026-07-22, new science category (massive-star wind/mass-loss, distinct from every other dataset in the batch). Ground truth confirmed via a real IAU Symposium 329 proceedings paper (Setia Gunawan et al. 2017, DOI 10.1017/S1743921317002861) that explicitly acknowledges this exact ALMA project code (2012.1.00955.S) and names HD 66811 in its 8-star sample. Zero Semantic Scholar hits, correctly relied on the self-citation rule -- a clean generalization check: this dataset was sourced *after* the self-citation fix went in, not one of the cases the fix was tuned against. Single self-referential citation, correct but thin (same pattern as `project_ngc4061`). |

(Rows for newly sourced Goalpost 4 datasets get appended below as they're run.)

## Known issues surfaced by this batch (Goalpost 4's actual purpose)

**1. Stage 6 false negative on `project_hops315_outflow` (axis-4 Fail) -- FIXED 2026-07-22.** The data
description explicitly named the source publication with a real DOI (Dutta et al. 2025, ApJ 991, 45)
-- the same kind of explicit self-citation that Stage 6 correctly trusted for `project_ngc4061`
(verdict PUBLISHED, also zero Semantic Scholar hits) and `project_mp_mus_disk` (verdict PUBLISHED,
real corroborating hits). For HOPS 315, with an equally explicit citation and zero Semantic Scholar
hits, Stage 6 instead concluded "the publication claim cannot be confirmed from the evidence
provided" and returned NOT_PUBLISHED -- an inconsistency (same evidence pattern, trusted once and
distrusted once), not just a single bad call.
**Fix:** added an explicit "self-citation rule" to `novelty_prompt` (`literature.py`): a specific,
well-formed self-citation (DOI/journal/author-list, tied to this project's own data) is sufficient
for PUBLISHED on its own and must not be downgraded merely because Semantic Scholar returned nothing
-- only an affirmative contradiction, or a vague/unverifiable citation, should discount it.
**Verified:** re-ran `run_pipeline.py` against `project_hops315_outflow` live after the fix -- now
correctly returns PUBLISHED and short-circuits, with the justification explicitly invoking the new
rule ("per the self-citation rule, this specific, well-formed reference... is sufficient for PUBLISHED
despite the empty Semantic Scholar search"). Offline `test_stage6.py` (4/4) still passes unchanged.

**2. Stage 5 idea-loop data-substitution risk on `project_m87_unpublished` -- IMPROVED, not fully
resolved, 2026-07-22.** When the assigned dataset is proprietary and the target is extremely
well-studied, the idea loop's fallback strategy (seen working well on `project_hd138813_unpublished`
and `project_ic443g_shock`, both of which grounded their substitute idea in data genuinely tied to
the same physical system and explicitly named in their own data descriptions) instead grabbed an
unrelated, narrower public dataset on the same famous target with no stated connection to what
2025.1.00830.V was actually for.
**Fix, round 1:** added a "substitute-data rule" to `idea_maker_prompt` (require the alternative to be
justified as addressing the same kind of scientific question) and a matching check to
`idea_hater_prompt`. **Result:** re-run live -- the hater now correctly named the exact violation by
description ("substitutes a VLBA/MOJAVE jet-kinematics compilation... that is never mentioned anywhere
in the data description"), but the maker's *next* idea still reached for a different unnamed dataset
(Walker et al. 2018 VLBA/MOJAVE data) rather than stopping -- the rule wasn't concrete enough to close
the loophole of introducing a dataset from the model's own general knowledge.
**Fix, round 2:** tightened the rule to explicitly forbid introducing any external dataset/paper/
catalog not literally named in the data description, treating unnamed ones as unavailable regardless
of real-world relevance. **Result:** re-run live again -- the final idea now confines itself entirely
to the one paper actually named in the description (A&A 699, A265), no longer fabricating an unnamed
second dataset. This is real, verified progress: the specific failure mode (introducing datasets from
the model's own knowledge that aren't in the description) is closed.
**Not fully resolved:** the idea still scores 2/3 (not 3/3) on Stage 5's own tractability rubric,
because *this specific test dataset's* own description explicitly frames the one named background
paper as "unrelated to this project" -- a wording choice made when authoring
`project_m87_unpublished/input_files/data_description.md`, not a remaining prompt-logic bug. Given
that framing, any idea built on that paper will honestly still read as a substitution, and arguably a
model that keeps flagging it as such (rather than pretending the tension away) is behaving correctly.
Left open: whether to reauthor this one dataset's description to remove the self-inflicted "unrelated"
framing, or accept a 2/3 score as the correct outcome for a case this genuinely constrained (the
assigned dataset's real science goal was never confirmed in the first place). Offline `test_stage5.py`
(4/4) still passes unchanged throughout both rounds.

**Early calibration signal (updated, 9 datasets, post-fix):** Stage 5's own tractability self-score
continues to agree with this rubric's independent thesis-scope-feasibility score in every case scored.
Batch published/unpublished accuracy: **9/9 Pass** after the `novelty_prompt` self-citation fix
(`project_hops315_outflow` was the one Fail, now fixed and re-verified live). Notably, that Fail
happened on an *easier* case (a single target with one clearly-cited real publication) than three
genuinely hard same-target-discrimination traps the pipeline got right on the first try (W49A,
HD 138813, M87) -- accuracy does not simply track "case difficulty," worth keeping in mind when
eventually setting Goalpost 4's aggregate threshold. Both issues found were run through a fix-and-
reverify cycle this session (not just logged) -- see Known Issues below for exactly what changed and
what, in the M87 case, remains an open, arguably-correct limitation rather than a bug.
`project_hd66811_masslos` (9th dataset, added after both fixes) is a genuine out-of-sample check on
the self-citation fix -- it was sourced and run after the fix went in, not one of the cases used to
design or verify it, and it passed cleanly on the first try.

## Aggregate pass/fail threshold

**Not yet set — per `PROJECT_ROADMAP.md`, this is explicitly deferred to Paul at this goalpost, not
fixed in advance.** Provisional working bar until Paul weighs in: average score ≥3.5/5 on axes 1-3
across the batch, and zero Fails on axis 4 (published/unpublished accuracy has no partial credit —
a wrong verdict is a hard failure of the pipeline's core claim).
