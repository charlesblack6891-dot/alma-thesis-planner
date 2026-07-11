"""Claude CLI call primitive (Stage 1).

Shells out to a headless `claude -p` invocation and returns plain text,
with zero API keys required. This is the one function every later stage
depends on.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass


class ClaudeCLIError(RuntimeError):
    """Raised when the `claude` CLI exits non-zero or returns unparseable output."""


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


def _invoke(prompt: str, *, timeout: float = 120, model: str | None = None) -> ClaudeResult:
    claude_exe = _resolve_claude_exe()
    cmd = [claude_exe, "-p", prompt, "--output-format", "json"]
    if model is not None:
        cmd += ["--model", model]

    start = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        shell=False,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
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


def call_claude(prompt: str, *, timeout: float = 120, model: str | None = None) -> str:
    """Send `prompt` to Claude via the headless CLI and return the response text."""
    return _invoke(prompt, timeout=timeout, model=model).text
