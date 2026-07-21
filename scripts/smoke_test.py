#!/usr/bin/env python3
import json
import os
import urllib.request

def probe(base_url: str) -> dict[str, str]:
    results = {}
    for endpoint in ("/health", "/ready"):
        with urllib.request.urlopen(base_url.rstrip("/") + endpoint, timeout=5) as response:
            results[endpoint] = json.load(response)["status"]
    return results

if __name__ == "__main__":
    print(json.dumps(probe(os.getenv("LEVI_BASE_URL", "http://127.0.0.1:8000")), indent=2))
