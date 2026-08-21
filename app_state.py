"""App-level local state: a single password lock and a generation history log.

Distinct from state.py (which handles *per-project* markdown files inside a
project_dir/input_files/ folder): this is *app-level* state that has to
survive across every project and outlive any one project folder, so it's
stored outside both the current project directory and the git repo entirely
-- in the user's home directory, the same way a native desktop app would
keep its own config. Nothing here is ever written inside this checkout, so
neither the password hash nor the run history can end up in git by accident.

Threat model: this is a casual local lock -- it keeps out someone else who
uses the same shared PC, not a hardened credential vault. Anyone with
filesystem access to APP_DIR can delete auth.json to reset the password, or
read history.json directly. That matches what was asked for (a single local
password, no server, no multi-user accounts) rather than over-building a
security boundary nothing here needs. Password hashing is stdlib-only
(hashlib.pbkdf2_hmac), matching gui_app.py's own "Tkinter, stdlib only --
nothing extra to install" design.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path

APP_DIR = Path.home() / ".alma_thesis_planner"
AUTH_FILE = APP_DIR / "auth.json"
HISTORY_FILE = APP_DIR / "history.json"

# OWASP's 2023 minimum-recommended iteration count for PBKDF2-HMAC-SHA256.
_PBKDF2_ITERATIONS = 260_000


def has_password() -> bool:
    return AUTH_FILE.exists()


def set_password(password: str) -> None:
    """(Re)set the app's single local password, overwriting any existing one."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    APP_DIR.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(
        json.dumps({"salt": salt.hex(), "hash": digest.hex(), "iterations": _PBKDF2_ITERATIONS}),
        encoding="utf-8",
    )


def verify_password(password: str) -> bool:
    """False both for a wrong password and for no password having been set yet."""
    if not AUTH_FILE.exists():
        return False
    data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    salt = bytes.fromhex(data["salt"])
    iterations = data.get("iterations", _PBKDF2_ITERATIONS)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    # Constant-time compare -- a naive == leaks timing information about how
    # many leading bytes of the hash matched.
    return hmac.compare_digest(digest.hex(), data["hash"])


@dataclass
class HistoryEntry:
    timestamp: str  # ISO 8601 (UTC) -- GUI code formats this for local-time display
    provider: str  # WizardConfig.provider key, e.g. "claude", "claude_free", "gemini"
    model: str
    scope: str  # WizardConfig.scope key, e.g. "quick_summary"
    project_code: str
    target: str
    project_dir: str
    status: str  # WizardResult.status: "done", "partial", or "short_circuited"


def append_history_entry(entry: HistoryEntry) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    entries = load_history()
    entries.append(asdict(entry))
    HISTORY_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def load_history() -> list[dict]:
    """Oldest-first, matching append order. Empty (not an error) if the file
    is missing or unreadable -- a corrupt/missing history log shouldn't block
    using the app, just leave the history view empty."""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
