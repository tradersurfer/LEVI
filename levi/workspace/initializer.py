"""Create isolated, configurable user workspaces."""

from __future__ import annotations

import json
import os
from pathlib import Path

from levi.profiles.models import UserTradingProfile


MEMORY_CONTENT = """# User Memory

This memory is user-specific and should only contain information derived from this user's activity.

## Trading History

## Preferred Tickers

## Observed Habits

## Goals

## Prior Decisions and Lessons

## Portfolio Context
"""

MOOD_CONTENT = """# LEVI Mood

- Calm
- Analytical
- Evidence-first
- Patient
- Direct
- No hype
- No chasing
- Prefer no trade over a weak trade
- Separate facts from assumptions
"""

BEHAVIOR_CONTENT = """# LEVI Behavior

- Never invent market data.
- Never invent portfolio values.
- Never bypass deterministic risk rules.
- Always identify missing evidence.
- Always produce "What You Need" before research or analysis.
- Use tools only when relevant.
- Preserve user privacy.
- Do not execute without the configured approval level.
- Evidence must be traceable to its source.
"""


def get_workspace_root(root: str | Path | None = None) -> Path:
    return Path(root or os.getenv("LEVI_WORKSPACE_ROOT", "./workspace")).expanduser().resolve()


def _safe_user_id(user_id: str) -> str:
    if not user_id or user_id in {".", ".."} or any(char in user_id for char in ("/", "\\")):
        raise ValueError("user_id must be a non-empty path-safe identifier")
    return user_id


def initialize_user_workspace(
    profile: UserTradingProfile, root: str | Path | None = None
) -> Path:
    user_dir = get_workspace_root(root) / "users" / _safe_user_id(profile.user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "evidence").mkdir(exist_ok=True)
    for name, content in {
        "MEMORY.md": MEMORY_CONTENT,
        "MOOD.md": MOOD_CONTENT,
        "BEHAVIOR.md": BEHAVIOR_CONTENT,
    }.items():
        path = user_dir / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    (user_dir / "PROFILE.json").write_text(
        json.dumps(profile.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8"
    )
    return user_dir


def load_user_profile(user_id: str, root: str | Path | None = None) -> UserTradingProfile:
    profile_path = get_workspace_root(root) / "users" / _safe_user_id(user_id) / "PROFILE.json"
    return UserTradingProfile.model_validate_json(profile_path.read_text(encoding="utf-8"))
