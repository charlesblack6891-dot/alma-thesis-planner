"""LLM call primitives (Stage 1, extended).

Two providers, both exposed as plain prompt-in/text-out functions:
- call_claude: shells out to a headless `claude -p` invocation. Zero API
  keys required -- it uses whatever account the `claude` CLI is already
  logged into (`claude` -> "Claude account" login, chosen once outside this
  app). Anthropic documents Claude Code CLI access as requiring a paid
  Claude Pro/Max/Team/Enterprise plan or API billing; a free claude.ai
  account may or may not be granted CLI access, and if not, every call
  fails immediately with an auth/permission error from the CLI. See
  wizard.py's PROVIDERS ("claude" vs. "claude_free") for the user-facing
  explanation -- the Python code path is identical either way, since
  call_claude has no way to tell which account is logged in.
- call_gemini: calls Google's Gemini API directly over HTTPS. Needs a
  GEMINI_API_KEY (free, no billing/card required, from
  https://aistudio.google.com/apikey), and stays within Gemini's free tier
  as long as request volume stays under its rate limits.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass

import requests

try:
    # Makes Python's ssl module verify certs via the OS trust store instead of
    # certifi's bundle. Needed on machines where an antivirus/proxy does TLS
    # interception with a root cert that's trusted by Windows but fails strict
    # OpenSSL chain validation (e.g. AVG's Web/Mail Shield root cert has its
    # Basic Constraints extension marked non-critical, which recent OpenSSL
    # rejects even though Windows CryptoAPI accepts it).
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass


class ClaudeCLIError(RuntimeError):
    """Raised when the `claude` CLI exits non-zero or returns unparseable output."""


class GeminiAPIError(RuntimeError):
    """Raised when the Gemini API call fails, is misconfigured, or returns no usable text."""


# Headless `claude -p` keeps full agentic tool access by default (Read/Glob/Bash on
# the cwd, an auto-memory check against the project's own memory/MEMORY.md, and
# spontaneous WebSearch attempts) even for prompts that never asked for any of it.
# This breaks call_claude's stateless prompt-in/text-out contract, non-deterministically
# (confirmed via investigate_ambient_context.py: identical prompts sometimes read local
# files unprompted, sometimes don't). Denying these tools explicitly is the fix -- a
# blanket `--tools ""` was tried first and rejected: it still lets the model *attempt*
# a now-blocked tool call, and the broken attempt leaks into the response text instead
# of being disabled cleanly.
DEFAULT_DISALLOWED_TOOLS = ["Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch", "Write", "Edit"]


@dataclass
class ClaudeResult:
    text: str
    wall_clock_s: float
    duration_ms: float | None
    cost_usd: float | None
    raw: dict


def _resolve_claude_exe() -> str:
    path = shutil.which("claude")
    if path is None:
        raise ClaudeCLIError(
            "Could not find `claude` on PATH. Install Claude Code CLI and "
            "ensure it is on PATH."
        )
    return path


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kill `proc` and any children it spawned. `proc.kill()` alone only kills the
    immediate process on Windows, which can leak child processes on timeout."""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
        )
    else:
        proc.kill()


