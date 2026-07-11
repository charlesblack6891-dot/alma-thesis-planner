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
| Goalpost 1 — Claude Code CLI adapter proven | Build Stages 1–2 | Stage 1 done; Stage 2 stress test run, functionally passing with 2 documented follow-ups (process-leak re-check, novelty-prompt wording) |
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
