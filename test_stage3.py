"""Stage 3 verification: extract_block() and the markdown state-file
read/write helpers.

Deliberately makes zero live `claude` CLI calls -- the repair-fallback path
is exercised with a fake repair_fn (dependency injection), not the real
Claude CLI, so this suite is free and deterministic to run.

Run directly (no pytest dependency needed):
    python test_stage3.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from blocks import BlockExtractionError, extract_block
from state import (
    DESCRIPTION_FILE,
    read_state_file,
    write_state_file,
)


def check_well_formed_extraction() -> None:
    text = "some preamble\n\\begin{IDEA}\nA great idea.\nTwo lines.\n\\end{IDEA}\ntrailer"
    result = extract_block(text, "IDEA")
    assert result == "A great idea.\nTwo lines.", f"got {result!r}"
    print("[PASS] well-formed block extracted correctly")


def check_malformed_no_repair_raises() -> None:
    text = "\\begin{IDEA}\nmissing the closing tag"
    try:
        extract_block(text, "IDEA", repair=False)
        raise AssertionError("expected BlockExtractionError, got no exception")
    except BlockExtractionError:
        print("[PASS] malformed block with repair=False raises predictably")


def check_malformed_repair_fallback_triggers() -> None:
    text = "\\begin{IDEA}\nmissing the closing tag"
    calls: list[str] = []

    def fake_repair_fn(prompt: str) -> str:
        calls.append(prompt)
        return "\\begin{IDEA}\nrepaired content\n\\end{IDEA}"

    result = extract_block(text, "IDEA", repair_fn=fake_repair_fn)
    assert result == "repaired content", f"got {result!r}"
    assert len(calls) == 1, f"expected exactly 1 repair call, got {len(calls)}"
    print("[PASS] malformed block triggers repair fallback exactly once, uses its output")


def check_malformed_repair_fallback_still_fails() -> None:
    text = "\\begin{IDEA}\nmissing the closing tag"

    def useless_repair_fn(_prompt: str) -> str:
        return "still no tags here"

    try:
        extract_block(text, "IDEA", repair_fn=useless_repair_fn)
        raise AssertionError("expected BlockExtractionError, got no exception")
    except BlockExtractionError:
        print("[PASS] malformed block whose repair also fails raises predictably (no crash)")


def check_file_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        content = "# Data description\n\nProject code: 2019.1.01234.S\n"
        written_path = write_state_file(tmp, DESCRIPTION_FILE, content)
        assert written_path == Path(tmp) / "input_files" / DESCRIPTION_FILE
        read_back = read_state_file(tmp, DESCRIPTION_FILE)
        assert read_back == content, f"round-trip mismatch: {read_back!r} != {content!r}"
        print("[PASS] write_state_file/read_state_file round-trip byte-identical")


def check_file_roundtrip_creates_input_files_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        assert not (Path(tmp) / "input_files").exists()
        write_state_file(tmp, DESCRIPTION_FILE, "x")
        assert (Path(tmp) / "input_files").is_dir()
        print("[PASS] write_state_file creates input_files/ when missing")


def main() -> int:
    checks = [
        check_well_formed_extraction,
        check_malformed_no_repair_raises,
        check_malformed_repair_fallback_triggers,
        check_malformed_repair_fallback_still_fails,
        check_file_roundtrip,
        check_file_roundtrip_creates_input_files_dir,
    ]
    failures = 0
    for check in checks:
        try:
            check()
        except AssertionError as exc:
            failures += 1
            print(f"[FAIL] {check.__name__}: {exc}")
    print(f"\n{len(checks) - failures}/{len(checks)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
