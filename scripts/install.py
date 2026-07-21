#!/usr/bin/env python3
"""Print reproducible installation guidance and verify supported Python."""

import sys


def main() -> int:
    if sys.version_info < (3, 11):
        print("LEVI requires Python 3.11 or newer")
        return 1
    print("Python version supported")
    print("Install with: python -m pip install -r requirements.txt")
    print("Validate with: python scripts/validate_env.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
