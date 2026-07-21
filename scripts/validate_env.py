#!/usr/bin/env python3
"""Validate LEVI deployment configuration without printing secret values."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from levi.deployment.environment import validate_environment


def main() -> int:
    result = validate_environment()
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    print("Environment validation passed" if result.valid else "Environment validation failed")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
