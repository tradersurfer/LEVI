#!/usr/bin/env python3
"""Small offline release audit; complements dependency and platform scanning."""

from __future__ import annotations

import re
from pathlib import Path

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|password)\s*=\s*['\"][^'\"]{12,}['\"]"),
)
SKIP_PARTS = {".git", ".venv", "node_modules", "workspace", "tests"}


def audit(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.name == ".env" or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            findings.append(f"forbidden release file: {path.relative_to(root)}")
            continue
        if path.suffix.lower() not in {".py", ".md", ".yml", ".yaml", ".json", ".txt", ".example"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            findings.append(f"possible embedded secret: {path.relative_to(root)}")
    return findings


if __name__ == "__main__":
    issues = audit(Path(__file__).resolve().parents[1])
    print("\n".join(issues) if issues else "Security audit passed")
    raise SystemExit(1 if issues else 0)
