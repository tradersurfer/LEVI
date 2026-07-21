# Contributing

Use a focused branch, preserve paper and alert behavior, and avoid unrelated refactors. Never commit `.env`, credentials, broker data, or personal evidence.

Before submitting a change, run:

```bash
pytest tests -q
python -m compileall -q levi bot
python scripts/security_audit.py
git diff --check
```

Tests must be offline and deterministic. New integrations require explicit scope, safe failure behavior, and mocked tests. Report security issues privately per `SECURITY.md`.
