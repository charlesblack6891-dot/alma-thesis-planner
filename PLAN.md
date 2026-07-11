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

### Stage 4 — Example dataset → `data_description.md`
*Purpose: get one real ALMA dataset's metadata into the pipeline's input format for the first time.
Finished when the filled template is complete and accurate against the source metadata.*
- **Input:** manually downloaded metadata for the one example ALMA dataset (project code, PI,
  target, band/frequency, obs date, array config, proposal science-goal abstract, data products).
  **Real data enters the pipeline here for the first time.**
- **Output:** a filled `data_description.md` for that dataset.
- **Verification:** cross-checked field-by-field against the raw metadata source for completeness;
  round-trips through the Stage 3 I/O helper.

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

### Stage 7 — Methods / work-plan generation
*Purpose: turn the settled idea into a concrete description of the work a student would actually
do. Finished when a human reviewer agrees it's executable in a thesis timeframe without assuming
results that don't exist yet.*
- **Input:** `data_description.md` + `idea.md` (real data); `methods_fast_prompt` ported, reframed
  to describe anticipated key plots/results rather than executed ones.
- **Output:** `methods.md` — description of work to be carried out.
- **Verification:** manual read confirms it's executable by a student in a thesis timeframe and
  doesn't presuppose results that don't exist yet.

### Stage 8 — One-page writeup assembly
*Purpose: combine the idea, methods, and reading list into the actual one-page deliverable.
Finished when the assembled document is coherent, complete, and close to one page.*
- **Input:** `idea.md` (abstract), `methods.md` (work description), `literature.md` (reading list)
  — real data.
- **Output:** a single ~1-page markdown/text file combining all three sections.
- **Verification:** close to one page; contains all three required sections; reads as one coherent
  document, not three stapled-together fragments.

### Stage 9 — End-to-end orchestration + published short-circuit
*Purpose: wire every prior stage into one entrypoint that automatically branches on the
published/unpublished verdict. Finished when a single command produces the correct output type for
both ground-truth test datasets, with no manual stage-by-stage invocation.*
- **Input:** a `data_description.md` for any dataset; one CLI entrypoint script. Real data — both
  ground-truth datasets from Stage 6.
- **Output:** either a short "already published" note + citation, or the full Stage 8 one-pager.
- **Verification:** run on both test datasets; each takes the correct branch automatically, with no
  manual stage-by-stage invocation.

## Milestone list

| Milestone | Scope | Status |
|---|---|---|
| Goalpost 0 — Project plan locked in with Paul | This document + sign-off | Near-complete; awaiting Paul's review |
| Goalpost 1 — Claude Code CLI adapter proven | Build Stages 1–2 | Stage 1 code written and passing (4/4 checks, native Windows Python); Stage 2 stress test not yet run |
| Goalpost 2 — First end-to-end one-pager | Build Stages 3–8 | Not started |
| Goalpost 3 — Validate the published/unpublished short-circuit | Build Stage 9 | Not started |
| Goalpost 4 — Small-batch calibration (~5–10 datasets) | Eval rubric, prompt tuning | Not started |
| Goalpost 5 — Automated ingestion | `astroquery.alma` or NRAO's layer, triggered by need | Not started |
| Goalpost 6 — Scale and robustness | Batch processing, retries, idempotency, review queue | Not started |
| Goalpost 7 — Handoff to Paul's/NRAO's team | Documentation, runbook, retrospective | Not started |

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
5. 10 back-to-back calls complete with no failures or silent truncation. ⬜ not yet run
6. A hard timeout is enforced and returns/raises cleanly rather than hanging. ⬜ not yet run
7. A prompt touching on literature search is checked for unwanted web-search tool use, and a
   prompt tempting file/tool use still returns plain text headlessly. ⬜ not yet run
8. The exact invocation flags needed for reliably clean output (including whether `--model`
   actually pins one model) are documented as the standard call pattern for Stage 5 onward. ⬜ not
   yet run

Once 5–8 hold (or have documented workarounds), Stages 1–2 are done and Stage 3 can start.

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
