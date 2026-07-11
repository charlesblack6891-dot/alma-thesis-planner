# ALMA Dataset → Senior Thesis Planner — Stage-by-Stage Build Plan

**Status:** planning only, no implementation code yet — companion to `PROJECT_BRIEF.md`.

Each stage is a working, independently-testable unit — no stage depends on unfinished work from a
later stage.

## Real vs. synthetic data, by stage

| Stage | Data to use | Why |
|---|---|---|
| 1 — Claude CLI call primitive | **Synthetic** (hardcoded test strings, e.g. `"PONG"`, a generic `\begin{IDEA}` prompt) | Testing subprocess/CLI mechanics only — no dataset content is involved at all. |
| 2 — Claude CLI stress test | **Synthetic** | Same — testing CLI reliability/cost/timeout behavior, not domain content. |
| 3 — Output-parsing and file-state primitives | **Synthetic** | Unit tests against fabricated well-formed/malformed strings; no ALMA data needed. |
| 4 — Example dataset → `data_description.md` | **Real** (first real data enters the pipeline here) | The whole point of this stage is building the actual template from real, manually-sourced ALMA metadata. |
| 5 — Idea-maker / idea-hater loop | **Real, after a synthetic smoke test** | Run once against a synthetic toy `data_description.md` first to validate loop mechanics and the scope-check rubric cheaply; then switch to the real dataset(s) from Stage 4 for the actual thesis-idea output. |
| 6 — Published/novelty check | **Real — specifically 2–3 hand-picked datasets with known ground truth** | Can only be verified against real, checkable publication status (at least one confirmed published, one confirmed not). |
| 7 — Methods / work-plan generation | **Real** | Builds directly on Stage 5's real idea output. |
| 8 — One-page writeup assembly | **Real** | Assembles real idea/methods/literature files produced by prior stages. |
| 9 — End-to-end orchestration + published short-circuit | **Real — needs both ground-truth datasets from Stage 6** | Verifies the branch logic against a known-published and a known-unpublished case. |

This refines Goalpost 0's "one example dataset" (wording left as-is in `PROJECT_PLAN.md`/
`PROJECT_ROADMAP.md`) into "2–3 hand-picked real examples" for this build plan specifically, since
Stages 6 and 9 already require at least two to be verifiable at all.

## Stage 1 — Claude CLI call primitive

- **Input:** a raw prompt string (plain text — no LangChain wrapper).
- **Output:** a single Python function, e.g. `call_claude(prompt: str) -> str`, that shells out to
  `claude -p ...` and returns the model's text.
- **Verification:** with `OPENAI_API_KEY`/`GOOGLE_API_KEY`/`ANTHROPIC_API_KEY` all unset in the
  shell, call it with `"Reply with exactly the single word: PONG"` and assert the stripped output
  `== "PONG"`. Separately, call it with a prompt that asks for a multi-line
  `\begin{IDEA}...\end{IDEA}` block and confirm the block survives the subprocess round-trip intact
  (no truncation, no encoding mangling — worth checking explicitly on Windows). Record latency;
  confirm it's tolerable given you'll call this ~8+ times per idea loop.

---

**Addendum to Stage 1 (added after live-testing against `claude` CLI v2.1.204, before any wrapper
code was written):** the original checks above held — 3/3 repeated `"PONG"` calls were literal and
consistent, and a `\begin{IDEA}...\end{IDEA}` block prompt was respected cleanly with no stray
wrapper text. But live-testing surfaced five issues the original Stage 1 didn't anticipate, now
folded in as required implementation details and additional checks:

1. **Fixed per-call overhead is large and separate from generation time.** Wall-clock time for a
   trivial call was ~8.8s, but the JSON output's own `duration_ms` (actual API generation time) was
   only ~1.76s — the remaining ~7s is Claude Code CLI session bootstrap, present on every call
   regardless of prompt complexity. **New check:** measure wall-clock vs. reported `duration_ms`
   separately, and budget the ~7s fixed cost into Stage 5's ~8-call idea loop timing (expect ~56s+
   of pure overhead, before any real generation time).
