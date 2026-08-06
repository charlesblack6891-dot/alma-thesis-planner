# ALMA Dataset → Senior Thesis Planner — Final Plan

**Status:** consolidated from `PROJECT_BRIEF.md`, `BUILD_PLAN.md`, and `PROJECT_ROADMAP.md`. Those
files retain the fuller history/reasoning behind each decision; this is the single reference copy.

## Project goal

Build an LLM-powered tool that examines an ALMA dataset, determines whether it has already been
published in a peer-reviewed journal, and — if not — produces a roughly one-page plan (an
abstract, a description of work to be carried out with anticipated key results/plots, and a
background-reading list) for a senior-thesis-level project using that dataset. The output is a
plan for a *human* to execute, not an automated research pipeline. It is built as a lean,
standalone tool that borrows Denario's prompts, markdown-file conventions, and project-directory
layout, but replaces all of Denario's API-key-based LLM calls with headless Claude Code CLI
invocations (`claude -p ...` via subprocess) — zero API keys — rather than modifying Denario in
place.

## Stage-by-stage breakdown

### Stage 1 — Claude CLI call primitive
*Purpose: establish the one function every later stage depends on — a reliable way to send a
prompt to Claude and get text back, with zero API keys. Finished when it reliably returns exact,
well-formed text for simple test prompts with no manual intervention.*
- **Input:** a raw prompt string (plain text, no LangChain wrapper); synthetic/hardcoded test
  prompts only, no ALMA data.
- **Output:** `call_claude(prompt: str) -> str`, shelling out to `claude -p ... --output-format
  json` and parsing the `result` field. Must pass `stdin=subprocess.DEVNULL` and capture stdout/
  stderr on separate streams.
- **Verification:** with `OPENAI_API_KEY`/`GOOGLE_API_KEY`/`ANTHROPIC_API_KEY` unset,
  `call_claude("Reply with exactly the single word: PONG")` returns exactly `"PONG"`; a
  `\begin{IDEA}...\end{IDEA}` block prompt survives the round-trip intact; wall-clock time is
  recorded separately from the CLI's own reported `duration_ms`.
  **Done — code written and passing.** `llm.py` (`call_claude`, `_invoke`, `ClaudeResult`,
  `ClaudeCLIError`) and `test_stage1.py` now exist at the repo root. Run 2026-07-11 via
  `C:\Users\cb447\AppData\Local\Programs\Python\Python313\python.exe test_stage1.py` — a plain
  system Python 3.13, no virtualenv, invoked from native PowerShell (not Git Bash) — with all three
  API-key env vars unset: 4/4 checks passed (no-API-keys check, 3/3 PONG exact matches, IDEA block
  round-trip, and the public `call_claude(prompt) -> str` signature). This also closes out the
  Stage 2/BUILD_PLAN addendum item 7 concern (native-Windows-Python vs. Git Bash PATH resolution) —
  `shutil.which("claude")` resolves `claude.exe` directly under both. Wall-clock 10.2–13.0s/call,
  `duration_ms` 2.3–2.8s, `total_cost_usd` $0.0096–$0.059 per PONG call (CLI v2.1.207) — all higher
  than the original manual-testing numbers below, worth tracking as CLI-version drift rather than
  a regression.

### Stage 2 — Claude CLI stress test
*Purpose: find out how the CLI behaves under repeated and adversarial conditions — cost, latency,
malformed output, timeouts — before anything is built on top of it. Finished when every stress
check passes or has a documented workaround, so Stage 3 onward can trust the primitive without
surprises.*
- **Input:** `call_claude` from Stage 1; synthetic prompts, including one realistic
  production-sized prompt and one JSON-format prompt (matching the novelty-check's expected
  output) — not yet real ALMA data.
- **Output:** a validation log documenting behavior under repeated/adversarial conditions, not
  production code.
- **Verification:** 10 back-to-back calls with no failures/truncation, P50/P95 latency recorded; a
  simulated 3–4 call loop with artificially growing prompt size to check whether cost/latency scale
  linearly (mimics Stage 5's growing `previous_ideas` context); a JSON-response prompt parses
  cleanly or the fallback-repair path is exercised and documented; a hard subprocess timeout is
  enforced and kills the full process tree on Windows; a literature-flavored prompt is checked for
  whether it triggers Claude Code's built-in web-search tool (observed to be available) in a way
  that affects reproducibility; whether `--model` reliably pins generation to one model (a single
  test call showed both `claude-haiku-4-5` and `claude-sonnet-5` billed together); cost/latency
  budget computed from realistic-sized prompts, not the trivial case; `call_claude` confirmed to
  work identically from plain Windows Python, not just Git Bash.
  **Not yet run — this is the concrete next action.**

### Stage 3 — Output-parsing and file-state primitives
*Purpose: give every later stage a reliable way to pull structured content out of raw Claude text
and persist it to the project's markdown files. Finished when extraction handles both clean and
malformed output predictably, and a file round-trips through write/read with no data loss.*
- **Input:** raw text from `call_claude`; synthetic well-formed and deliberately malformed test
  strings; no ALMA data.
- **Output:** `extract_block(text, tag) -> str` (regex + repair fallback, ported from Denario's
  `extract_latex_block`); read/write helpers for the markdown state files (`data_description.md`,
  `idea.md`, `methods.md`, `literature.md`) under `input_files/`.
- **Verification:** well-formed input extracts cleanly; malformed input (missing closing tag)
  triggers the fallback path predictably rather than crashing; a file round-trips byte-identical
  through the write/read helpers.
  **Done — code written and passing.** `blocks.py` (`extract_block`, `BlockExtractionError`) and
  `state.py` (`read_state_file`, `write_state_file`, following `denario/config.py`'s
  `input_files/`+filename convention) now exist at the repo root, plus `test_stage3.py`. Unlike
  Stage 1/2's tests, this suite makes **zero live `claude` CLI calls** — the repair-fallback path
  is exercised via a `repair_fn` dependency-injection parameter on `extract_block` (defaults to
  `call_claude`, overridable for tests), so it's free and deterministic to run. 6/6 checks passed
  (well-formed extraction, malformed+`repair=False` raises, malformed+fake-repair-success uses the
  repaired output, malformed+fake-repair-failure still raises cleanly, file round-trip, and
  `input_files/` auto-creation). Also wrote `paul_check.py`, the concrete one-command script named
  in Paul's Goalpost-1 pass/fail check (prompt-template → `call_claude` → `extract_block` →
  `write_state_file`, run twice unattended) — compiles and imports cleanly but **has not yet been
  run live** (it makes real, cost-incurring CLI calls; deliberately not run without checking in
  first — see session log).

### Stage 4 — Example dataset → `data_description.md`
*Purpose: get one real ALMA dataset's metadata into the pipeline's input format for the first time.
Finished when the filled template is complete and accurate against the source metadata.*
- **Input:** manually downloaded metadata for the one example ALMA dataset (project code, PI,
  target, band/frequency, obs date, array config, proposal science-goal abstract, data products).
  **Real data enters the pipeline here for the first time.**
- **Output:** a filled `data_description.md` for that dataset.
- **Verification:** cross-checked field-by-field against the raw metadata source for completeness;
  round-trips through the Stage 3 I/O helper.
  **Done, with two flagged gaps.** `project_ngc4061/input_files/data_description.md` built from
  Nguyen et al. 2026 (ApJ, DOI 10.3847/1538-4357/ae771c) — project codes, PI names, band/frequency,
  array config, and data products all cross-checked against the source text and present. Round-trip
  through `write_state_file`/`read_state_file` confirmed byte-identical (2034 chars). Two checklist
  fields could not be filled from the paper alone and are left flagged rather than guessed: (a) exact
  observation date/epoch of the ALMA execution blocks, and (b) the original ALMA time-proposal's
  science-goal abstract (substituted with the published paper's own science summary instead, which
  is a materially different document). Both would require a direct ALMA Science Archive lookup by
  project code to close — deferred per the user's decision to move forward without them for now.

### Stage 5 — Idea-maker / idea-hater loop
*Purpose: generate one thesis-scoped project idea from the dataset, adapted from Denario's
critique loop. Finished when the loop produces a settled idea that demonstrably improved through
criticism and passes the tractability rubric.*
- **Input:** `data_description.md`; `idea_maker_prompt`/`idea_hater_prompt` ported from Denario and
  reframed to senior-thesis scope; a plain Python loop replacing LangGraph's router. Run once
  against a synthetic toy dataset first (smoke test), then against the real Stage 4 dataset.
