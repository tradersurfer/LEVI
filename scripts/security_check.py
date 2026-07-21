#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.security_audit import audit

if __name__ == "__main__":
    issues = audit(Path(__file__).resolve().parents[1])
    print("\n".join(issues) if issues else "Security check passed")
    raise SystemExit(1 if issues else 0)
