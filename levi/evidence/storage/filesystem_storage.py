"""Authenticated, encrypted filesystem evidence storage."""

from __future__ import annotations

import base64
import hashlib
import os
import re
from pathlib import Path, PureWindowsPath

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from levi.evidence.storage.base import StoredEvidenceFile
from levi.workspace.initializer import get_workspace_root


class StorageConfigurationError(RuntimeError):
    pass


class StorageSecurityError(ValueError):
    pass


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAGIC = b"LEVI-AESGCM-1\x00"


def _validate_identifier(value: str, label: str) -> str:
    if not value or "\x00" in value or not _SAFE_ID.fullmatch(value) or value in {".", ".."}:
        raise StorageSecurityError(f"invalid {label}")
    return value


def _validate_original_filename(filename: str) -> str:
    if (
        not filename or "\x00" in filename or Path(filename).is_absolute()
        or PureWindowsPath(filename).is_absolute() or Path(filename).name != filename
        or "/" in filename or "\\" in filename
    ):
        raise StorageSecurityError("invalid original filename")
    return filename


def _decode_key(value: str) -> bytes:
    try:
        padding = "=" * (-len(value) % 4)
        key = base64.urlsafe_b64decode(value + padding)
    except Exception as exc:
        raise StorageConfigurationError("evidence encryption key is invalid") from exc
    if len(key) != 32:
        raise StorageConfigurationError("evidence encryption key must decode to 32 bytes")
    return key


class EncryptedFilesystemStorage:
    encryption_version = "AES-256-GCM-v1"

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = get_workspace_root(root)
        configured_key = os.getenv("LEVI_EVIDENCE_ENCRYPTION_KEY", "").strip()
        self.allow_plaintext = os.getenv("LEVI_ALLOW_PLAINTEXT_EVIDENCE", "false").lower() == "true"
        if configured_key:
            self.key = _decode_key(configured_key)
        elif self.allow_plaintext:
            self.key = None
        else:
            raise StorageConfigurationError("evidence encryption is required but no valid key is configured")

    def _directory(self, user_id: str, *, create: bool = False) -> Path:
        safe_user = _validate_identifier(user_id, "user_id")
        root = self.root.resolve()
        directory = root / "users" / safe_user / "evidence"
        if directory.exists() and directory.is_symlink():
            raise StorageSecurityError("evidence directory may not be a symbolic link")
        if create:
            directory.mkdir(parents=True, exist_ok=True)
        try:
            directory.resolve().relative_to(root)
        except ValueError as exc:
            raise StorageSecurityError("evidence storage path escapes workspace root") from exc
        if directory.is_symlink():
            raise StorageSecurityError("evidence directory may not be a symbolic link")
        return directory

    def _path(self, user_id: str, evidence_id: str, *, create: bool = False) -> Path:
        safe_evidence = _validate_identifier(evidence_id, "evidence_id")
        suffix = ".levi" if self.key is not None else ".plain"
        return self._directory(user_id, create=create) / f"{safe_evidence}{suffix}"

    def store(
        self, *, user_id: str, evidence_id: str, source_path: Path,
        original_filename: str,
    ) -> StoredEvidenceFile:
        _validate_original_filename(original_filename)
        if not source_path.is_file() or source_path.is_symlink():
            raise StorageSecurityError("source must be a regular file")
        target = self._path(user_id, evidence_id, create=True)
        if target.exists() or target.is_symlink():
            raise FileExistsError("evidence file already exists")
        plaintext = source_path.read_bytes()
        digest = hashlib.sha256(plaintext).hexdigest()
        if self.key is not None:
            nonce = os.urandom(12)
            associated_data = f"{user_id}:{evidence_id}".encode("utf-8")
            stored_bytes = _MAGIC + nonce + AESGCM(self.key).encrypt(nonce, plaintext, associated_data)
            encrypted = True
            version = self.encryption_version
        else:
            stored_bytes = plaintext
            encrypted = False
            version = None
        with target.open("xb") as handle:
            handle.write(stored_bytes)
        return StoredEvidenceFile(
            evidence_id=evidence_id,
            user_id=user_id,
            storage_path=str(target),
            original_filename=original_filename,
            stored_filename=target.name,
            size_bytes=len(plaintext),
            sha256=digest,
            encrypted=encrypted,
            encryption_version=version,
        )

    def retrieve(self, *, user_id: str, evidence_id: str) -> bytes:
        path = self._path(user_id, evidence_id)
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError("evidence file not found")
        stored = path.read_bytes()
        if self.key is None:
            return stored
        if not stored.startswith(_MAGIC) or len(stored) <= len(_MAGIC) + 12:
            raise StorageSecurityError("encrypted evidence file is invalid")
        nonce_start = len(_MAGIC)
        nonce = stored[nonce_start:nonce_start + 12]
        ciphertext = stored[nonce_start + 12:]
        associated_data = f"{user_id}:{evidence_id}".encode("utf-8")
        return AESGCM(self.key).decrypt(nonce, ciphertext, associated_data)

    def delete(self, *, user_id: str, evidence_id: str) -> None:
        path = self._path(user_id, evidence_id)
        if path.exists():
            if path.is_symlink():
                raise StorageSecurityError("refusing to delete symbolic link")
            path.unlink()

    def exists(self, *, user_id: str, evidence_id: str) -> bool:
        path = self._path(user_id, evidence_id)
        return path.is_file() and not path.is_symlink()