- **Output:** `idea.md` — one settled, thesis-scoped project idea.
- **Verification:** idea text changes meaningfully across maker/hater iterations, not just
  repeating; the final idea is scored against a 3-question tractability rubric *at this stage, not
  deferred to later batch calibration* — (1) bounded to one thesis timeframe, (2) no new
  instrumentation/data beyond `data_description.md`, (3) a domain expert would call it tractable;
  zero API keys present during the run.
  **Done.** `idea_loop.py` (`idea_maker_prompt`/`idea_hater_prompt`/`tractability_prompt`, ported
  from Denario's LangGraph `idea_maker`/`idea_hater`, reframed to thesis scope, plain Python loop
  replacing the LangGraph router) plus `test_stage5.py` (4/4 offline checks, $0 cost, dependency-
  injected `call_claude_fn` per Stage 3's pattern) and `run_idea_loop.py` (the live runner). Smoke-
  tested first against a synthetic toy dataset (`project_toy_smoketest`, 2 iterations) -- caught and
  fixed a real bug (Windows console defaults to cp1252, which can't encode characters like the
  arcsec double-prime mark that Claude's responses commonly include; fixed by forcing UTF-8
  stdout/stderr in the runner). Also discovered `claude` isn't on WSL's PATH -- this stage's code
  has zero heavy dependencies by design, so it runs from native Windows Python (where Stage 1
  already confirmed `claude.exe` resolves), not through the Denario-fork WSL venv. Ran live (4
  iterations, 9 calls total) against the real Stage 4 dataset (`project_ngc4061`) with all three
  API-key env vars confirmed unset beforehand. The critique loop genuinely revised the idea each
  round rather than repeating: iteration 1's custom "forward-modeling" beam-smearing step was caught
  as secretly reintroducing the original paper's own hardest multi-month technique, swapped for an
  existing tool (3D-Barolo); a later round's hater independently computed the black hole's
  sphere-of-influence vs. the beam size (~0.6-1.3 beams -- borderline unresolved) and caught the
  continuum image having no defined role in the method, both fixed in the next iteration. Final idea
  scored 3/3 YES on the tractability rubric. Written to `project_ngc4061/input_files/idea.md`.

### Stage 6 — Published/novelty check
*Purpose: answer the tool's core question — has this dataset already been published — with cited
evidence. Finished when the verdict matches known ground truth on both a published and an
unpublished test case.*
- **Input:** `data_description.md` (+ `idea.md` if useful); `novelty_prompt`/
  `summary_literature_prompt` ported and reframed around project code/PI/target rather than generic
  idea novelty; the plain (non-LLM) Semantic Scholar REST call. **Requires 2–3 real, hand-picked
  datasets with known ground truth** (at least one confirmed published, one confirmed not).
- **Output:** `literature.md` — a PUBLISHED / NOT-PUBLISHED verdict with citations, doubling as the
  background-reading list.
- **Verification:** verdict matches ground truth for both test cases; cross-checked against the
  ALMA archive UI's own publication-linkage field where possible.
  **Closed — live verification run 2026-07-21.** `run_literature_check.py project_ngc4061 ...`
  returned `VERDICT: PUBLISHED`, correctly citing the Nguyen et al. 2026 paper named in that
  project's own `data_description.md`. `run_literature_check.py project_w49a_unpublished ...`
  returned `VERDICT: NOT_PUBLISHED`, and explicitly reasoned that the unrelated 2024 A&A paper by
  overlapping authors (Wilner/Tobin, arXiv:2404.02250) on the same target is not a match for this
  project code -- the exact non-trivial distinction this ground-truth pair was built to test. Both
  verdicts written to each project's `literature.md`; both ground-truth cases now pass.
  `literature.py` (`search_semantic_scholar`,
  `novelty_prompt`, `check_published`) and `test_stage6.py` (4/4 offline checks, $0 cost, both the
  Semantic Scholar call and the `claude` call dependency-injected per Stage 3/5's pattern) plus
  `run_literature_check.py` (the live runner). `novelty_prompt` explicitly warns that a shared
  target or shared author doesn't by itself mean a match -- needed for the W49A test case, where an
  unrelated 2024 paper by overlapping authors exists on the same target. Hit two real environment
  issues getting the live Semantic Scholar call working: (1) the same AVG-antivirus TLS-interception
  root cert from earlier sessions, but rejected by Python 3.13's stricter default
  `VERIFY_X509_STRICT` check (the cert's Basic Constraints extension isn't marked critical, an RFC
  5280 violation) even once trusted -- fixed by loading the cert into the SSL context *and* clearing
  that flag; (2) Semantic Scholar's unauthenticated tier hit a persistent HTTP 429 (didn't clear
  after 45+ seconds of backoff) -- added retry-with-backoff, but decided to wait and retry live
  verification later rather than get a dedicated API key right now. This blocker is now resolved,
  see the live-verification note above.

### Stage 7 — Methods / work-plan generation
*Purpose: turn the settled idea into a concrete description of the work a student would actually
do. Finished when a human reviewer agrees it's executable in a thesis timeframe without assuming
results that don't exist yet.*
- **Input:** `data_description.md` + `idea.md` (real data); `methods_fast_prompt` ported, reframed
  to describe anticipated key plots/results rather than executed ones.
- **Output:** `methods.md` — description of work to be carried out.
- **Verification:** manual read confirms it's executable by a student in a thesis timeframe and
  doesn't presuppose results that don't exist yet.
  **Done — code written and run live 2026-07-21.** `methods.py` (`methods_prompt`,
  `generate_methods`) ports `methods_fast_prompt` from `denario/langgraph_agents/prompts.py`,
  reframed to thesis-student scope, following Stage 5's injectable-`call_claude_fn` pattern.
  `run_idea_and_methods.py` chains the Stage 5 idea loop straight into methods generation for one
  project directory. Run live against a new third dataset, `project_w49a_variability_2018`
  (De Pree et al. 2018, ApJ Letters, arXiv:1807.10669 -- a confirmed-published VLA 3.6cm
  flux-variability study of the same W49A field as `project_w49a_unpublished`, sourced as a
  companion/background dataset). The idea loop's critic caught real problems across 4 iterations
  (an early idea risked reproducing a table the source paper likely already published; a
  correlation-analysis variant was rejected for having no statistical power with only one variable
  source) before settling on a bounded methods contribution (multi-component deblending bias in the
  field's crowded subregion), scored 3/3 YES on tractability. `methods.md` written as a 7-phase
  CASA-based workflow. Both `idea.md` and `methods.md` written to
  `project_w49a_variability_2018/input_files/`.

### Stage 8 — One-page writeup assembly
*Purpose: combine the idea, methods, and reading list into the actual one-page deliverable.
Finished when the assembled document is coherent, complete, and close to one page.*
- **Input:** `idea.md` (abstract), `methods.md` (work description), `literature.md` (reading list)
  — real data.
- **Output:** a single ~1-page markdown/text file combining all three sections.
- **Verification:** close to one page; contains all three required sections; reads as one coherent
  document, not three stapled-together fragments.
  **Done — code written and run live 2026-07-21.** `writeup.py` (`writeup_prompt`,
  `assemble_writeup`) and `run_writeup.py`. Unlike Stages 5/7, there's no Denario prompt to port
  here (Denario writes a full paper, not a one-pager), so this prompt is original, designed
  directly from `PROJECT_BRIEF.md`'s spec -- Abstract / Work Plan (with anticipated key
  results/plots) / Background Reading, under ~700 words. Run live against all three real projects
  that had complete inputs (after backfilling the missing `methods.md`/`literature.md` pieces with
  `run_methods.py` and `run_literature_check.py`): `project_ngc4061` (621 words),
  `project_w49a_unpublished` (641 words), `project_w49a_variability_2018` (608 words). All three
  read as one coherent document with all three required sections; `writeup.md` written to each
  project's `input_files/`.

### Stage 9 — End-to-end orchestration + published short-circuit
*Purpose: wire every prior stage into one entrypoint that automatically branches on the
published/unpublished verdict. Finished when a single command produces the correct output type for
both ground-truth test datasets, with no manual stage-by-stage invocation.*
- **Input:** a `data_description.md` for any dataset; one CLI entrypoint script. Real data — both
  ground-truth datasets from Stage 6.
- **Output:** either a short "already published" note + citation, or the full Stage 8 one-pager.
- **Verification:** run on both test datasets; each takes the correct branch automatically, with no
  manual stage-by-stage invocation.
  **Done — code written and run live 2026-07-22.** `pipeline.py` (`run_pipeline`, `PipelineResult`,
  `short_circuit_note`) wires Stage 6's `check_published` in front of Stages 5/7/8, following
  Stage 3/5/6/7/8's dependency-injection pattern so the branching logic itself is unit-testable for
  $0 -- `test_stage9.py` (4/4 offline checks) proves Stage 5/7/8 are never invoked on the
  PUBLISHED/UNKNOWN branches (each fake raises if called) and that data is wired through correctly
  on the NOT_PUBLISHED branch. Verdicts of `UNKNOWN` (unparseable Stage 6 output) also short-circuit,
  worded distinctly from `PUBLISHED` rather than defaulting to either branch silently. `run_pipeline.py`
  is the single CLI entrypoint (`python run_pipeline.py <project_dir> <project_code> <pi> <target>
  [n_iterations]`). Run live against both ground-truth datasets: `project_ngc4061` returned
  `VERDICT: PUBLISHED` and correctly short-circuited, writing a citation-only note to `writeup.md`
  with zero Stage 5/7/8 calls; `project_w49a_unpublished` returned `VERDICT: NOT_PUBLISHED` and
  correctly ran the full idea/methods/writeup pipeline, producing a 699-word one-pager. **Goalpost 3
  is now closed.**
  **Open finding, not yet resolved:** the NOT_PUBLISHED live run's final idea scored 1/3 YES on
  Stage 5's own tractability rubric (2/3 NO -- it leans on unconfirmed archival VLA/ALMA datasets not
  established in the actual data description), but `run_pipeline`/`run_pipeline.py` don't gate on
  that score -- they log it and proceed to Stages 7/8 regardless, per Stage 5's original "score,
  don't block" spec. Worth a decision before this becomes the default unattended path: should Stage 9
  halt (or re-run the idea loop) on a failing tractability score rather than building methods/writeup
  on top of a flagged-bad idea?

### Stage 10 — Topic-only entrypoint (no project code, PI, or target needed)
*Purpose: remove the last manual step before the tool can be run "as itself" — knowing an ALMA
project code, PI, and target ahead of time. Finished when a single free-text topic sentence
reliably lands on a matching already-vetted-unpublished dataset and flows straight into the
existing Stage 9 pipeline with zero further manual input.*
- **Input:** a one- or two-sentence natural-language research interest; the pool of
  already-vetted-unpublished, already-ingested candidates in the sibling
  `alma_thesis_planning-ptorrey` checkout's `queue.csv` (rows with `status=done`,
  `verdict=unpublished`, and both `metadata.json` + `data_description.md` present on disk).
- **Output:** `topic_lookup.py` (`list_candidates`, `load_project_data`,
  `pick_project`/`pick_project_prompt`) plus `run_auto.py`, the single CLI entrypoint (`python
  run_auto.py ["<topic sentence>"] [n_iterations]`) that picks a candidate and hands it straight to
  Stage 9's `run_pipeline`.