def _invoke(
    prompt: str,
    *,
    timeout: float = 120,
    model: str | None = None,
    disallowed_tools: list[str] | None = DEFAULT_DISALLOWED_TOOLS,
) -> ClaudeResult:
    claude_exe = _resolve_claude_exe()
    # The prompt is piped over stdin rather than passed as a "-p <prompt>"
    # command-line argument -- confirmed live that a long prompt as an argv
    # element (tens of thousands of characters, e.g. a late idea-loop
    # iteration with several rounds of accumulated context) raises
    # `OSError: [WinError 206] The filename or extension is too long` on
    # Windows. `-p`/`--print` alone (no positional prompt) reads from stdin,
    # confirmed working via `echo ... | claude -p --output-format json`,
    # and stdin has no comparable length limit.
    cmd = [claude_exe, "-p", "--output-format", "json"]
    if model is not None:
        cmd += ["--model", model]
    if disallowed_tools:
        cmd += ["--disallowedTools", *disallowed_tools]

    # On Windows, `claude` is an npm .cmd shim, so launching it spawns a cmd.exe
    # that needs a console. When the parent has none of its own (gui_app.py runs
    # via pythonw.exe from a desktop shortcut), Windows pops up a brand-new
    # visible console window for it -- even though stdin/stdout/stderr are fully
    # piped and nothing needs to be shown there. CREATE_NO_WINDOW suppresses
    # that console entirely; the pipes still work identically.
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    start = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        shell=False,
        creationflags=creationflags,
    )
    try:
        stdout, stderr = proc.communicate(input=prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_process_tree(proc)
        proc.wait()
        raise ClaudeCLIError(f"claude CLI timed out after {timeout}s (process tree killed)")
    wall_clock_s = time.monotonic() - start

    if proc.returncode != 0:
        raise ClaudeCLIError(
            f"claude CLI exited {proc.returncode}. stderr:\n{stderr}"
        )

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ClaudeCLIError(
            f"claude CLI did not return valid JSON. stdout:\n{stdout!r}\n"
            f"stderr:\n{stderr!r}"
        ) from exc

    if "result" not in data:
        raise ClaudeCLIError(f"claude CLI JSON had no 'result' field: {data!r}")

    return ClaudeResult(
        text=data["result"],
        wall_clock_s=wall_clock_s,
        duration_ms=data.get("duration_ms"),
        cost_usd=data.get("total_cost_usd"),
        raw=data,
    )


def call_claude(
    prompt: str,
    *,
    timeout: float = 120,
    model: str | None = None,
    disallowed_tools: list[str] | None = DEFAULT_DISALLOWED_TOOLS,
) -> str:
    """Send `prompt` to Claude via the headless CLI and return the response text.

    By default, denies Read/Glob/Grep/Bash/WebSearch/WebFetch/Write/Edit so the call
    behaves as a stateless prompt-in/text-out function rather than a full agent with
    ambient access to the calling directory. Pass disallowed_tools=None to restore
    default (unrestricted) tool access.
    """
    return _invoke(prompt, timeout=timeout, model=model, disallowed_tools=disallowed_tools).text


# Google's rolling aliases, which always resolve to the current supported
# Flash/Pro models. Pinned ids rot: "gemini-2.5-flash" started returning 404
# ("no longer available to new users") for keys created after some cutoff,
# observed live 2026-08-06, while STILL appearing in the ListModels response --
# so availability can't even be checked by listing. The aliases sidestep model
# retirements entirely. Free-tier (no-billing-key) quotas apply to the Flash
# alias; set the GEMINI_MODEL env var or pass model= to override either.
DEFAULT_GEMINI_MODEL = "gemini-flash-latest"
# The stronger Gemini model for keys with billing enabled (pay-per-token). Its
# free-tier quota is tiny-to-none, so it's only offered behind the GUI's
# explicit "paid tier" choice, never as a silent default.
PAID_GEMINI_MODEL = "gemini-pro-latest"
GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"
GEMINI_MODEL_ENV_VAR = "GEMINI_MODEL"
_GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# How many times a 429 (per-minute rate limit) is waited out before giving up.
# Free-tier per-minute caps reset within ~a minute, so waiting is normally
# enough; per-day caps don't reset until midnight Pacific and aren't retried.
_RATE_LIMIT_MAX_WAITS = 3
_RATE_LIMIT_DEFAULT_WAIT_S = 30.0
_RATE_LIMIT_MAX_WAIT_S = 70.0


def _parse_retry_delay_s(response_json: dict) -> float:
    """Pull google.rpc.RetryInfo's retryDelay (e.g. "39s") out of a 429 error
    body, falling back to a default if absent/unparseable."""
    try:
        for detail in response_json.get("error", {}).get("details", []):
            if str(detail.get("@type", "")).endswith("RetryInfo"):
                delay = str(detail.get("retryDelay", "")).rstrip("s")
                return min(float(delay), _RATE_LIMIT_MAX_WAIT_S)
    except (TypeError, ValueError):
        pass
    return _RATE_LIMIT_DEFAULT_WAIT_S


def call_gemini(prompt: str, *, timeout: float = 120, model: str | None = None) -> str:
    """Send `prompt` to Gemini via its HTTPS API and return the response text.

    Free-tier fallback for call_claude: needs a GEMINI_API_KEY (free, no billing
    required -- get one at https://aistudio.google.com/apikey) instead of a Claude
    subscription, but is generally a less capable/consistent writer for this
    pipeline's multi-stage prompts, and is rate-limited (requests per minute/day)
    rather than token-metered.
    """
    api_key = os.environ.get(GEMINI_API_KEY_ENV_VAR)
    if not api_key:
        raise GeminiAPIError(
            f"No {GEMINI_API_KEY_ENV_VAR} environment variable set. Get a free key (no billing/card "
            f"required) at https://aistudio.google.com/apikey, then set {GEMINI_API_KEY_ENV_VAR} "
            "before running this again."
        )

    resolved_model = model or os.environ.get(GEMINI_MODEL_ENV_VAR) or DEFAULT_GEMINI_MODEL
    url = _GEMINI_ENDPOINT.format(model=resolved_model)
    # Two transients are waited out here rather than surfaced, because one
    # mid-pipeline throw discards every already-made call in the run:
    # - 503 ("model is experiencing high demand") -- observed repeatedly in a
    #   single afternoon (2026-08-06), brief.
    # - 429 per-MINUTE rate limit (free tier) -- resets within ~a minute, so
    #   waiting out Google's own retryDelay hint normally succeeds. The
    #   per-DAY cap is the exception: it doesn't reset until midnight Pacific,
    #   so it's surfaced immediately with a clear message instead of retried
    #   (its quotaId contains "PerDay" in the 429 error body).
    response = None
    rate_limit_waits = 0
    attempt = 0
    while True:
        attempt += 1
        try:
            response = requests.post(
                url,
                params={"key": api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise GeminiAPIError(f"Gemini API request failed: {exc}") from exc
        if response.status_code == 503 and attempt < 3:
            time.sleep(5 * attempt)
            continue
        if response.status_code == 429:
            body_squashed = response.text.upper().replace("_", "").replace(" ", "")
            if "PERDAY" in body_squashed:
                raise GeminiAPIError(
                    "Gemini free-tier DAILY request cap exhausted -- it resets at midnight US "
                    "Pacific time, so retrying now won't help. Options: wait for the reset, switch "
                    "the provider to Claude, or use Gemini's paid tier (enable billing on your "
                    f"Google account's key). Response: {response.text}"
                )
            if "SPENDCAP" in body_squashed or "SPENDINGCAP" in body_squashed:
                # Hit live 2026-08-06: a key whose Google project has a monthly
                # spending cap returns 429 with this message once the cap is
                # exceeded. No amount of waiting clears it -- only raising the
                # cap (or waiting for the new month) does.
                raise GeminiAPIError(
                    "Your Gemini key's Google project has exceeded its MONTHLY spending cap -- "
                    "retrying won't help. Raise or remove the cap at https://ai.studio/spend, "
                    f"switch the provider to Claude, or wait for the new month. Response: {response.text}"
                )
            if rate_limit_waits < _RATE_LIMIT_MAX_WAITS:
                rate_limit_waits += 1
                try:
                    delay = _parse_retry_delay_s(response.json())
                except json.JSONDecodeError:
                    delay = _RATE_LIMIT_DEFAULT_WAIT_S
                time.sleep(delay)
                continue
            raise GeminiAPIError(
                "Gemini per-minute rate limit still hit after waiting it out "
                f"{_RATE_LIMIT_MAX_WAITS} times -- the free tier caps requests per minute. Wait a "
                "few minutes and retry, switch the provider to Claude, or use Gemini's paid tier "
                f"(enable billing on your Google account's key). Response: {response.text}"
            )
        break

    if response.status_code == 404:
        raise GeminiAPIError(
            f"Gemini model {resolved_model!r} was not found for this API key -- Google retires "
            "model ids over time and gates some by account age. This app defaults to the rolling "
            f"'{DEFAULT_GEMINI_MODEL}' alias to avoid exactly this; if you overrode the model (the "
            f"{GEMINI_MODEL_ENV_VAR} env var or an explicit model=), clear the override or pick an "
            f"id your key can use. Response: {response.text}"
        )
    if response.status_code != 200:
        raise GeminiAPIError(f"Gemini API returned HTTP {response.status_code}: {response.text}")

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        raise GeminiAPIError(f"Gemini API did not return valid JSON: {response.text!r}") from exc

    candidates = data.get("candidates") or []
    if not candidates:
        feedback = data.get("promptFeedback")
        raise GeminiAPIError(f"Gemini API returned no candidates (promptFeedback={feedback}): {data!r}")

    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts)
    if not text:
        finish_reason = candidates[0].get("finishReason")
        raise GeminiAPIError(
            f"Gemini API returned no text (finishReason={finish_reason!r}) -- the prompt may have "
            f"been blocked by safety filters: {data!r}"
        )
    return text