2. **Real per-call dollar cost, even for trivial prompts.** A two-word "PONG" response cost
   `$0.0174` because `-p` bootstraps a full session with system prompt/tool definitions injected
   every time (2,899 input tokens + 26,673 cache-read tokens for an 8-token prompt). **New check:**
   sum `total_cost_usd` (from `--output-format json`) across a full Stage 5 idea-loop run and treat
   it as a real budget line item for Goalpost 4/6 batch scale, not as free.
3. **More than one model is invoked per single `-p` call.** The JSON `modelUsage` field showed both
   `claude-haiku-4-5` and `claude-sonnet-5` billed in one invocation — there's an internal
   routing/helper layer. **New check:** confirm whether a `--model` flag pins this reliably, since
   uncontrolled model routing could affect output consistency across runs.
4. **stdin-wait gotcha.** Without explicitly closing stdin, the CLI prints
   `Warning: no stdin data received in 3s, proceeding without it.` and waits ~3 extra seconds
   guessing whether something is piping input to it. **New implementation requirement:** the Python
   wrapper must always pass `stdin=subprocess.DEVNULL`, not just capture stdout.
5. **stdout/stderr must be captured separately.** The stdin warning above is written to stderr; if
   the wrapper merges streams, that text (or any other stderr output) could contaminate the
   regex-extraction step. **New implementation requirement:** capture stdout and stderr on separate
   pipes and parse only stdout.

Checks 1 and 2 are also added to Stage 2's stress test below as explicit pass criteria (cost/latency
budget, not just correctness).

---

## Stage 2 — Claude CLI stress test

Pulled forward, before any prompt-porting work: Stage 1 only proves the happy path (one clean
call). This stage proves the primitive is trustworthy under the conditions it'll actually run
under — `claude -p` is a full agentic harness (tool-use, permission prompts, hooks, context
injection), not a stateless completion API, so its failure modes are different from a raw API call
and worth finding now rather than mid-way through Stage 5's idea loop.

- **Input:** `call_claude` from Stage 1.
- **Output:** a short validation script/log documenting behavior under repeated and adversarial
  conditions — not production code, just evidence.
- **Verification:**
  1. **Repeated calls:** issue 10 back-to-back calls (matching the ~8-call idea-loop volume from
     Stage 5) with no failures or silent truncation; record P50/P95 latency.
  2. **Messy/wrapped output:** send a loosely-specified prompt likely to trigger conversational
     preamble around the requested content, and confirm whether `extract_block` (Stage 3) needs its
     fallback-repair path exercised for real, not just on synthetic malformed input.
  3. **Timeout handling:** confirm a hard subprocess timeout is enforced and raises/returns cleanly
     rather than hanging, in case the CLI ever blocks on a permission/tool-use prompt it can't
     resolve non-interactively.
  4. **Permission-prompt behavior:** craft a prompt that might tempt the CLI toward tool use (e.g.
     referencing a file path, asking it to "check" something) and confirm headless invocation still
     returns plain text rather than stalling or erroring.
  5. Document any CLI flags required to get reliably clean, tool-use-free text output (e.g. a
     specific `--output-format` mode) — this becomes the standard invocation used everywhere from
     Stage 5 onward.
  6. **Cost/latency budget (added per Stage 1 addendum):** sum `total_cost_usd` and wall-clock time
     across the 10 repeated calls from check 1; confirm both are within a per-dataset budget
     acceptable for Goalpost 4/6 batch scale (exact numbers TBD with Paul, but the order of
     magnitude — cents and single-digit seconds of overhead per call — needs to be sanity-checked
     now).

  All of the above must pass, or have a documented workaround, before Stage 3 begins.

---

**Addendum to Stage 2 (added after a walkthrough of each of the six checks above, before running
the stress test):**

1. **Check 1 (repeated calls) uses a non-representative prompt.** 10 identical short calls won't
   surface the real scaling problem: Stage 5's actual idea loop appends to `previous_ideas` every
   iteration, so call 8 carries a much larger prompt (and higher cost/latency) than call 1. **New
   check:** in addition to the 10 fixed-prompt calls, run a short simulated loop (3–4 calls with
   artificially growing prompt size) to see whether cost/latency scale linearly or worse. Also
   confirm each call gets a genuinely fresh session (no accidental `--continue`/`--resume`), and
   watch for throttling under rapid sequential calls.
