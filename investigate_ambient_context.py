"""One-off investigation: why did a headless `claude -p` call reference the
local test_stage2.py file by name and line number, unprompted, when the prompt
gave it no reason to? This isn't part of the Stage 2 test suite -- it's a
follow-up experiment to isolate the cause before deciding how (or whether) to
fix call_claude's statelessness assumption.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = shutil.which("claude")
NEUTRAL_DIR = (
    r"C:\Users\cb447\AppData\Local\Temp\claude\C--Users-cb447-OneDrive-Documents-GitHub-Denario-fork"
    r"\9cbe325e-13d5-4ef0-a8ef-1165804a4770\scratchpad\neutral_cwd_test"
)

AMBIENT_PROMPT = (
    "Can you help me come up with a senior thesis idea for an ALMA dataset of "
    "NGC 1365? Please format your final answer inside \\begin{IDEA}...\\end{IDEA} tags."
)


def run(label: str, prompt: str, extra_args: list[str] | None = None, cwd: str | None = None) -> dict | None:
    cmd = [CLAUDE, "-p", prompt, "--output-format", "json"]
    if extra_args:
        cmd += extra_args
    print(f"\n--- {label} ---")
    print(f"  cmd: {' '.join(a if a else chr(39)+chr(39) for a in cmd[:2])} <prompt> {' '.join(cmd[3:])}")
    print(f"  cwd: {cwd or '(default)'}")
    proc = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        timeout=120,
    )
    if proc.returncode != 0:
        print(f"  [ERROR] exit={proc.returncode}")
        print(f"  stderr: {proc.stderr[:2000]}")
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] non-JSON stdout: {proc.stdout[:1000]!r}")
        return None
    print(f"  is_error={data.get('is_error')} num_turns={data.get('num_turns')} "
          f"permission_denials={data.get('permission_denials')}")
    print(f"  result: {data.get('result', '')[:600]!r}")
    return data


def main() -> int:
    # 1. Baseline: reproduce the original Check 4 finding with full raw JSON visible,
    #    from the project directory (where test_stage2.py actually exists).
    run("1. baseline (project dir, default tools)", AMBIENT_PROMPT)

    # 2. Same prompt, same directory, but with all tools disabled -- if the
    #    file-reference disappears, tool use (not system-prompt cwd/git-status
    #    text) was the cause.
    run("2. tools disabled (--tools \"\")", AMBIENT_PROMPT, extra_args=["--tools", ""])

    # 3. Same prompt, but run from a neutral directory with no project files at
    #    all -- isolates whether cwd *contents* (not just cwd path/git status)
    #    matter.
    run("3. neutral empty directory, default tools", AMBIENT_PROMPT, cwd=NEUTRAL_DIR)

    # 4. Does --bare preserve OAuth auth, or does it force API-key auth (which
    #    would break the project's zero-API-key design)? Cheap PONG check.
    run("4. --bare auth check", "Reply with exactly the single word: PONG", extra_args=["--bare"])

    # 5. Does moving cwd/git-status out of the system prompt (without removing
    #    it) change behavior?
    run(
        "5. --exclude-dynamic-system-prompt-sections",
        AMBIENT_PROMPT,
        extra_args=["--exclude-dynamic-system-prompt-sections"],
    )

    # 6. --tools "" left the model attempting a blocked tool call and giving a
    #    broken stub answer. Does an explicit deny-list instead produce a clean
    #    answer that just doesn't use tools, rather than a failed attempt?
    run(
        "6. explicit --disallowedTools deny-list",
        AMBIENT_PROMPT,
        extra_args=["--disallowedTools", "Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch"],
    )

    print("\nDone. Compare 'result' text across runs 1/2/3/6 to isolate the cause.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
