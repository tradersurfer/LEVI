#!/usr/bin/env python3
"""Offline ASGI startup and health-response baseline."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def measure() -> dict[str, float | bool]:
    started = perf_counter()
    from bot.status_api import app
    import asyncio
    import httpx

    startup_seconds = perf_counter() - started

    async def probe() -> float:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            before = perf_counter()
            response = await client.get("/health")
            elapsed = perf_counter() - before
            response.raise_for_status()
            return elapsed

    response_seconds = asyncio.run(probe())
    return {
        "startup_seconds": startup_seconds,
        "health_response_seconds": response_seconds,
        "startup_under_5s": startup_seconds < 5,
        "response_under_1s": response_seconds < 1,
    }


if __name__ == "__main__":
    result = measure()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["startup_under_5s"] and result["response_under_1s"] else 1)
