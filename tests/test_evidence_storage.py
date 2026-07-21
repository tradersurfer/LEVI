import hashlib
import os
from pathlib import Path

import pytest

from levi.evidence.storage.filesystem_storage import (
    EncryptedFilesystemStorage, StorageConfigurationError, StorageSecurityError,
)
from tests.evidence_helpers import encryption_key


def _storage(tmp_path, monkeypatch):
    monkeypatch.setenv("LEVI_EVIDENCE_ENCRYPTION_KEY", encryption_key())
    monkeypatch.delenv("LEVI_ALLOW_PLAINTEXT_EVIDENCE", raising=False)
    return EncryptedFilesystemStorage(tmp_path / "workspace")


def _source(tmp_path, content=b"private evidence"):
    path = tmp_path / "source.csv"
    path.write_bytes(content)
    return path


def test_file_encrypted_at_rest(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    stored = storage.store(user_id="u1", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="data.csv")
    assert stored.encrypted is True
    assert stored.encryption_version == "AES-256-GCM-v1"


def test_ciphertext_differs_from_source(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    source = _source(tmp_path)
    stored = storage.store(user_id="u1", evidence_id="ev_1", source_path=source, original_filename="data.csv")
    assert Path(stored.storage_path).read_bytes() != source.read_bytes()


def test_correct_user_retrieves_file(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    storage.store(user_id="u1", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="data.csv")
    assert storage.retrieve(user_id="u1", evidence_id="ev_1") == b"private evidence"


def test_another_user_cannot_retrieve_file(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    storage.store(user_id="u1", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="data.csv")
    with pytest.raises(FileNotFoundError):
        storage.retrieve(user_id="u2", evidence_id="ev_1")


def test_path_traversal_user_id_rejected(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    with pytest.raises(StorageSecurityError, match="user_id"):
        storage.store(user_id="../u2", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="data.csv")


def test_absolute_original_filename_rejected(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    with pytest.raises(StorageSecurityError, match="filename"):
        storage.store(user_id="u1", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="C:\\private\\data.csv")


def test_missing_encryption_key_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("LEVI_EVIDENCE_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("LEVI_ALLOW_PLAINTEXT_EVIDENCE", raising=False)
    with pytest.raises(StorageConfigurationError, match="required"):
        EncryptedFilesystemStorage(tmp_path)


def test_plaintext_mode_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("LEVI_EVIDENCE_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("LEVI_ALLOW_PLAINTEXT_EVIDENCE", "false")
    with pytest.raises(StorageConfigurationError):
        EncryptedFilesystemStorage(tmp_path)


def test_explicit_plaintext_mode_allowed_for_development(tmp_path, monkeypatch):
    monkeypatch.delenv("LEVI_EVIDENCE_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("LEVI_ALLOW_PLAINTEXT_EVIDENCE", "true")
    storage = EncryptedFilesystemStorage(tmp_path / "workspace")
    stored = storage.store(user_id="u1", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="data.csv")
    assert stored.encrypted is False


def test_sha256_stored_correctly(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    stored = storage.store(user_id="u1", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="data.csv")
    assert stored.sha256 == hashlib.sha256(b"private evidence").hexdigest()


def test_delete_removes_stored_evidence(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    storage.store(user_id="u1", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="data.csv")
    storage.delete(user_id="u1", evidence_id="ev_1")
    assert not storage.exists(user_id="u1", evidence_id="ev_1")


def test_symbolic_link_escape_rejected_where_supported(tmp_path, monkeypatch):
    storage = _storage(tmp_path, monkeypatch)
    outside = tmp_path / "outside"
    outside.mkdir()
    evidence_dir = tmp_path / "workspace" / "users" / "u1" / "evidence"
    evidence_dir.parent.mkdir(parents=True)
    try:
        os.symlink(outside, evidence_dir, target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links are unavailable in this environment")
    with pytest.raises(StorageSecurityError, match="symbolic link"):
        storage.store(user_id="u1", evidence_id="ev_1", source_path=_source(tmp_path), original_filename="data.csv")
