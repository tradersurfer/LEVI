# Contributing

Use a focused branch, preserve paper and alert behavior, and avoid unrelated refactors. Never commit `.env`, credentials, broker data, personal evidence, caches, logs, or implementation-review reports.

Before submitting a change, run:

```bash
pytest tests -q
python -m compileall -q levi bot
python scripts/security_audit.py
git diff --check
```

Tests must be offline and deterministic. New integrations require explicit scope, safe failure behavior, and mocked tests. Report security issues privately according to [Security](SECURITY.md).