2. **Check 2 (messy/wrapped output) only tests one of two output formats actually needed.** The
   `\begin{TAG}` block format was already validated in the Stage 1 addendum, but `novelty_prompt`
   (needed for Stage 6) expects raw JSON — a different failure surface. Denario's own code needed
   three successive JSON-parsing fallbacks (`json_parser`, `json_parser2`, `json_parser3`), a strong
   signal that JSON-format compliance is flakier than block-format compliance. **New check:**
   explicitly test a JSON-response prompt, not just the block format.
3. **Check 3 (timeout) can't be set from PONG-scale timing data.** The trivial call took ~8.8s
   wall-clock; a real idea/method-generation call could run 30s–2min+. **New check:** run at least
   one timing sample against an actual production-length prompt before picking a timeout value.
   Separately, confirm `subprocess.run(..., timeout=N)` actually kills the full `claude` process
   tree on Windows, not just the immediate handle, to avoid orphaned processes silently accruing
   cost.
4. **Check 4 (permission prompts) should target web search, not file/tool use.** The Stage 1
   addendum's JSON output included `"web_search_requests":0`, implying headless Claude Code has a
   web-search tool available by default. The literature/novelty-check prompts are specifically
   about finding related work — exactly the kind of prompt that might tempt a web search rather
   than reasoning only from the prompt-provided context. **New check:** test whether the novelty
   prompt triggers a web search, whether that affects determinism/cost run-to-run, and decide
   whether to suppress it (for reproducibility) or lean into it (it might outperform the separate
   Semantic Scholar call).
5. **Check 5 (documented flags) should confirm `--model` actually pins a single model.** Stage 1's
   addendum showed two different models (`haiku` + `sonnet`) billed in one call. **New check:**
   verify whether `--model` genuinely constrains generation to one model or just influences a
   "primary" choice while internal routing still happens underneath.
6. **Check 6 (cost/latency budget) has the same blind spot as check 1.** Summing cost over 10
   trivial calls will understate the real per-idea-loop budget once prompts carry a full data
   description plus accumulating context. **New check:** rerun the budget calculation against a
   realistic-sized prompt, not just the PONG-style one, before trusting the number.
7. **Meta: verify subprocess invocation from plain Windows Python, not just Git Bash.** All testing
   so far has gone through Git Bash, where `claude` resolves via
   `/c/Users/cb447/.local/bin/claude`. If the real wrapper runs under native Windows Python,
   `shell=True`/`False` behavior and PATH resolution haven't been verified yet. **New check:**
   confirm `call_claude` works identically when invoked from a plain `python.exe` process on
   Windows.

---

## Stage 3 — Output-parsing and file-state primitives

- **Input:** raw text from `call_claude`, and a project directory path.
- **Output:** (i) `extract_block(text, tag) -> str`, a regex extractor for
  `\begin{TAG}...\end{TAG}` ported from Denario's `extract_latex_block`, including a repair
  fallback for malformed output; (ii) plain read/write helpers for the markdown state files
  (`data_description.md`, `idea.md`, `methods.md`, `literature.md`) under `input_files/`, following
  Denario's directory convention.
- **Verification:** unit-test `extract_block` against a well-formed string, and a deliberately
  malformed one (missing closing tag) — confirm the fallback path triggers predictably rather than
  crashing. Confirm a file written by the write-helper reads back byte-identical through the
  read-helper.

## Stage 4 — Example dataset → `data_description.md`

- **Input:** manually downloaded metadata for the one example ALMA dataset (project code, PI,
  target, band/frequency, obs date, array config, proposal science-goal abstract, data products).
- **Output:** a filled `data_description.md` for that dataset.
- **Verification:** cross-check the filled file against the raw metadata source field-by-field for
  completeness, and confirm it round-trips through the Stage 2 I/O helper.

## Stage 5 — Idea-maker / idea-hater loop

