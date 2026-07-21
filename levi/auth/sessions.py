"""Process-local revocation list; provider logout remains authoritative."""

from __future__ import annotations

import hashlib
from threading import RLock


class SessionRevocationStore:
    def __init__(self):
        self._revoked: set[str] = set()
        self._lock = RLock()

    @staticmethod
    def fingerprint(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def revoke(self, token: str) -> None:
        with self._lock:
            self._revoked.add(self.fingerprint(token))

    def is_revoked(self, token: str) -> bool:
        with self._lock:
            return self.fingerprint(token) in self._revoked