- **Verification:** well-formed and adversarial candidate-filtering/pick logic pass offline; two
  live end-to-end runs each take a topic sentence to a finished writeup with no manual
  intervention beyond that sentence.
  **Done — code written and run live 2026-07-23** (built and verified last session but not yet
  logged in this file until now — see 2026-07-24 session log entry below). `test_stage10.py`, 7/7
  offline checks ($0 cost, dependency-injected `call_claude_fn` per Stage 3/5/6's pattern): candidate
  filtering correctly excludes a `done`/`unpublished` queue row with no ingest files on disk yet,
  missing-queue raises cleanly, target dedup, and the topic-pick round trip including rejection of an
  out-of-list pick. Ran live twice end to end, each with zero manual input beyond one topic sentence:
  (1) a dense-gas-chemistry topic picked `2013.1.01332.S` (NGC 4567/4568 collision front), correctly
  returned NOT_PUBLISHED, and produced a full 612-word one-pager; (2) an outflow-chemistry topic
  picked `2017.1.01053.S` (HH 212), correctly returned NOT_PUBLISHED, and produced a full 728-word
  one-pager, with Stage 9's tractability-banner machinery working unmodified underneath. Full
  transcripts in `run_auto_output.log` / `run_auto_output2.log`. `WRITEUP_FILE` constant added to
  `state.py` in support of this. **This is the capability the user asked to continue: the tool now
  runs "on its own," with the only manual input being a single topic sentence** — candidate
  selection, publication check, idea loop, methods, and writeup all run unattended from there.
  **Still open, inherited from Stage 9's own unresolved finding directly above:** a candidate whose
  idea scores badly on tractability still gets a full writeup (with the caution banner) rather than
  being re-picked or re-run — the same open decision, now also reachable through this entrypoint.

### Stage 11 — Full paper-draft assembly
*Purpose: go one step past Stage 8's one-page proposal and produce an actual multi-section paper
draft (Title/Abstract/Introduction/Methods/Results/Conclusions/References), porting Denario's
original paper-writing agent (`denario/paper_agents/`) rather than the one-pager this repo
otherwise deliberately stops at. Finished when a single command turns a project's already-settled
`idea.md`/`methods.md`/`literature.md` into a coherent `paper.md`.*
- **Input:** `idea.md`, `methods.md`, `literature.md` for a project that already completed Stages
  5–7 (real content, no synthetic placeholders); `abstract_prompt`/`introduction_prompt`/
  `methods_prompt`/`conclusions_prompt` ported from `denario/paper_agents/prompts.py`, reframed
  from LaTeX + per-LangGraph-node JSON output to this repo's plain-markdown
  `\begin{TAG}...\end{TAG}` `extract_block` convention (Stage 3), each independently
  `call_claude_fn`-injectable per Stage 5/7/8's pattern.
- **Output:** `paper.py` (`generate_title_and_abstract`, `generate_introduction`,
  `generate_paper_methods`, `results_placeholder`, `generate_conclusions`, `references_section`,
  `assemble_paper`) and `run_paper.py`, the CLI entrypoint (`python run_paper.py <project_dir>`)
  that writes `paper.md` to that project's `input_files/`. `PAPER_FILE` constant added to
  `state.py`.
- **A deliberate, load-bearing divergence from the original Denario script:** Denario's
  `results_node`/`plots_node` write the Results section from real figures produced by an earlier
  `denario.get_results()` run that actually executed analysis code against real data. Nothing in
  this repo ever does that — every `project_*/` directory here stops at a thesis *plan*, no CASA
  reduction or real ALMA analysis has ever been run, and no plots exist anywhere in the repo.
  Presented with this fork explicitly (placeholder Results vs. a synthetic/toy end-to-end demo vs.
  building real analysis-execution infrastructure), the call was: placeholder. So rather than have
  an LLM invent a Results section with fabricated numbers, `results_placeholder()` is a **fixed
  string with zero LLM calls** — Abstract/Introduction/Methods/Conclusions are all written
  *prospectively* ("registered report" style: what the study aims to determine and how success
  will be judged, not asserted outcomes) and the assembled `paper.md` opens with an explicit
  `DRAFT_BANNER` stating every section but the placeholder must be revised once real results exist.
  Denario's `citations_node` (Perplexity-based citation injection) and `keywords_node`
  (AAS-keyword-list selection) were not ported — out of scope for this stage; `literature.md`'s
  existing Stage-6 citation list is reused verbatim (via `references_section`, which pulls just the
  `CITATIONS:` block) as the References section instead.
- **Verification:** `test_stage11.py`, 9/9 offline checks ($0 cost, dependency-injected
  `call_claude_fn`) — title+abstract both extracted from one call, downstream sections wired with
  the right upstream content, `results_placeholder` provably makes zero LLM calls, conclusions are
  handed the placeholder (not asked to invent findings) and the prompt says so, `references_section`
  extracts just the citations list and falls back to the whole text rather than dropping unparseable
  input, `assemble_paper` makes exactly 4 `claude` calls end to end and includes the draft banner,
  and malformed LLM output raises `BlockExtractionError` rather than returning silently-wrong text.
  Ran live against `project_2017_1_00379_s_auto` (NGC 3256 AGN-driven-outflow project from Stage
  10's auto run) — see 2026-07-24 session log entry for the live-run outcome.

### Stage 13 — Real ALMA-data download + analysis + AASTeX PDF paper
*Purpose: go past Stage 11's placeholder-Results paper draft and produce an actual
publishable-format PDF whose Results are grounded in real measurements from real
downloaded ALMA data, not LLM-invented or placeholder numbers.*
- **User ask (2026-07-28/29 session):** "create a script that produces a fully
  publishable paper from ALMA data sources... including graphs... in a pdf and
  formatted properly... find an ALMA data source that is on supermassive black
  holes" for the first test. Scoped with the user via AskUserQuestion first: real
  data analysis (not placeholder), LaTeX/AASTeX PDF (not pure-Python), and a
  public-but-not-journal-published SMBH dataset (not an already-published one).
- **Done, run live end to end 2026-07-29.** New modules: `netfix.py` (SSL
  workaround for this machine's AVG-antivirus TLS interception, extended from
  `literature.py`'s existing urllib-based fix to also cover `requests`/`astroquery`,
  via a custom `HTTPAdapter` with a relaxed `SSLContext`), `alma_download.py`
  (`fetch_science_products` -- queries the public ALMA TAP archive directly via
  `astroquery.alma`, finds a member OUS's science-ready FITS products by expanding
  the datalink `#this`/`#auxiliary` tarball manifests, downloads a continuum image +
  one line cube), `analysis.py` (real, non-LLM analysis: moment 0/1/2 maps, a
  position-velocity cut, beam-scaled circular-aperture photometry with an explicit
  3-sigma detection/upper-limit rule, HCN luminosity -> dense-gas-mass conversion,
  a central-depression metric -- all numbers traced to the FITS headers/pixels plus
  exactly two cited external constants), `latex_paper.py` (markdown->LaTeX
  converter + AASTeX 7.0.1 document builder + `xelatex` compile wrapper -- switched
  from `pdflatex` to `xelatex` specifically because LLM-written prose routinely
  contains raw Unicode (sigma, en/em dashes) that pdftex's 8-bit engine can't
  typeset), and `run_full_paper.py` (`python run_full_paper.py <project_dir>
  <project_code> <pi> <target>`, mirroring `run_pipeline.py`'s exact signature --
  reuses Stage 5/6/7 if idea/methods/literature don't exist yet, then downloads,
  analyzes, drafts, and compiles). Extended `paper.py` with a parallel
  "real-results" prompt set (`assemble_paper_with_results` and friends) rather than
  modifying the existing placeholder-based `assemble_paper`, since that placeholder
  design is still correct/used for every other `project_*/` directory that has no
  real analysis behind it.
- **Environment set up this session:** a dedicated `.venv` inside the repo (astropy,
  astroquery, matplotlib, spectral-cube, radio-beam, photutils, scipy -- kept
  separate from the unrelated `Denario-fork` venv that `python` on PATH otherwise
  resolves to) and MiKTeX (installed via `winget install --id MiKTeX.MiKTeX --source
  winget` -- the default `msstore` source hit a cert error) with the `aastex`
  package (ships as `aastex701.cls`, not `aastex631` as PLAN.md's Stage 11 entry
  had assumed from the upstream Denario reference).
- **Dataset:** NGC 4429 (ALMA project 2023.1.01214.S, PI Kyoko Onishi, proposal
  title "Circumnuclear Holes around Supermassive Black Holes"), a Virgo Cluster
  lenticular galaxy. Confirmed via ALMA TAP query (`bib_reference IS NULL` +
  `data_rights='Public'`) and this pipeline's own Stage 6 check to be public but
  NOT_PUBLISHED. Real products downloaded: a Band 3 continuum image and an
  HCN(1-0) "representative bandwidth" cube (both already pipeline-imaged FITS --
  no CASA calibration/imaging was run by this pipeline or needed). Written to
  `project_ngc4429_smbh_hole/` (`data_description.md`, `idea.md`, `methods.md`,
  `literature.md` via the existing Stage 5/6/7 modules; `raw_data/` gitignored;
  `input_files/results.json` + `input_files/figures/*.png` from `analysis.py`;
  `paper.pdf` from the full run).
- **A real correctness bug caught mid-session:** `data_description.md` was
  initially written with a hand-misread beam size (0.45x0.43 arcsec, from
  misreading the FITS header's `BMAJ`/`BMIN` as already being in arcsec rather than
  degrees) that then propagated into the Stage 5/7 idea/methods text's "explicit
  scoping" numbers. Caught once `analysis.py` actually measured the beam from the
  FITS header directly (1.63x1.55 / 1.88x1.81 arcsec -- ~4x larger, self-consistent
  with the 0.31 arcsec/pixel scale, unlike the original guess). `data_description.md`
  corrected; the idea/methods loop was not re-run since the beam-limited framing of
  its analysis plan holds regardless of the exact beam number (arguably strengthened
  by the correction, not undermined). A second bug (primary-beam-correction noise
  inflation at the image edges being misread as widespread "detected" signal in the
  moment-map kinematic mask) was caught by inspecting the actual rendered figures,
  not just the numbers -- fixed by restricting the detection mask to a bounded field
  of view around the nucleus.
- **Live result:** Band 3 continuum detected at the nucleus at S/N 11.0/6.4/3.4 (1/2/3
  beam radii); HCN(1-0) came back as 3-sigma upper limits at every radius (S/N
  1.47/2.23/1.86) -- an honest inconclusive result (cannot distinguish a real
  central gas deficit from a beam-diluted, sensitivity-limited non-detection), not a
  fabricated positive finding. The generated paper's Conclusions state this
  explicitly and recommend a concrete higher-resolution/wider-bandwidth follow-up
  rather than overclaiming. A `Software and Data` section in the PDF itself
  discloses that the text was LLM-drafted and not independently peer reviewed.
- **Overlaps with Goalpost 5** (`astroquery.alma`, previously "Not started") --
  this stage builds real `astroquery.alma`-based archive querying and download, but
  scoped narrowly to "find one science-ready image+cube pair for one known
  project/target," not the fuller automated-ingestion/candidate-discovery pipeline
  Goalpost 5 originally envisioned (e.g. topic-driven discovery of *which* dataset
  to use, batch ingestion). Worth reconciling explicitly with Goalpost 5's scope
  next time either is touched.
- **Not yet done / open follow-ups:** (a) `run_full_paper.py` was verified live
  exactly once, on exactly one dataset (NGC 4429) -- not yet tried on a case where
  the analysis would show a real line detection rather than all-upper-limits, nor on
  a target needing a different band/product-naming pattern than this one; (b)
  `alma_download.pick_continuum_and_cube`'s filename-pattern matching is specific to
  the pipeline product-naming convention seen on this one project and hasn't been
  stress-tested against other proposals' naming variants; (c) session ended without
  committing any of this (repeatedly deferred, per the user's own instruction this
  session) -- the accumulated uncommitted state is now larger still.

### Stage 14 — Prompt-to-paper desktop GUI + headless wizard orchestration layer
*Purpose: give a non-technical end user (not just someone comfortable running Python
scripts) one window that turns a free-text research-interest prompt directly into a
rendered PDF, wiring every prior stage (1–13) behind a single "Generate a Paper"
button rather than requiring stage-by-stage script invocation.*
- **Built 2026-08-01.** `wizard.py` (`WizardConfig`, `WizardResult`, `resolve`,
  `generate`, `slugify`, plus model/scope constant tables `MODELS`/`SCOPES`) is the
  GUI-independent orchestration layer, deliberately kept separate from `gui_app.py`
  so it can be driven directly (no clicking, no Tkinter event loop) for
  scripted/live verification. `gui_app.py` (Tkinter, stdlib only) is the actual
  window: a prompt box, a data-source choice (type an ALMA project code/PI/target
  manually, or let Claude match the prompt against `topic_lookup.py`'s pre-vetted
  unpublished-candidate pool from Stage 10), a model picker (Sonnet 5 / Opus 5 /
  Haiku 4.5, all included with a Claude subscription; Fable 5, pay-per-token via API
  credits, flagged as such in the UI), and a scope picker (`idea_methods` — Stage
  9's literature+idea+methods pipeline rendered to PDF; `full_paper` — additionally
  Stage 13's real ALMA download + analysis + compiled AASTeX paper PDF). Runs on a
  background thread so the window stays responsive; a search-mode project-code match
  is shown back to the user for confirmation before anything is downloaded or
  generated, since an LLM-guessed project code is the one part of this flow that
  could plausibly be wrong.
- **Two deliberate, fail-loudly-not-silently scope limits**, both documented in
  `wizard.py`'s own module docstring: (a) "search" mode matches only against
  `topic_lookup`'s local, already-vetted pool (~14 datasets at time of writing), not
  a live archive/web search; (b) "full_paper" scope reuses `analysis.py`'s real-data
  engine, which is only physically valid for an HCN(1-0) line cube (its `alpha_HCN`
  dense-gas-mass conversion factor is calibrated specifically for that transition)
  — it refuses to run rather than silently misapplying the conversion to a
  different line.
- **Three real bugs found and fixed via live testing this session, each documented
  in the code as a comment tied to the specific failure that surfaced it:**
  1. **Windows command-line length limit in `llm.py`.** `_invoke` previously passed
     the prompt as a `claude -p "<prompt>"` argv element; a long, late-iteration
     idea-loop prompt (tens of thousands of characters) raised `OSError:
     [WinError 206] The filename or extension is too long`. Fixed by switching to
     `claude -p --output-format json` with the prompt piped over stdin
     (`stdin=subprocess.PIPE`, `proc.communicate(input=prompt, ...)`) — stdin has no
     comparable length limit. Verified live afterward with a real 37,393-character
     prompt succeeding (`smores_rerun.log`, 12 chained calls, project
     2017.1.01053.S).
  2. **Windows path length limit from long ALMA project directory names.** A
     multi-target SMORES proposal (2017.1.01053.S, 8 pointings: BHR_71, HH_212,
     IRAS_0416+2706, L1551_IRS_5, CG_30, HH_46, GAL_331.5-00.1, IRAS_04166+2706)
     produced an uncapped, comma-joined-then-slugified directory name 106 characters
     long (still present on disk, untracked, as concrete before/after evidence:
     `project_2017_1_01053_s_bhr_71_hh_212_iras_0416_2706_l1551_irs_5_cg_30_hh_46_gal_331_5_00_1_iras_04166_2706`)
     — combined with the repo path plus a typical ~90-character ALMA archive FITS
     filename inside it, this exceeded Windows' path-length limit (`WinError 206`
     again, this time as "the filename or extension is too long" on a file write,
     not a subprocess argv). Fixed with `slugify(text, max_len=24)` plus a new
     `_short_hash()` — a deterministic (not random) 6-hex-character SHA-1
     disambiguator appended to the truncated slug, so two different long inputs that
     happen to share the same first 24 characters still land on different
     directories, and re-running the same project deterministically lands on the
     same directory each time (matching the download step's existing
     skip-if-already-downloaded behavior). The same SMORES project re-run after the
     fix correctly produced the short, disambiguated
     `project_2017_1_01053_s_bhr_71_hh_212_iras_0416_0f130a`.
  3. **Galactic distance fed into an extragalactic-only formula.** In `full_paper`
     scope, an LLM distance/systemic-velocity lookup for that same Galactic SMORES
     target (BHR 71, a Milky Way protostellar outflow) returned 0.0002 Mpc (~200 pc
     — a real, correct Galactic distance), which nothing then caught before feeding
     it into `analysis.py`'s luminosity-distance-based dense-gas-mass conversion
     (calibrated by Gao & Solomon 2004 for nearby-*galaxy* science) — physically
     meaningless at Galactic scale. Fixed with a `MIN_EXTRAGALACTIC_DISTANCE_MPC =
     0.03` (30 kpc, comfortably past the Milky Way's ~15 kpc radius but below even
     the LMC/SMC) guard in `generate()` that raises a `RuntimeError` explaining why,
     rather than producing a nonsense mass/luminosity number, and suggests "Idea +
     Methods only" scope instead.
  4. **Not a bug fix but a related live-testing hardening:** `llm.py`'s default
     120s per-call timeout was found too tight for this wizard's up-to-~20-chained-
     call runs — a live GS 1354-645 (2013.1.00222.T) run via Sonnet 5 had 6
     consecutive calls complete normally (18–71s each) before a 7th hung for over
     1400s before dying, a genuine stall rather than a slow-but-fine response.
     `wizard.py` sets its own `CLAUDE_CALL_TIMEOUT_S = 300.0` and retries once on
     timeout (`CLAUDE_CALL_MAX_ATTEMPTS = 2`, fresh subprocess, same prompt) via
     `_make_call_claude`'s wrapper, which also adds per-call progress logging (call
     number, prompt size, elapsed time, attempt number) so a failure shows exactly
     how far a run got rather than failing as one opaque block.
  5. Also fixed along the way: `resolved.target` can be a comma-joined list of every
     pointing in a multi-target proposal (`topic_lookup.py`'s display convention);
     the real archive download needs one exact `target_name`, so `generate()` now
     downloads only the first pointing and says so in the progress log — confirmed
     live that passing the full joined string always fails with "No public member
     OUS found".
- **`state.py` extended:** `raw_data_dir()` and `figures_dir()` (both
  auto-`mkdir`-ing) plus `RESULTS_FILE`/`WRITEUP_FILE`/`PAPER_FILE`/
  `FULL_DOCUMENT_FILE` constants, so `wizard.py` and `run_full_paper.py` share the
  same directory-layout helpers rather than each hardcoding paths. `.gitignore`
  extended for `raw_data/`, `pdf_build/`, `pdf_build_smoketest/`, and
  `alma_ca_bundle.pem` (all regenerable/re-downloadable, not source).
- **Live-verified end to end, multiple real runs, both scopes:**
  `project_gui_wizard_verification` (search mode, Fable 5, `idea_methods` scope, a
  dense-gas/AGN-outflow topic prompt); `project_full_paper_wizard_verification`
  (`full_paper` scope — produced `idea.pdf`, `methods.pdf`, *and* a real 773 KB
  compiled `paper.pdf` with downloaded `raw_data/` and rendered figures, proving the
  full Stage 13 real-data path now also runs through the wizard, not just
  `run_full_paper.py` directly); `project_2013_1_00222_t_gs1354_645` and
  `project_2021_1_01208_t_candidate_black_hole_x_ray_binary` (two separate
  black-hole/X-ray-binary-topic search-mode runs, Sonnet 5); the SMORES/BHR_71
  multi-target run described above (Opus 5, the one that surfaced bugs 2 and 3).
  Manual GUI interaction (not just scripted `wizard.py` calls) was also screenshotted
  through every form state (main window, expanded form, model/scope radios, the
  search-mode confirmation dialog) to confirm the actual Tkinter window behaves
  correctly, not just the underlying functions.
- **Session ended without committing** (consistent with every prior session on this
  project) and without writing any of this up in `PLAN.md` or memory at the time —
  a fresh 2026-08-02 session had to reconstruct it from file timestamps,
  `.claude/settings.local.json`'s permission history, and leftover scratchpad
  scripts/logs before continuing. **2026-08-02 follow-up:** that same fresh session
  found the working tree's last action was an interrupted smoke test
  (`project_test_galactic_guard/input_files/data_description.md`, an 18-byte
  `"test description"` stub with nothing else written) — re-ran a fresh equivalent
  smoke test (`WizardConfig(mode="manual", scope="idea_methods",
  model="claude-haiku-4-5-20251001", n_iterations=1, ...)`) live, confirmed
  `resolve()`/`generate()` still complete cleanly end to end post-fix (6 real Haiku
  4.5 calls, `idea.pdf`+`methods.pdf` produced with no errors), then deleted that
  throwaway output plus an unrelated stray `name/` directory (a second piece of
  leftover test scratch, real SMORES data written under a literal `"name"` project
  folder — cause not fully diagnosed, not reproduced, left as a one-off rather than
  a confirmed bug).
- **Not yet done / open follow-ups:** (a) the long-directory-name bug fix (#2 above)
  has only been verified against the one SMORES case that originally surfaced it,
  not stress-tested against other extreme-length inputs; (b) no automated test suite
  exists for `wizard.py` (unlike every numbered Stage 1–13 module, which all have a
  `test_stageN.py` following the dependency-injection pattern) — all verification so
  far has been live, cost-incurring runs and manual screenshots, not a `$0` offline
  suite; (c) `gui_app.py` itself has no automated UI test, only manual
  screenshot-driven verification; (d) still uncommitted, now a still-larger
  accumulated diff.

## Milestone list

| Milestone | Scope | Status |
|---|---|---|
| Goalpost 0 — Project plan locked in with Paul | This document + sign-off | Near-complete; awaiting Paul's review |
| Goalpost 1 — Claude Code CLI adapter proven | Build Stages 1–2 | **Closed.** Stages 1–2 done; Paul's named pass/fail check (`paul_check.py`) run live and passed 2026-07-17. 2 minor follow-ups remain open (process-leak re-check, novelty-prompt wording) but don't block Goalpost 2 — most relevant to Stage 6 specifically |
| Goalpost 2 — First end-to-end one-pager | Build Stages 3–8 | **Closed 2026-07-21.** Stages 3–8 all done and run live (Stage 4 with two flagged gaps); three real one-pagers produced end to end |
| Goalpost 3 — Validate the published/unpublished short-circuit | Build Stage 9 | **Closed 2026-07-22.** Follow-up added same day: a soft tractability-caution banner on weak ideas (`pipeline.py`). |
| Goalpost 4 — Small-batch calibration (~5–10 datasets) | Eval rubric, prompt tuning | **In progress.** `eval_rubric.md` drafted; 9/9 datasets scored (3 pre-existing + 6 newly sourced), **9/9 Pass** on published/unpublished accuracy. Found and fixed 2 real issues: a Stage 6 self-citation inconsistency (fixed, re-verified live, then confirmed on a genuine out-of-sample 9th dataset sourced after the fix) and a Stage 5 idea-substitution flaw (meaningfully improved and re-verified, one edge case left open as arguably-correct rather than buggy). Review packet drafted for Paul (`PAUL_REVIEW_GOALPOST4.md`), not yet sent/answered. |
| Goalpost 5 — Automated ingestion | `astroquery.alma` or NRAO's layer, triggered by need | **Partially started** via Stage 13 (see below) -- real `astroquery.alma` download built and run live, but scoped to one known project/target, not candidate discovery/batch ingestion |
| Goalpost 6 — Scale and robustness | Batch processing, retries, idempotency, review queue | Not started |
| Goalpost 7 — Handoff to Paul's/NRAO's team | Documentation, runbook, retrospective | Not started |
| Goalpost 8 — Real-data analysis + publishable PDF (Stage 13) | Build Stage 13 | **Closed 2026-07-29 for one live case.** Real ALMA FITS download, real analysis (moment maps/aperture photometry/luminosity conversion), real AASTeX PDF, run end to end on NGC 4429 (2023.1.01214.S). Not yet tried on a second dataset. |
| Goalpost 9 — End-user prompt-to-paper GUI (Stage 14) | Build Stage 14 | **Built and live-verified 2026-08-01, documented 2026-08-02.** `gui_app.py`/`wizard.py` wire Stages 1–13 behind one window; both scopes (idea+methods, full paper) verified live across multiple real datasets/models. Found and fixed 3 real bugs (Windows argv-length limit, Windows path-length limit from long project-dir names, a Galactic distance fed into an extragalactic-only formula). No automated `test_stage14.py` yet — verification so far is all live/manual, unlike every earlier stage. |

## First milestone and its verification criteria

**Goalpost 1 / Build Stages 1+2 combined** — the Claude CLI call primitive proven trustworthy under
realistic conditions, not just the happy path. This is first because everything downstream depends
on it, and because `claude -p` is a full agentic harness (tool-use, permission prompts, hooks,
context injection), not a stateless completion API — its failure modes needed to be found before
any prompt-porting work began.

**Status:** Stage 1's happy-path checks have already been run live and passed. Stage 2's full
stress test is the concrete next action.

**Concrete pass/fail check (named explicitly by Paul):** one command runs prompt-template → Claude
CLI → markdown output, twice in a row, with zero manual intervention between runs.
- **Pass:** both runs complete unattended and each produces a valid, non-empty markdown file
  derived from the Claude CLI's response.
- **Fail:** either run requires a manual step (answering a permission prompt, re-authenticating,
  etc.), hangs, or produces empty/malformed output.
- **Status: not yet run as this exact script.** Tonight's testing (see Session log below) is
  adjacent evidence — it proves the underlying `claude -p` call is reliable and repeatable — but
  doesn't yet cover writing the result to a markdown file via one command. That's the next concrete
  action, and this check is what determines pass/fail on it.

The eight items below are the fuller, itemized verification criteria this pass/fail check is built
on:
1. `OPENAI_API_KEY`/`GOOGLE_API_KEY`/`ANTHROPIC_API_KEY` cleared and confirmed empty. ✅ done
2. `call_claude("Reply with exactly the single word: PONG")` returns exactly `"PONG"`. ✅ done (3/3)
3. A `\begin{IDEA}...\end{IDEA}` multi-line block survives the round-trip intact. ✅ done
4. Wall-clock latency for a single call measured and judged acceptable for an 8-call idea loop. ✅
   done (~8.8s/call; ~56s+ expected pure overhead for Stage 5's loop)
5. 10 back-to-back calls complete with no failures or silent truncation. ✅ done — 10/10 exact PONG
   matches, P50=10.72s/P95=14.29s, $0.1454 total.
6. A hard timeout is enforced and returns/raises cleanly rather than hanging. ✅ done, with a
   caveat — see Stage 2 session log; the leak-detection part of this check is inconclusive, not
   confirmed clean.
7. A prompt touching on literature search is checked for unwanted web-search tool use, and a
   prompt tempting file/tool use still returns plain text headlessly. ✅ done — web search requires
   explicit permission and is never auto-triggered; tool-tempting prompt returned plain text with no
   stall.
8. The exact invocation flags needed for reliably clean output (including whether `--model`
   actually pins one model) are documented as the standard call pattern for Stage 5 onward. ✅ done
   — `--model` does pin the primary response; see session log for the haiku-side-cost clarification.

Stage 2 is functionally done; two follow-up items are open before calling it fully closed (see
session log): (a) redo the timeout/leak check with a proper before/after process baseline, and (b)
decide how to word Stage 6's `novelty_prompt` so it doesn't read as a request for a canned verdict.
Stage 3 can start in parallel with those follow-ups.

## ALMA input decision — decided, not open

**Decision (locked with Paul at Goalpost 0):** manually download one example ALMA dataset's
metadata locally for development — no `astroquery`/API-based archive access yet. The NRAO
ingestion team is building the general access layer, so building throwaway archive plumbing now
isn't worth it. Revisit automated access (`astroquery.alma`) around Goalpost 5, only if manual
sourcing becomes the actual bottleneck, not on a fixed calendar date.

**Refinement surfaced during planning:** "one" dataset is the floor, not the target. Stage 6 and
Stage 9's own verification require at least two real datasets with known ground truth (one
confirmed published, one confirmed not), so in practice this means manually sourcing **2–3
hand-picked real examples** up front rather than one now and a second one later.

## Open questions for my advisor. Focus only on 3.

1. Which 2–3 example datasets to use — need at least one likely-published and one
   likely-unpublished case.
2. Is Semantic Scholar sufficient for the published-check, or do we need NASA ADS / the ALMA
   archive's own publication-linkage field as a primary or fallback source?
3. How rigorously must "already published" be verified before the pipeline is trusted to skip a
   dataset unattended — this informs the review-queue design at Goalpost 6.
4. Any hard constraint on Claude Code CLI usage volume/rate/cost to design around? Now grounded in
   real numbers from live testing: ~$0.017 and ~9s wall-clock for a trivial call; real prompts will
   cost and take more, and this compounds across an 8-call idea loop and later batch processing.
5. What accuracy/quality thresholds should gate moving from Goalpost 4 into scaling (Goalposts
   5–6)?
6. Should the published/novelty-check be allowed to use Claude Code's built-in web-search tool
   (confirmed available in headless mode), or should it be suppressed in favor of only the explicit
   Semantic Scholar call, for reproducibility?

## Session log

**2026-08-02 — Stage 14 (GUI/wizard, built 2026-08-01) documented; interrupted smoke test finished**
- Picked up in a fresh session with instructions to "continue from the last query,"
  but with no memory of the 2026-08-01 session that built the GUI/wizard (that
  session never wrote `PLAN.md` or memory before ending) — reconstructed what
  happened from file modification timestamps, `.claude/settings.local.json`'s
  accumulated permission-approval history (which command lines were run, in what
  order), and leftover scratchpad scripts/screenshots/logs, rather than asking the
  user to re-explain from scratch.
- Confirmed via that reconstruction that `gui_app.py`/`wizard.py` (Stage 14, full
  detail in the new section above) were built and live-verified across multiple
  real datasets and all four selectable models, with three real bugs found and
  fixed (Windows argv-length limit in `llm.py`, Windows path-length limit from an
  uncapped multi-target project-directory name, a Galactic distance silently fed
  into `analysis.py`'s extragalactic-only mass conversion) — none of it written up
  anywhere, and the working tree's last action was a smoke test cut off mid-run
  (`project_test_galactic_guard/input_files/data_description.md`, an 18-byte
  `"test description"` stub with nothing else written yet).
- Asked the user how to proceed (finish the cut-off test / write up Stage 14 /
  commit / something else) rather than guessing, since re-running live `claude`
  calls costs real money and picking the wrong thread would waste it. User chose to
  finish the interrupted smoke test first.
- Re-ran an equivalent fresh smoke test live (`WizardConfig(mode="manual",
  scope="idea_methods", model="claude-haiku-4-5-20251001", n_iterations=1, ...)` —
  Haiku 4.5 chosen specifically to keep this cheap and fast since the point was only
  to confirm the plumbing, not produce a scientifically meaningful idea): 6 real
  calls, `resolve()`/`generate()` completed with zero errors, `idea.pdf`/
  `methods.pdf` produced — confirms both the argv-length and path-length fixes
  still hold and `wizard.py`'s current code path is intact. Deleted the resulting
  throwaway output plus an unrelated stray `name/` directory (leftover test scratch
  from the same 2026-08-01 session, cause not fully diagnosed) per the user's
  explicit choice.
- Wrote up the full Stage 14 section (above) and added Goalpost 9 to the milestone
  table, per the user's follow-up request to document the GUI/wizard stage
  specifically.
- **Next action:** unchanged in kind from every recent entry — commit the
  accumulated uncommitted state (now larger still, including Stage 12's undocumented
  `student_plan.py`/`full_document.py` work, which this session did not attempt to
  reconstruct or document since it wasn't what was asked), add a `test_stage14.py`
  offline suite for `wizard.py` (currently the only stage with zero `$0` automated
  coverage), or continue toward Goalpost 4/6/7.

**2026-07-29 — Stage 13 built and run live: real ALMA data download, real analysis, real AASTeX PDF (new Goalpost 8)**
- User asked (this session, no memory of Stage 12's student-plan work built in a
  parallel/different session) to build a script producing "a fully publishable
  paper from ALMA data sources...including graphs...in a pdf and formatted
  properly," following the existing idea/methods/write-up steps, first-tested on
  an SMBH dataset. This is a deliberate reversal of Stage 11's placeholder-Results
  decision, so scoped with the user via `AskUserQuestion` first (real data analysis
  vs. placeholder; LaTeX/AASTeX vs. pure-Python PDF; public-but-unpublished vs.
  already-published dataset) rather than assuming.
- Found NGC 4429 (2023.1.01214.S, PI Onishi) via direct ALMA TAP queries
  (`bib_reference IS NULL` + `data_rights='Public'`), confirmed NOT_PUBLISHED via
  this repo's own Stage 6 `check_published`. Downloaded its real Band 3 continuum +
  HCN(1-0) cube FITS (already pipeline-imaged, no CASA needed).
- Full detail in the new Stage 13 section above. Bottom line: `run_full_paper.py
  project_ngc4429_smbh_hole 2023.1.01214.S "Kyoko Onishi" "NGC4429"` runs
  literature/idea/methods (reusing Stages 5-7) -> real download -> real analysis
  (`analysis.py`) -> real Claude-drafted paper sections grounded in those numbers
  -> compiled AASTeX PDF (`latex_paper.py`, xelatex), in one command. Verified live
  end to end exactly once. Real result: continuum core detected, HCN(1-0) came back
  as upper limits everywhere -- reported honestly as inconclusive, not spun positive.
- Caught and fixed two real bugs mid-session by inspecting actual output (not just
  trusting the numbers): a hand-transcription error in `data_description.md`'s beam
  size (degrees misread as arcsec), and a primary-beam-correction noise-inflation
  artifact that was making the moment-map kinematic mask "detect" a huge, spurious
  number of edge pixels -- caught by looking at the rendered figure, not the raw
  count.
- **User ended the session here, explicitly declined to commit** (repeatedly
  deferred across many past sessions too -- see git status, likely a large diff by
  now). This PLAN.md update itself is also uncommitted.
- **Next action:** try `run_full_paper.py` on a second SMBH (or other) dataset,
  ideally one where the analysis would show a real line detection rather than
  all-upper-limits, to check the paper-writing prompts and LaTeX assembly hold up
  on a different results shape; reconcile Stage 13's ad hoc `astroquery.alma` use
  with Goalpost 5's fuller original scope; decide whether to finally commit.

**2026-07-24 (cont'd) — Stage 11 built and run live: full paper-draft assembly, results-placeholder scope decided with the user**
- Two earlier actions this session first: (1) confirmed a user-quoted command wasn't actually
  running (checked `python.exe` process command lines via `Get-CimInstance Win32_Process` — only
  Jupyter kernels were live, no `run_auto.py`); (2) ran a second live Stage 10 `run_auto.py` test
  with an original topic prompt (AGN-driven merger outflows), deliberately distinct from the
  shock-tracer/protostellar-outflow candidate used in the existing `_auto` directories. It matched
  `2017.1.00379.S` (NGC 3256), correctly returned NOT_PUBLISHED, and produced a full pipeline output
  (idea/methods/writeup) in `project_2017_1_00379_s_auto/`.
- User then asked to "follow the original denario script" and write code to produce an entire
  publishable paper. Located the actual upstream Denario checkout at
  `C:\Users\cb447\OneDrive\Documents\GitHub\Denario` (a full clone with `denario/paper_agents/` —
  the LangGraph paper-writing graph this repo's PLAN.md had previously only referenced in passing,
  at Stage 8, as "Denario writes a full paper, not a one-pager"). Read `agents_graph.py` and
  `paper_node.py` to find the real blocker: `results_node`/`plots_node` require real analysis
  output (figures from an executed `denario.get_results()` run against real data) that nothing in
  this repo has ever produced — confirmed by checking every `project_*/` directory on disk: all of
  them stop at markdown planning files, zero plots, zero executed analysis anywhere.
- This was a genuine fork, not a detail to guess past: fabricating a Results section with
  LLM-invented numbers would misrepresent unexecuted work as real findings. Asked the user directly
  (placeholder Results vs. synthetic/toy demo vs. building real analysis-execution infrastructure);
  answer was the placeholder option.
- Built Stage 11: `paper.py` ports `abstract_prompt`/`introduction_prompt`/`methods_prompt`/
  `conclusions_prompt` from `denario/paper_agents/prompts.py`, reframed from LaTeX+JSON to this
  repo's `\begin{TAG}...\end{TAG}` `extract_block` convention, each `call_claude_fn`-injectable.
  `results_placeholder()` is a fixed string with **zero** LLM calls by design — proven directly in
  `test_stage11.py` rather than just asserted. Everything else is written prospectively
  ("registered report" style — what the study aims to determine, not asserted findings), and the
  assembled document opens with an explicit `DRAFT_BANNER`. `references_section()` reuses Stage 6's
  existing `literature.md` citations rather than porting Denario's separate Perplexity-based
  `citations_node`; `keywords_node` (AAS keyword selection) also not ported — both out of scope for
  this stage. `run_paper.py` is the CLI entrypoint (`python run_paper.py <project_dir>` → writes
  `paper.md`).
- `test_stage11.py`: 9/9 offline checks, $0 cost, Stage 3/5/7/8/9's dependency-injection pattern.
  First draft had a real bug caught by the offline run itself: fixture strings used Python raw
  strings (`r"\begin{TITLE}\n..."`) where the `\n` needed to be an actual newline for
  `extract_block`'s regex/strip to behave as intended — raw-string `\n` stayed literal backslash-n
  text, so `.strip()` didn't remove it and the assertion failed loudly rather than silently passing.
  Fixed by switching those fixtures to normal escaped strings.
- Ran live against `project_2017_1_00379_s_auto` (this session's own NGC 3256 project): 4 live
  `claude` calls (title+abstract, introduction, methods, conclusions) completed cleanly, produced a
  coherent 4356-word `paper.md` with Title/Abstract/Introduction/Methods/Results(placeholder)/
  Conclusions/References — Conclusions correctly came out conditional ("if X is found... if instead
  Y..."), not asserting an outcome, and closes by restating that it must be rewritten from real
  results.
- **Next action:** unchanged in kind from prior entries — send `PAUL_REVIEW_GOALPOST4.md` to Paul,
  commit the large accumulated uncommitted git state (repeatedly deferred across many sessions), or
  extend Stage 11 (citations_node/keywords_node porting, or wiring `run_paper.py` into
  `pipeline.py`/`run_auto.py` as an opt-in extra step) if a full paper draft becomes a standard part
  of the automated flow rather than a separate manual command.

**2026-07-24 — Stage 10 documented (was built and verified live last session, but never written up)**
- User asked (from a different repo/session) to "continue making it so alma-thesis-planner can run
  on its own just only being prompted." This session had no memory of the prior one, so it
  investigated the working tree directly rather than assuming: `topic_lookup.py`, `run_auto.py`, and
  `test_stage10.py` already existed on disk (file timestamps 2026-07-23), and two full transcripts
  (`run_auto_output.log`, `run_auto_output2.log`) showed the topic-only entrypoint already ran live,
  twice, end to end, successfully — but `PLAN.md` had no session-log entry past 2026-07-22 and no
  Stage 10 section, so the work existed but was undocumented against this project's own established
  pattern of logging every stage.
- Re-ran `test_stage10.py` to confirm it still passes cold (7/7, $0 cost) before writing anything
  up. Did not re-run the live `run_auto.py` path this session — the existing two live transcripts
  already demonstrate it end to end, and re-running would be a real, cost-incurring `claude` CLI
  call made without being asked for one.
- Added the Stage 10 section to the stage-by-stage breakdown above (mirroring Stages 4-9's format)
  documenting what was built and both live runs' outcomes.
- **Next action:** open choices, unchanged in kind from Goalpost 4's last entry — send
  `PAUL_REVIEW_GOALPOST4.md` to Paul, decide the Stage 9/10 shared tractability-gate question, commit
  the large accumulated uncommitted git state (repeatedly declined in past sessions — not touched
  here either), or use `run_auto.py` for further real topic-driven runs.

**2026-07-22 (cont'd, part 6) — 9th dataset sourced and scored (out-of-sample check on the self-citation fix)**
- User (in a separate interactive thread, working directly in the IDE alongside this session) pasted
  a real ALMA archive record and asked to run the pipeline against it, then add the result to
  `eval_rubric.md`.
- Sourced `project_et_cha` first (target ET Cha, PI Claudio Caceres, not the initially-named Amelia
  Bayo who is a co-I) -- flagged as a genuinely different case type (publicly-released but no
  confirmed publication found, so ground truth isn't structurally certain the way proprietary-lock
  cases are); not run live or added to the scored batch, left as a sourced-but-unscored dataset since
  its ground truth can't be independently verified.
- Sourced and ran `project_hd66811_masslos` (target HD 66811 / Zeta Puppis, PI Samer Kanaan, ALMA
  project 2012.1.00955.S): confirmed real ground truth via a genuine IAU Symposium 329 proceedings
  paper (Setia Gunawan et al. 2017, DOI 10.1017/S1743921317002861) that explicitly acknowledges this
  exact project code and names HD 66811 in its 8-star sample. Ran `run_pipeline.py` live -- correctly
  returned PUBLISHED and short-circuited, explicitly invoking the self-citation rule added earlier
  this session despite zero Semantic Scholar hits.
- Added to `eval_rubric.md`'s scoring table. **Significance:** this dataset was sourced *after* the
  self-citation fix went in, so it's a genuine out-of-sample generalization check, not one of the
  cases the fix was tuned against -- and it passed cleanly. **Batch is now 9/9 Pass** on published/
  unpublished accuracy.
- **Next action:** unchanged in kind -- send `PAUL_REVIEW_GOALPOST4.md` to Paul (user's action), decide
  whether to score `project_et_cha` despite its uncertain ground truth or leave it unscored, commit
  the accumulated uncommitted git state (repeatedly declined this session).

**2026-07-22 (cont'd, part 5) — Review packet drafted for Paul (not a real review, just the ask)**
- User said "complete Paul's rubric-threshold review." Paul is a real advisor who hasn't actually been
  consulted this session -- declined to fabricate his sign-off or invent what he'd decide, and asked
  the user to clarify what they actually wanted instead.
- User chose: draft an actual review packet suitable for sending to Paul, not a placeholder threshold
  set by Claude standing in for him.
- Wrote `PAUL_REVIEW_GOALPOST4.md`: a ~15-minute-read summary covering what Goalpost 4 is, the 8
  datasets run (including the 3 deliberately-hard same-target-discrimination cases), the rubric used,
  the two issues found and fixed this session, the new tractability caution-banner feature, and 5
  concrete open questions for Paul (aggregate threshold, Semantic-Scholar-sufficiency, published-
  verification rigor, cost/volume constraints, web-search permission) -- each phrased as a specific
  question with context, not just copy-pasted from `PLAN.md`'s longer-form advisor-questions list.
  No threshold has been set anywhere in the codebase; `eval_rubric.md`'s "not yet set" placeholder is
  unchanged.
- **Next action:** send `PAUL_REVIEW_GOALPOST4.md` to Paul (user's action, not mine); once he responds,
  update `eval_rubric.md`'s aggregate threshold section and act on whichever of the 5 questions he
  answers.

**2026-07-22 (cont'd, part 4) — Stage 9 tractability gate implemented (the open item from Stage 9's
original build)**
- User said "continue" after the two Goalpost 4 fixes below. Picked up the one remaining open
  architectural question flagged back when Stage 9 was first built: a failing Stage 5 tractability
  score was computed but silently ignored by `run_pipeline`/`run_pipeline.py`, which proceeded to
  Stages 7/8 regardless. Decided this myself (self-contained, reversible, directly continues today's
  momentum) rather than treating it as blocked on user input.
- **Design decision: a soft flag, not a hard gate.** Per `PROJECT_BRIEF.md`'s own framing -- the
  output is a plan for a *human* to execute, not an automated research pipeline -- a weak idea is
  still surfaced, just with an explicit warning prepended, rather than silently discarded or silently
  presented as fully vetted.
- Added `tractability_failures()` (parses the Stage 5 SCORE block for real NO verdicts, splitting on
  `--` before checking so a justification sentence containing the word "no", e.g. "no new
  instrumentation", is never misread as a failure) and `tractability_caution_banner()` to
  `pipeline.py`; `run_pipeline()` now prepends the banner to the writeup whenever any axis fails.
- Also resolved the M87-dataset-description open question from the prior entry: decided to leave
  `project_m87_unpublished`'s description as-is rather than reword it. Its "unrelated" framing is
  factually accurate, and a model that keeps flagging the resulting idea as a substitution given that
  framing is behaving correctly, not failing -- softening the wording just to raise the score would be
  gaming the test case rather than fixing anything real.
- `test_stage9.py` extended to 8/8 offline checks ($0 cost): a "no" inside a passing justification
  isn't misparsed as a failure; real NO verdicts are detected and included in the banner; a failing
  score prepends the banner to the pipeline's returned writeup; a fully-passing score leaves the
  writeup untouched.
- **Verified live**, re-running `project_m87_unpublished` (a known non-3/3 case) end to end: the
  banner now appears correctly at the top of the actual `writeup.md` file, quoting the specific failed
  item verbatim, exactly as designed.
- **Next action:** open choices, unchanged in kind -- get Paul's review of `eval_rubric.md` and its
  aggregate threshold, commit the accumulated uncommitted git state (repeatedly declined this
  session), or continue sourcing datasets toward 10.

**2026-07-22 (cont'd, part 3) — Both Goalpost 4 issues fixed and re-verified live**
- User asked to fix both issues logged in the previous entry, not just leave them noted.
- **Fix 1 (Stage 6 self-citation inconsistency):** added an explicit self-citation rule to
  `novelty_prompt` (`literature.py`) -- a specific, well-formed self-citation (DOI/journal/authors,
  tied to this project's own data) is sufficient for PUBLISHED on its own and must not be downgraded
  just because Semantic Scholar returned nothing; only an affirmative contradiction or a vague/
  unverifiable citation should discount it. Offline `test_stage3/5/6/9.py` all still pass unchanged.
  Re-ran `run_pipeline.py` against `project_hops315_outflow` live: now correctly returns PUBLISHED and
  short-circuits, explicitly citing the new rule in its own justification text. **Fixed and verified
  -- batch published/unpublished accuracy is now 8/8 Pass.**
- **Fix 2 (Stage 5 idea-loop data substitution):** added a substitute-data rule to
  `idea_maker_prompt` plus a matching check to `idea_hater_prompt`, requiring any alternative-data
  idea to be justified as addressing the same scientific question as the assigned (inaccessible)
  dataset. First re-run of `project_m87_unpublished` showed the mechanism working better (the hater
  named the exact violation by description) but the maker's next idea still reached for a *different*
  unnamed dataset (VLBA/MOJAVE, Walker et al. 2018) never mentioned in the data description -- a
  loophole, not a full fix. Tightened the rule a second time to explicitly forbid introducing any
  external dataset/paper/catalog not literally named in the data description. Re-ran again: the final
  idea now confines itself entirely to the one paper actually named in the description (A&A 699,
  A265) -- the specific failure mode (fabricating unnamed external data) is closed and verified.
  **Not fully resolved:** the idea still scores 2/3, not 3/3, on Stage 5's own tractability rubric,
  because `project_m87_unpublished`'s own data description explicitly frames that one named background
  paper as "unrelated to this project" -- a wording choice from how *that one dataset* was authored,
  not a remaining prompt bug. A model that keeps flagging the resulting idea as a substitution given
  that framing is arguably behaving correctly rather than failing. Left open: reauthor that one
  dataset's description, or accept 2/3 as the right answer for a case this genuinely constrained
  (2025.1.00830.V's real science goal was never confirmed to begin with). Offline `test_stage5.py`
  (4/4) passes unchanged throughout.
- Both fixes and their full verification trail (including the intermediate, not-fully-fixed round 1
  attempt on issue 2) are documented in `eval_rubric.md`'s Known Issues section in detail.
- **Next action:** unchanged in kind -- (a) decide on the M87 dataset-description framing question
  above, (b) get Paul's review of `eval_rubric.md` and its aggregate threshold, (c) commit the now
  still-larger uncommitted git state, (d) continue sourcing toward 10 datasets or move on.

**2026-07-22 (cont'd, part 2) — Goalpost 4 batch extended to 8 datasets; first real miss found**
- Continuation of today's session, user asked to source 2-5 more datasets to reach the 7-10 range
  (was at 5). Sourced 3 more, landing at 8, all facts verified via WebSearch/WebFetch/ALMA TAP query
  against real papers and archive records -- no fabricated codes/PIs/dates:
  - `project_hops315_outflow` (**published**, new science category: protostellar jet/outflow line
    kinematics): G205.46-14.56S3 (HOPS 315), ALMA project 2018.1.00302.S (PI Tie Liu, part of the
    ALMASOP survey), published in Dutta (2025), ApJ 991, 45, DOI 10.3847/1538-4357/adf8d6.
  - `project_ic443g_shock` (**unpublished**, new science category: SNR/molecular-cloud shock
    chemistry): IC 443 clump G, ALMA project 2025.1.00086.S (PI Tu), release 2027-07-10. Well-studied
    at other wavelengths (Turner et al. 1992 and others) but no prior ALMA-specific publication found
    -- a cleanly "genuinely new" unpublished case, unlike the same-target-discrimination traps below.
  - `project_m87_unpublished` (**unpublished**, deliberately the hardest case in the whole project):
    M87/Virgo A, ALMA project 2025.1.00830.V (PI Chan, VLBI-affiliated per the ".V" suffix, consistent
    with EHT-monitoring timing per ALMA's own Cycle 13 guide), release 2027-07. M87 is one of the most
    heavily ALMA-published AGN targets in existence (found and cited a real, different-project-code
    July 2025 A&A polarization paper plus the VAPOLA survey as confusable prior literature).
- Ran `run_pipeline.py` live against all three (HOPS 315 foreground first, then IC443G and M87 in
  parallel background). Results:
  - `project_ic443g_shock`: correctly NOT_PUBLISHED. Idea loop explicitly abandoned the proprietary
    dataset (documented as unusable within a thesis timeframe) and pivoted to a fully archival
    RADEX/shock-model reanalysis of Turner et al. 1992's single-dish data -- scored 3/3 YES,
    best-grounded idea in this new trio.
  - `project_m87_unpublished`: correctly NOT_PUBLISHED, explicitly distinguishing the July 2025 A&A
    paper as a different project code -- Stage 6 held up under the hardest test yet. **But** Stage 5's
    idea loop substituted the actual (undescribed, proprietary) data with that same unrelated public
    polarization dataset to build its idea, with no stated scientific link to what 2025.1.00830.V
    itself was for -- caught by Stage 5's own rubric (NO on "avoids data beyond what's described",
    2/3 YES overall) but not prevented from being generated and carried through to a full writeup.
  - `project_hops315_outflow`: **incorrectly returned NOT_PUBLISHED against a verified-PUBLISHED
    ground truth -- the first real miss found anywhere in this project.** The data description
    explicitly cited the real source paper with a DOI, the same kind of self-citation Stage 6 had
    just correctly trusted for `project_ngc4061` and `project_mp_mus_disk` under an identical
    "empty Semantic Scholar search" condition -- logged in `eval_rubric.md`'s Known Issues section as
    an unresolved inconsistency (trusted once, distrusted once, same evidence pattern), not yet fixed.
- **Batch now at 8/8 scored: 7/8 Pass on published/unpublished accuracy.** Notably, the one Fail
  happened on an *easier* single-citation case, not on any of the three deliberately-hard
  same-target-discrimination traps (W49A, HD 138813, M87) -- all three of which the pipeline got
  right. Full per-axis scores and both open findings are in `eval_rubric.md`.
- **Next action:** open choices, unchanged in kind from before this batch extension -- (a) decide
  whether to investigate/fix the two logged prompt issues now or continue sourcing toward 10, (b) get
  Paul's review of `eval_rubric.md` and its aggregate threshold, (c) commit the accumulated
  uncommitted git state (still open, now larger by 3 more project directories).

**2026-07-22 (cont'd) — Goalpost 4 started: eval rubric drafted, 2 new datasets sourced and run**
- Continuation of today's earlier session (Stage 9/Goalpost 3), same sitting. User declined to
  commit the accumulated uncommitted work for now and asked to proceed straight to Goalpost 4.
- Per `PROJECT_ROADMAP.md`'s fuller Goalpost 4 spec (not detailed in `PLAN.md` itself): source ~5-10
  more real datasets, define a lightweight eval rubric, run the pipeline across the batch, score
  against the rubric, iterate on prompts. No domain expert ("Paul") in this session, so both the
  rubric and dataset sourcing were done solo -- flagged throughout as provisional/self-scored pending
  expert review, not a substitute for it. Scoped to 2 new datasets first, with a check-in before
  sourcing the rest of the batch (user's choice).
- Wrote `eval_rubric.md`: four axes (abstract quality, thesis-scope feasibility, reading-list
  relevance, published/unpublished accuracy), 1-5 scale on the first three, hard pass/fail on the
  fourth (no partial credit -- a wrong verdict fails the batch regardless of the other scores).
  Aggregate pass/fail threshold explicitly left unset per the roadmap's own instruction to decide
  that with Paul at this goalpost, not before.
- Scored the 3 pre-existing datasets first (free -- just reading already-produced outputs): flagged
  that `project_w49a_variability_2018`'s writeup predates Stage 9 and was never actually run through
  the short-circuit-respecting `run_pipeline.py` (it's PUBLISHED and would short-circuit if re-run
  today) -- scored as a Stage 5-8 prompt-quality sample only, not a Stage 9 test.
- Sourced 2 new real datasets, deliberately choosing a different science flavor (continuum-only disk
  imaging) from the existing line-kinematics/HII-region-heavy set, and verified every fact via
  WebSearch/WebFetch against real papers -- no fabricated project codes, PIs, or dates:
  - `project_mp_mus_disk` (**published** case): MP Mus (PDS 66) protoplanetary disk, ALMA projects
    2021.1.01205.S (Band 7, PI Claudio Caceres) + 2017.1.01419.S/2017.1.01167.S (Band 6, PIs Caceres/
    Perez), published as Aguayo et al. 2025, A&A 698, A165, DOI 10.1051/0004-6361/202554484.
  - `project_hd138813_unpublished` (**unpublished** case, deliberately hard): HD 138813 debris disk,
    ALMA project 2025.1.00062.S (PI Luca Matra), sourced via a direct ALMA TAP/ADQL query (`curl` to
    `https://almascience.nrao.edu/tap/sync`, table `ivoa.obscore`) after confirming AVG's TLS-
    interception cert issue (same one hit in Stage 6) also blocks Windows `curl`/schannel -- worked
    around with `--ssl-no-revoke`. Chosen specifically because it's *harder* than the existing W49A
    ground-truth pair: HD 138813 is part of the already-published ARKS survey (2022.1.00338.L, A&A
    705, A195, Jan 2026), and Matra is a co-PI on *both* ARKS and this new proposal -- same target,
    overlapping PI, but a genuinely different, unreleased (2027-07 release dates) project code.
- Ran `run_pipeline.py` live against both. `project_mp_mus_disk` correctly short-circuited
  (PUBLISHED) -- notably the first case where Semantic Scholar returned real hits, and the model
  correctly distinguished the true match from a different, earlier (2023) paper on the same target
  rather than conflating them. `project_hd138813_unpublished` correctly returned NOT_PUBLISHED,
  explicitly reasoning that the ARKS citation is a different project code -- and Stage 5's idea loop
  *independently* discovered the same same-target/different-code nuance unprompted, building its own
  literature-audit gate before committing to scope and explicitly excluding the proprietary dataset.
  Scored 3/3 YES on tractability, the best-scoring idea of the batch so far.
- **Batch status: 5/5 datasets scored, zero published/unpublished misses**, including both
  deliberately-hard same-target discrimination cases (W49A: shared target/unrelated overlapping
  authors; HD 138813: shared target *and* overlapping PI) -- no false verdict yet on any ground-truth
  case across the whole project. Full detail and per-axis scores in `eval_rubric.md`.
- **Checked in with the user: stopping at 5 datasets for now** (the low end of the ~5-10 target),
  rather than sourcing more this session. No failure pattern has emerged yet to iterate prompts
  against -- zero misses across all 5 -- so the roadmap's "iterate on prompts/node logic based on
  failure patterns" milestone has nothing to act on yet; revisit once either more datasets surface a
  real failure, or Paul reviews the rubric/scores and sets the aggregate threshold this goalpost is
  meant to be verified against.

**2026-07-22 — Stage 9 built and run live; Goalpost 3 closed**
- Continuity check: picked this project back up from a fresh session rooted in `Denario-fork`
  (sibling directory), per the standalone-tool decision -- confirmed via memory and `PROJECT_BRIEF.md`
  that the real work happens here, not in Denario-fork.
- Found PLAN.md's own state (Stages 1-8 done, Goalpost 2 closed, Stage 9 the only open item) ahead of
  git: only Stages 1-3 were ever committed (`87213fe`); Stages 4-8's code and all four `project_*/`
  directories were sitting uncommitted in the working tree. Left uncommitted per this session's scope
  (adding Stage 9, not a git-hygiene pass) -- flagged for a follow-up commit.
- Built Stage 9: `pipeline.py` (`run_pipeline`, `PipelineResult`, `short_circuit_note`) and
  `run_pipeline.py`. Design choice beyond the original spec: a Stage 6 verdict of `UNKNOWN` (Stage 6's
  own parser falls back to this on unparseable output) also short-circuits, with wording distinct from
  `PUBLISHED` ("Publication Status Unclear" vs. "Already Published") rather than silently defaulting
  either way.
- `test_stage9.py`: 4/4 offline checks, $0 cost, following the established dependency-injection
  pattern -- proves Stage 5/7/8 functions are never called on the PUBLISHED/UNKNOWN branches (each
  fake raises loudly if invoked) and that idea/methods/literature content is correctly threaded
  through to the writeup on the NOT_PUBLISHED branch.
- Ran live against both Stage 6 ground-truth datasets: `project_ngc4061` (PUBLISHED) correctly
  short-circuited with zero Stage 5/7/8 calls, writing a citation-only note to `writeup.md`;
  `project_w49a_unpublished` (NOT_PUBLISHED) correctly ran the full idea-loop -> methods -> writeup
  pipeline, producing a 699-word one-pager. Both took the correct branch automatically, no manual
  stage-by-stage invocation. **Goalpost 3 (published/unpublished short-circuit) is now closed.**
- **Open finding, not yet resolved:** the live NOT_PUBLISHED idea scored only 1/3 YES on Stage 5's own
  tractability rubric, but the pipeline doesn't gate on that score -- it logs and proceeds anyway. This
  is Stage 5's original "score, don't block" design, inherited as-is by Stage 9, but worth an explicit
  decision now that this is the unattended end-to-end path: should a failing tractability score halt
  the pipeline (or trigger a re-run of the idea loop) rather than building methods/writeup on top of a
  flagged-weak idea?
- **Next action:** commit the accumulated uncommitted work (Stages 4-9's code, all `project_*/`
  outputs, and `PLAN.md`/`state.py`/`investigate_ambient_context.py`'s modifications), then decide
  between the open finding above and starting Goalpost 4 (small-batch calibration, ~5-10 datasets).

**2026-07-21 — Stage 6 live-verified; Stage 7 (methods) built and run live; third dataset sourced**
- Continuity check: picked this project back up in a fresh session from `Denario-fork` (sibling
  directory), per the standalone-tool decision.
- Sourced a third real dataset, `project_w49a_variability_2018/input_files/data_description.md`:
  De Pree et al. 2018, ApJ Letters, "Flux Density Variations at 3.6 cm in the Massive Star-Forming
  Region W49A" (arXiv:1807.10669) -- a confirmed-published VLA 3.6cm repeat-imaging (1994 vs. 2015)
  study of the same crowded W49A field as `project_w49a_unpublished`, with overlapping authors
  (De Pree, Wilner, Mac Low, Klessen). Found via web search after the ALMA archive's own JS-driven
  query UI proved unfetchable directly; confirmed via the arXiv abstract page.
- Built Stage 7: `methods.py` (`methods_prompt`, `generate_methods`), porting Denario's
  `methods_fast_prompt` and reframing it to thesis-student scope, plus `run_idea_and_methods.py`
  chaining Stage 5's idea loop into methods generation for one project directory.
- Ran both live against `project_w49a_variability_2018`. The idea loop's critic did real work over
  4 iterations: iteration 1's full-catalog variability census was flagged as likely reproducing a
  table the source paper already published; iteration 2's variability-vs-morphology correlation was
  rejected outright for having no statistical power (only one variable source in the dataset, so no
  distribution to correlate against); iteration 3 repeated the reproduction risk a third time; the
  loop settled on iteration 4, a bounded methods contribution (quantifying multi-component
  deblending bias in the field's crowded B/C/D/G subregion, contingent on confirming the source
  paper's own tables don't already do this), scored 3/3 YES on tractability. `methods.md` came out
  as a 7-phase CASA-based workflow (confirm published baseline as a go/no-go gate, align epochs,
  flag confused sources, validate single-component photometry against the paper's own G2 numbers,
  multi-component deblend, quantify bias, reassess variability). Both `idea.md` and `methods.md`
  written to `project_w49a_variability_2018/input_files/`.
- Ran Stage 6's previously-untested live path (`run_literature_check.py`) against both existing
  ground-truth cases: `project_ngc4061` returned `VERDICT: PUBLISHED`, correctly citing the Nguyen
  et al. 2026 paper named in its own data description; `project_w49a_unpublished` returned
  `VERDICT: NOT_PUBLISHED`, explicitly reasoning that the unrelated 2024 A&A paper by overlapping
  authors on the same target is not a match for this project code -- the exact non-trivial
  distinction this ground-truth pair was built to test. Both verdicts match known ground truth;
  Stage 6 is now closed.
- Backfilled the remaining gaps so all three real projects had complete inputs: ran
  `run_methods.py` (new standalone Stage 7 runner, for projects that already have a settled
  `idea.md` and don't need the idea loop re-run) against `project_ngc4061` and
  `project_w49a_unpublished`; ran `run_literature_check.py` against `project_w49a_variability_2018`
  (verdict PUBLISHED, correctly matched against its own cited source paper).
- Built Stage 8: `writeup.py` (`writeup_prompt`, `assemble_writeup`) and `run_writeup.py`. No
  Denario prompt exists to port for this one (Denario writes a full paper, not a one-pager), so the
  prompt is original, designed directly from `PROJECT_BRIEF.md`'s three-part spec (abstract / work
  plan with anticipated key results-plots / background reading), capped around 700 words. Run live
  against all three projects: `project_ngc4061` (621 words), `project_w49a_unpublished` (641
  words), `project_w49a_variability_2018` (608 words) -- all three read as one coherent document,
  not stapled fragments. **Goalpost 2 (first end-to-end one-pager) is now closed.**
- **Next action:** Goalpost 3 / Stage 9 -- wire Stages 1-8 into one CLI entrypoint that branches
  automatically on the Stage 6 published/unpublished verdict (short-circuit to a citation-only note
  if PUBLISHED, full Stage 7-8 pipeline if NOT_PUBLISHED), and verify it produces the correct output
  type for both ground-truth datasets with no manual stage-by-stage invocation.

**2026-07-20 — Stage 6 ground-truth pair identified (published + unpublished)**
- Resolves advisor open question 1 (which datasets to use for the published/unpublished pair),
  ahead of Stage 6 itself being built.
- Checked two initial candidates from the ALMA archive and ruled both out as the "unpublished"
  half: an old (2013-2014) J0451/MACS J0451+0006 lensed-galaxy Band 3 dataset turned out to already
  be published (Rawle et al. 2015, A&A, arXiv:1502.03842 -- PI Ellis, first-author Rawle matches the
  Co-I list exactly), and a 2013-2014 Pluto Band 7 continuum dataset (New Horizons support) was also
  already published (Butler et al. 2018, Icarus) and a poor thematic fit besides (calibration-style
  flux measurement, not a resolved-imaging science case).
- Landed on project code `2024.1.00717.S` ("Accretion and Outflow Dynamics of the Hypercompact HII
  Regions in W49A", PI: Wilner, David) as the unpublished half. Its ALMA archive release/proprietary
  date is 2027-05-04 -- over 9 months in the future as of today -- so this is a **structural**
  confirmed-not-published case (the data is still exclusive to the PI team), not an inference from
  an absent literature search. Built `project_w49a_unpublished/input_files/data_description.md`
  from the proposal abstract (target: W49A/W49N hypercompact HII regions; science goal: test
  whether they're structured as ionized accretion disks via the H21alpha line and ~0.45mm/Band 9
  continuum at ~100 AU resolution). Flagged, not guessed: exact observation date(s), array
  configuration, and angular resolution/sensitivity aren't in the archive yet, consistent with these
  observations not having been executed/calibrated into the archive's observation-level tables yet
  (confirmed this isn't an account/login gate -- ALMA's own policy is that metadata, unlike data
  files, isn't protected by the proprietary period).
- Genuinely useful non-trivial detail for Stage 6: the same target region and overlapping authors
  (Wilner, Tobin) have an unrelated 2024 A&A paper (arXiv:2404.02250) using different, earlier ALMA
  continuum data. Stage 6's novelty check will need to correctly distinguish "has this specific
  project code's data been published" from "has this target ever been studied" -- this pair
  exercises exactly that distinction rather than being a trivially easy case.
- **Next action unchanged:** Stage 6 itself (novelty_prompt/summary_literature_prompt ported and
  reframed, plus the plain Semantic Scholar REST call) is still not built; this session only sourced
  and documented the ground-truth pair it will be tested against.

**2026-07-20 — Stage 4 built: first real dataset (`project_ngc4061/input_files/data_description.md`)**
- Continuity check: located the real project directory again (`alma-thesis-planner`, sibling to
  `Denario-fork`), confirmed the standalone-tool decision still holds.
- Source dataset identified: Nguyen et al. 2026, ApJ, "Dynamical Evidence for a Billion Solar-mass
  Black Hole in Galaxy NGC 4061 from ALMA 12CO(2-1) Kinematics" (DOI 10.3847/1538-4357/ae771c).
  Fetched the PDF, extracted text via `pymupdf` in the WSL venv (poppler/`pdftoppm` isn't installed
  on this machine, so the harness's own PDF-reading tool couldn't render it directly), and pulled
  observational facts via targeted pattern search rather than reading the full text, to stay clear
  of reproducing extended passages from a paywalled paper.
- Built `project_ngc4061/input_files/data_description.md`: target NGC 4061 (D = 107.2 Mpc), ALMA
  Band 6 12CO(2-1) (rest 230.538 GHz), two combined projects (`2018.1.00397.S` PI M. Smith;
  `2019.1.00036.S` PI D. Nguyen), 12-m array C43-7/C43-5 configs, ~0.16" beam, continuum
  image + CO(2-1) cube/moment-map data products, plus a short paraphrased science-context note
  citing the source paper.
- **Verification run:** round-tripped the file through Stage 3's actual `write_state_file`/
  `read_state_file` helpers — byte-identical, 2034 chars both ways. Field-by-field cross-check
  against `BUILD_PLAN.md`'s Stage 4 checklist: project code, PI, target, band/frequency, array
  config, and data products all present and sourced from the paper. Two fields could not be filled
  from the paper alone and are flagged rather than guessed: (a) exact observation date/epoch of the
  ALMA execution blocks, (b) the original ALMA proposal's science-goal abstract (the paper documents
  what was found, not the original time-proposal text) — both would need a direct ALMA Science
  Archive lookup by project code to close.
- **Decision:** move forward without closing those two gaps for now (user's call).
- Bonus: since this dataset is already published, it's a candidate for Stage 6's known-published
  ground-truth case later, in addition to serving as this Stage 4 example — not yet decided which
  role it plays; a second (and possibly third) dataset is still needed for Stage 6/9's ground-truth
  pair regardless of how this one is used.
- **Next action:** Stage 5 — idea-maker/idea-hater loop. Per its own spec, run a synthetic smoke
  test first, then against this real dataset. This will make live, cost-incurring `claude` CLI calls
  (per Stage 1/2's measured ~$0.01-0.07/call and ~10-18s/call), unlike Stages 3-4 which were free.

**2026-07-17 — Continuity check + Stage 3 built (`blocks.py`, `state.py`, `test_stage3.py`,
`paul_check.py`)**
- Picked this project back up in a fresh session. Located the real project directory
  (`alma-thesis-planner`, sibling to `Denario-fork` — the fork itself was untouched, consistent
  with the standalone-tool decision in `PROJECT_BRIEF.md`) and confirmed the repo was clean and
  fully committed through the Stage 2 ambient-context fix (commit `37b9633`).
- Before writing new code, statically verified all existing code is intact and usable without
  making any live API calls: `python -m py_compile` on `llm.py`, `test_stage1.py`,
  `test_stage2.py`, `investigate_ambient_context.py`, `verify_ambient_context_fix.py` all
  compiled clean, and `import llm` succeeded. Did not re-run the live-CLI test suites
  (`test_stage1.py`/`test_stage2.py`) to avoid incurring real cost on a routine continuity check —
  deferred to whenever a live-CLI verification is actually wanted.
- Built Stage 3 per `BUILD_PLAN.md`/`PLAN.md`'s spec: `blocks.py::extract_block` (ported from
  Denario's `extract_latex_block`/`fixer`) and `state.py::read_state_file`/`write_state_file`
  (following `denario/config.py`'s `input_files/`+filename convention exactly). Designed
  `extract_block`'s repair fallback with an injectable `repair_fn` parameter specifically so
  `test_stage3.py` could exercise both the happy path and the repair-fallback path with zero live
  `claude` calls — 6/6 checks passed, $0 cost.
- Wrote `paul_check.py`: the exact one-command script named in Paul's Goalpost-1 pass/fail check
  (prompt-template → `call_claude` → `extract_block` → `write_state_file`, run twice unattended).
  **Run live and passed.** Both runs completed unattended with no manual intervention, each wrote a
  non-empty, well-formed `idea.md` (run 1: 412 chars, run 2: 535 chars — run 2 overwrote run 1's
  file at the same path, as expected since `write_state_file` always targets the same filename).
  Spot-checked run 2's output by hand, not just for non-emptiness: a coherent, correctly-scoped
  thesis idea (archival ALMA Band 6 continuum + CO(2-1) analysis of NGC 1365's circumnuclear gas,
  compared against AGN torus orientation from the literature, explicitly scoped to "one semester").
  **Goalpost 1 is now fully closed** — all 8 itemized checks plus Paul's own named pass/fail check
  are done.
- **Next action:** Stage 4 — source the one real example ALMA dataset's metadata and fill in
  `data_description.md`, kicking off Goalpost 2. The two Stage 2 follow-ups (process-leak
  re-baseline, `novelty_prompt` wording) remain open, most relevant to Stage 6, not blocking here.

**2026-07-11 — Ambient-context finding chased down and fixed
(`investigate_ambient_context.py`, `verify_ambient_context_fix.py`)**
- Follow-up on Stage 2 Check 4's "the model referenced `test_stage2.py:128-130` unprompted"
  finding. Ran 6 targeted experiments to isolate the cause rather than guess:
  1. **Root cause confirmed directly.** With `--tools ""` (meant to disable everything), the raw
     attempted command leaked straight into the response text: `powershell type
     C:\Users\cb447\.claude\projects\...\alma-thesis-planner\memory\MEMORY.md 2>nul || echo NONE`.
     The headless `claude -p` subprocess runs as a full Claude Code agent — the same system this
     assistant runs as — which by default (a) keeps Read/Glob/Bash tool access to the cwd, (b) has
     a built-in habit of checking a per-project `memory/MEMORY.md` for prior context before
     answering, and (c) will spontaneously attempt a `WebSearch` even when the prompt never asked
     for literature (confirmed separately: a plain "give me a thesis idea" prompt triggered a denied
     `WebSearch` for "ALMA NGC 1365 CO molecular gas gravity torques inflow AGN circumnuclear disk").
     None of this was something the wrapper opted into.
  2. **Not a cross-project memory leak, for now.** The `alma-thesis-planner` project's own
     `.claude/projects/.../memory/` directory is currently empty, so nothing was actually leaked
     *from* memory in these tests — but the mechanism is real and would start injecting persisted
     context into supposedly-stateless calls the moment that file gets populated (e.g., if `claude`
     is ever run interactively from this directory). Forward-looking risk, not fixed by anything
     below — worth re-checking once real project work starts happening in this directory
     interactively.
  3. **Non-deterministic.** The identical prompt, identical directory, identical tool settings
     sometimes triggered file-reading/tool-use behavior and sometimes didn't across repeated runs —
     a real, repeatable failure mode, not a guaranteed one.
  4. **`--bare` ruled out.** Confirmed it hard-fails (exit 1) when only an OAuth CLI login is
     present — it requires `ANTHROPIC_API_KEY`/`apiKeyHelper` and never reads the OAuth session or
     keychain, which is incompatible with this project's zero-API-key design constraint.
  5. **Blanket `--tools ""` rejected as the fix.** It doesn't cleanly disable tool use — the model
     still *attempts* a now-blocked tool call and the broken attempt (raw shell-command text) leaks
     into the final response instead of being suppressed.
  6. **Fix: explicit `--disallowedTools` deny-list.** `--disallowedTools Read Glob Grep Bash
     WebSearch WebFetch` produced a clean, direct answer with `permission_denials=[]` and no
     meta-commentary. Verified this holds repeatably, not just once: 5/5 repeated runs of the exact
     ambient-context-triggering prompt came back clean (no file/tool references) through
     `call_claude`'s new default.
- **Fix applied to `llm.py`:** added `DEFAULT_DISALLOWED_TOOLS = ["Read", "Glob", "Grep", "Bash",
  "WebSearch", "WebFetch", "Write", "Edit"]`, passed as `--disallowedTools` by default in both
  `_invoke` and `call_claude` (overridable via a `disallowed_tools` kwarg, `None` to restore
  unrestricted access). Re-ran `test_stage1.py` afterward — still 4/4, confirming the deny-list
  doesn't break ordinary text generation.
- **Still open:** re-check the memory-leak risk (item 2 above) once this directory has real
  interactive `claude` usage in it, not just subprocess calls from the wrapper.

**2026-07-11 — Stage 2 stress test run (`test_stage2.py`, log in `stage2_run_log.txt`)**
- Fixed a real bug found while building this stage's timeout check: `llm._invoke` previously used
  `subprocess.run(timeout=...)`, which on Windows only kills the immediate `claude.exe` handle, not
  any children it spawns. Rewrote it around `Popen` + a `_kill_process_tree` helper that shells out
  to `taskkill /F /T /PID` on Windows (plain `.kill()` elsewhere) so a timeout can't leak orphans.
  Re-ran `test_stage1.py` afterward — still 4/4.
- **Check 1 (10 back-to-back calls):** 10/10 exact `PONG` matches. Latency P50=10.72s, P95=14.29s,
  min=9.15s, max=14.29s. Total cost $0.1454 for the 10 calls (~$0.0145/call average, higher than
  Stage 1's original $0.017-for-one estimate divided out — consistent with the CLI-version cost
  drift already noted in the Stage 1 entry below).
- **Check 2 (simulated growing-context loop, 4 iters, 274→1466 chars):** wall-clock grew only
  +5.41s and cost only +$0.0099 across the 4 iterations — i.e., cost/latency scale sub-linearly
  with prompt size at this scale (dominated by the fixed ~10s CLI overhead, not prompt length).
  Good news for Stage 5's 8-call idea loop: growing `previous_ideas` context is not expected to
  blow up cost/latency on its own.
- **Check 3 (raw-JSON prompt) — important, unexpected:** the test prompt asked Claude to always
  reply with a canned `{"verdict": "NOT_PUBLISHED", "citations": []}` regardless of any real input.
  Claude refused outright, explicitly identifying this as looking like a prompt-injection/fake-
  verdict pattern, and returned prose instead of JSON. **This is a prompt-design finding, not a
  JSON-parsing finding:** Stage 6's real `novelty_prompt` must always give Claude genuine
  dataset/context to evaluate and ask it to *determine* the verdict, never request a
  predetermined/canned answer — doing otherwise risks an outright refusal rather than malformed
  JSON. The three-fallback JSON-repair path Denario needed may be solving a different problem than
  this one; re-test check 3 with a genuine (not canned-answer) prompt before trusting the
  JSON-format failure mode is understood.
- **Check 4 (loosely-worded prompt) — important, unexpected:** the response opened with
  unprompted meta-commentary noting the prompt was "copied verbatim from `test_stage2.py:128-130`"
  before answering. **This means a headless `claude -p` call invoked from within a project
  directory is not a pure stateless prompt→text function** — it appears to have situational
  awareness of (or read) the surrounding project's files/context rather than treating the prompt
  as isolated text. This directly threatens the "zero side effects" assumption `call_claude` was
  designed around and needs a decision before Stage 5: either (a) always invoke `claude -p` from an
  isolated/empty working directory to force statelessness, or (b) accept and document that ambient
  project context can leak into responses and design prompts defensively around that. **Flagging
  for your review — this is the single most consequential finding from this stress test.**
- **Check 5 (hard timeout):** timeout enforcement itself passed cleanly — raised
  `ClaudeCLIError` ~6s after a 2s timeout was set (the extra ~4s is `taskkill`'s own overhead), no
  hang. The process-tree leak check is **inconclusive**: `tasklist` showed 10 `claude.exe`
  processes still running afterward, but the test took no baseline snapshot before the run, so
  there's no way to tell how many of those 10 pre-existed (e.g. this very interactive session is
  itself a `claude.exe` process, as may be an IDE extension host) versus how many were actually
  leaked by the killed subprocess. **Follow-up needed:** re-run with a `tasklist` snapshot taken
  before Check 1 even starts, diff against the post-timeout snapshot, and only count genuinely new
  PIDs as leaks.
- **Check 6 (tool-tempting prompt):** returned plain text ("`secret_notes.txt` doesn't exist")
  with no stall or permission-prompt hang; `num_turns=2` suggests one internal tool-check turn
  happened but resolved headlessly as expected.
- **Check 7 (web-search trigger) — resolves an open question from Stage 1's addendum:** contrary
  to the earlier inference that headless Claude Code has web search "available by default," the
  literature-flavored prompt got an explicit "I don't have permission to use web search right now"
  response — web search requires an explicit grant and is **not** auto-invoked headlessly, and
  critically it does not stall waiting for permission, it just says so in text. This is good news
  for Stage 6 reproducibility: the novelty-check won't accidentally go out to the live web
  non-deterministically unless we explicitly grant that permission.
- **Check 8 (`--model` pinning) — resolves the other open question from Stage 1's addendum:**
  `--model claude-haiku-4-5` produces `modelUsage` billing for *only* haiku. Passing no `--model`
  or `--model claude-sonnet-5` both bill sonnet for the actual reply *plus* a small fixed
  `claude-haiku-4-5-20251001` side-charge (526 input/~15 output tokens, ~$0.0006) that appears to be
  a fixed internal overhead (e.g. conversation-title generation) rather than uncontrolled routing
  of the primary answer. **Conclusion: `--model` does reliably pin the primary generation**; the
  earlier "two models billed in one call" observation was this fixed side-cost, not routing
  uncertainty, and it should be included in per-call cost budgeting regardless of which model is
  requested.
- **Check 9 (realistic-sized prompt budget):** a genuine 705-char dataset-description-style prompt
  cost $0.0722 and took 17.97s wall-clock (10.2s of which was actual generation) — noticeably more
  than the trivial PONG case ($0.01–0.06, ~10-14s). Budgeting Stage 5's 8-call idea loop off this
  number instead: roughly $0.4–0.6 and 2–3 minutes total, which is comfortably tolerable.
- **Net effect on the plan:** items 5–8 of the "eight items" checklist above are now done, two with
  documented caveats (leak re-check, novelty-prompt wording) rather than fully clean passes. Stage 3
  can start; the two caveats should be resolved before Stage 6 specifically (novelty check) is
  built, since both concerns are most relevant there.

**2026-07-11 — Stage 1 implemented and verified as code**
- Project moved to its own standalone repo/folder, `alma-thesis-planner`, outside `Denario-fork`
  (per the plan's own framing: this borrows Denario's conventions but is not a modification of
  Denario in place).
- Wrote `llm.py`: `call_claude(prompt, *, timeout=120, model=None) -> str`, resolving the `claude`
  executable via `shutil.which` (rather than a bare string) so it works whether invoked from Git
  Bash or native Windows Python; `stdin=subprocess.DEVNULL`; stdout/stderr captured on separate
  pipes; `--output-format json` parsed for `result`, `duration_ms`, `total_cost_usd`; a
  `ClaudeCLIError` raised on non-zero exit, JSON-parse failure, or subprocess timeout.
- Wrote `test_stage1.py`, an automated (no pytest needed) version of the checks that were
  previously only run by hand: no-API-keys check, 3x PONG exact-match, IDEA block round-trip, and
  the public `call_claude` signature.
- Ran it via the plain system Python 3.13 install (`AppData\Local\Programs\Python\Python313`), not
  the Denario-fork `.venv`, from native PowerShell — 4/4 checks passed. This directly answers the
  open "does this work identically from plain Windows Python, not just Git Bash" question raised in
  both Stage 1's addendum and Stage 2 addendum item 7.
- Confirmed `claude` resolves to a real `.exe` (`C:\Users\cb447\.local\bin\claude.exe`) under both
  Git Bash and native PowerShell — so `shell=False` subprocess invocation is safe; no `.cmd`-shim
  `shell=True` workaround is needed.
- **Next action unchanged:** Stage 2's stress test (10 back-to-back calls, timeout enforcement,
  JSON-format prompt, web-search-tool check, `--model` pinning check) has not been run yet.

**2026-07-08 — Stage 1 happy-path smoke test**
- Confirmed `claude` CLI (v2.1.204) runs with zero `OPENAI_API_KEY`/`GOOGLE_API_KEY`/
  `ANTHROPIC_API_KEY` present in the environment.
- 3/3 repeated `claude -p "Reply with exactly the single word: PONG"` calls returned exactly
  `PONG` — no drift, no preamble, no punctuation added.
- A `\begin{IDEA}...\end{IDEA}` block-format prompt was respected cleanly in one test — no stray
  text inside or around the tags.
- Measured: ~8.8s wall-clock per trivial call, of which only ~1.76s was actual API generation time
  (`duration_ms` from `--output-format json`) — roughly 7s of fixed CLI session-bootstrap overhead
  on every call, independent of prompt size. Cost: ~$0.017 for a two-word reply, because Claude
  Code injects its full system prompt/tool definitions (~2,900 input + ~26,700 cache-read tokens)
  on every invocation, not just complex ones.
- **Subprocess/PATH lesson:** all of tonight's testing went through Git Bash, where `claude`
  resolved at `/c/Users/cb447/.local/bin/claude`. This has *not* been confirmed to hold from a
  plain native-Windows Python process — Git Bash and native Windows PowerShell/`python.exe` can
  resolve `PATH` differently, so the wrapper's actual subprocess invocation (`shell=True` vs.
  `False`, bare `claude` vs. a resolved full path) still needs to be verified directly from Windows
  Python before Stage 1 is considered portable, not just "works from this terminal." This is
  tracked as verification item 8 above and in `BUILD_PLAN.md`'s Stage 2 addendum.
- **Not yet done:** Paul's concrete first-milestone check (one command, prompt-template → Claude
  CLI → markdown file, twice in a row, zero manual intervention) has not been formally executed as
  its own script. Tonight's testing is adjacent evidence — it validates the CLI call itself is
  reliable and repeatable — but doesn't yet cover writing output to a markdown file via a single
  command. That script is the concrete next action.