- **Input:** `data_description.md`; `idea_maker_prompt`/`idea_hater_prompt` text ported from
  Denario and reframed to senior-thesis scope; a plain Python loop (replacing LangGraph's `router`)
  driving N maker↔hater iterations.
- **Output:** `idea.md` — one settled, thesis-scoped project idea.
- **Verification:** run against the Stage 4 dataset; diff the idea text iteration-to-iteration to
  confirm the hater's criticism is actually changing the maker's output (not just repeating);
  manually confirm the final idea reads as thesis-sized, not full-paper-sized; confirm zero API
  keys were present during the run.

  **Early scope check (do not defer to batch calibration):** score every idea produced in this
  stage against a lightweight 3-question rubric before moving on — (1) is the task bounded to
  something completable in one thesis timeframe, (2) does it avoid requiring new
  instrumentation/data beyond what's in `data_description.md`, (3) would a domain expert plausibly
  agree it's tractable, not just novel/impactful? Denario's idea-hater prompt optimizes for
  feasibility *and impact*, which can push toward over-ambitious scope — catching that drift here,
  on the first dataset, is cheaper than discovering it after Stages 6–9 are built on top of it.

## Stage 6 — Published/novelty check

- **Input:** `data_description.md` (+ `idea.md` if useful for context); `novelty_prompt`/
  `summary_literature_prompt` ported and reframed around project code/PI/target rather than generic
  idea novelty; the plain Semantic Scholar REST call (unchanged, no LLM).
- **Output:** `literature.md` — a PUBLISHED / NOT-PUBLISHED verdict with citations, doubling as the
  background-reading list.
- **Verification:** run against two hand-picked test cases — one dataset known to already have a
  publication, one known not to — and confirm the verdict matches ground truth for both. Where
  possible, cross-check against the ALMA archive UI's own publication-linkage field.

## Stage 7 — Methods / work-plan generation

- **Input:** `data_description.md` + `idea.md`; `methods_fast_prompt` ported, reframed to describe
  *anticipated* key plots/results rather than executed ones.
- **Output:** `methods.md` — description of work to be carried out.
- **Verification:** manual read: is this something a student could actually execute in a thesis
  timeframe, and does it avoid presupposing results that don't exist yet?

## Stage 8 — One-page writeup assembly

- **Input:** `idea.md` (→ abstract), `methods.md` (→ work description), `literature.md` (→ reading
  list).
- **Output:** a single ~1-page markdown/text file combining all three sections.
- **Verification:** render it and confirm it's close to one page, contains all three required
  sections, and reads as one coherent document rather than three stapled-together fragments.

## Stage 9 — End-to-end orchestration + published short-circuit

- **Input:** a `data_description.md` for any dataset; one CLI entrypoint script.
- **Output:** either a short "already published" note + citation (if Stage 5 says PUBLISHED), or
  the full Stage 7 one-pager (if NOT PUBLISHED).
- **Verification:** run the single entrypoint on both Stage 6 test datasets (published and
  unpublished) and confirm each takes the correct branch automatically, with no manual
  stage-by-stage invocation.

## First milestone

**Stages 1 + 2 together** — the Claude CLI call primitive, proven trustworthy under realistic
conditions, not just the happy path. Everything downstream depends on it, and it's the one
genuinely unproven assumption in the whole architecture: that a headless `claude -p` subprocess
call — which is an agent harness, not a stateless completion API — can reliably stand in for an
LLM API call, on Windows, at the volume this pipeline needs.

**Exact verification to call it met:**

1. Clear `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY` from the environment and confirm
   they're empty.
2. `call_claude("Reply with exactly the single word: PONG")` returns exactly `"PONG"` after
   stripping whitespace.
3. `call_claude(...)` with a prompt demanding a `\begin{IDEA}...\end{IDEA}` multi-line block
   returns that block intact — no truncation, no mangled line endings/encoding.
4. Measure wall-clock time for a single call; confirm it's low enough that an 8-call idea loop
   (Stage 5) finishes in a few minutes, not tens of minutes.
5. 10 back-to-back calls complete with no failures or silent truncation (Stage 2, check 1).
6. A hard timeout is enforced and returns/raises cleanly rather than hanging (Stage 2, check 3).
7. A prompt that might tempt tool use still returns plain text headlessly, without stalling on a
   permission prompt (Stage 2, check 4).
8. The exact invocation flags needed for reliably clean output are documented, to be used as the
   standard call pattern from Stage 5 onward (Stage 2, check 5).

Once all eight hold, Stages 1–2 are done and Stage 3 can start.
