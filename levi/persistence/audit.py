"""Audit writer that deliberately excludes secrets and token values."""

from typing import Any

from .repositories import AuditRepository


SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "secret", "encryption_key"}


def sanitize(details: dict[str, Any]) -> dict[str, Any]:
    return {
        key: ("[REDACTED]" if key.lower() in SENSITIVE_KEYS or key.lower().endswith("_encryption_key") else value)
        for key, value in details.items()
    }


def record_audit(repository: AuditRepository, *, user_id: str, action: str,
                 entity_type: str, entity_id: str | None = None,
                 details: dict[str, Any] | None = None):
    return repository.add(user_id, action=action, entity_type=entity_type,
                          entity_id=entity_id, details=sanitize(details or {}))
