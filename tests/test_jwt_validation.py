from datetime import datetime, timedelta, timezone

import jwt
import pytest

from levi.auth.errors import AuthenticationConfigurationError, AuthenticationError
from levi.auth.jwt import JwtValidator

SECRET = "test-secret-that-is-at-least-32-bytes-long"
WRONG_SECRET = "wrong-secret-that-is-at-least-32-bytes"


def token(**overrides):
    claims = {"sub": "user-1", "aud": "authenticated", "exp": datetime.now(timezone.utc) + timedelta(minutes=5), "email": "u@test.com"}
    claims.update(overrides)
    return jwt.encode(claims, SECRET, algorithm="HS256")


def test_valid_jwt_extracts_identity(): assert JwtValidator(secret=SECRET).validate(token()).user_id == "user-1"
def test_jwt_extracts_email(): assert JwtValidator(secret=SECRET).validate(token()).email == "u@test.com"
def test_authenticated_user_has_expiry(): assert JwtValidator(secret=SECRET).validate(token()).expires_at is not None
def test_authenticated_user_exposes_mapping_claims(): assert JwtValidator(secret=SECRET).validate(token()).claims["sub"] == "user-1"
def test_wrong_signature_rejected():
    with pytest.raises(AuthenticationError): JwtValidator(secret=WRONG_SECRET).validate(token())
def test_expired_token_rejected():
    with pytest.raises(AuthenticationError): JwtValidator(secret=SECRET).validate(token(exp=datetime.now(timezone.utc)-timedelta(seconds=1)))
def test_wrong_audience_rejected():
    with pytest.raises(AuthenticationError): JwtValidator(secret=SECRET, audience="other").validate(token())
def test_missing_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    with pytest.raises(AuthenticationConfigurationError): JwtValidator(secret="").validate(token())
