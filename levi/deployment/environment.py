"""Deterministic environment validation with secret-safe messages."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class EnvironmentValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def validate_environment(env: Mapping[str, str] | None = None) -> EnvironmentValidation:
    values = os.environ if env is None else env
    production = values.get("LEVI_ENV", "development").lower() == "production"
    errors: list[str] = []
    warnings: list[str] = []

    if _truthy(values.get("AUTO_EXECUTE")):
        errors.append("AUTO_EXECUTE must remain false for this release")
    if values.get("TASTYTRADE_PAPER", "true").lower() != "true":
        errors.append("TASTYTRADE_PAPER must remain true")
    if production:
        for name in ("LEVI_EVIDENCE_ENCRYPTION_KEY", "LEVI_CORS_ORIGINS"):
            if not values.get(name, "").strip():
                errors.append(f"{name} is required in production")
        if values.get("LEVI_ALLOW_PLAINTEXT_EVIDENCE", "false").lower() != "false":
            errors.append("plaintext evidence storage is forbidden in production")
    elif not values.get("LEVI_EVIDENCE_ENCRYPTION_KEY"):
        warnings.append("evidence uploads require LEVI_EVIDENCE_ENCRYPTION_KEY")

    root = values.get("LEVI_WORKSPACE_ROOT", "./workspace")
    if "\x00" in root:
        errors.append("LEVI_WORKSPACE_ROOT contains an invalid character")
    elif Path(root).name in {"", ".", ".."}:
        errors.append("LEVI_WORKSPACE_ROOT must identify a dedicated directory")

    return EnvironmentValidation(not errors, tuple(errors), tuple(warnings))
