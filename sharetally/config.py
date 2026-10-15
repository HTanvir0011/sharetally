"""Runtime settings, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    db_path: str = field(default_factory=lambda: os.environ.get("SHARETALLY_DB", str(ROOT / "data" / "sharetally.db")))
    # Demo clock: the engine evaluates "as of" this date so results are reproducible.
    as_of: str | None = field(default_factory=lambda: os.environ.get("SHARETALLY_AS_OF") or None)
    secure_cookies: bool = field(default_factory=lambda: _flag("SHARETALLY_SECURE_COOKIES"))
    show_demo_logins: bool = field(default_factory=lambda: _flag("SHARETALLY_SHOW_DEMO_LOGINS", "1"))
    pbkdf2_iterations: int = field(default_factory=lambda: int(os.environ.get("SHARETALLY_PBKDF2_ITERATIONS", "600000")))
    session_hours: int = field(default_factory=lambda: int(os.environ.get("SHARETALLY_SESSION_HOURS", "8")))
    ai_enabled: bool = field(default_factory=lambda: _flag("SHARETALLY_AI", "1"))
    ai_model: str = field(default_factory=lambda: os.environ.get("SHARETALLY_AI_MODEL", "claude-opus-5-5"))
    # Demo accounts (synthetic prototype only). Override every password for any public deployment.
    demo_users: tuple = field(default_factory=lambda: (
        ("reviewer.demo", "reviewer", "AC Land office reviewer (demo)",
         os.environ.get("SHARETALLY_PW_REVIEWER", "review-demo-2026")),
        ("clerk.demo", "clerk", "Sub-Registry clerk (demo)",
         os.environ.get("SHARETALLY_PW_CLERK", "clerk-demo-2026")),
        ("auditor.demo", "auditor", "Auditor, read-only (demo)",
         os.environ.get("SHARETALLY_PW_AUDITOR", "audit-demo-2026")),
    ))
