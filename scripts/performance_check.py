#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.performance_baseline import measure

if __name__ == "__main__":
    result = measure()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["startup_under_5s"] and result["response_under_1s"] else 1)
