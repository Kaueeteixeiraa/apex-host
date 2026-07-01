from datetime import timedelta

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import create_access_token, decrypt_secret, encrypt_secret
from app.services.validators import validate_branch, validate_command, validate_domain, validate_slug


def test_validators_accept_safe_values():
    assert validate_slug("meu-projeto-1") == "meu-projeto-1"
    assert validate_branch("feature/deploy-v1") == "feature/deploy-v1"
    assert validate_domain("app.example.com") == "app.example.com"
    assert validate_command("npm run build") == "npm run build"


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (validate_slug, "../root"),
        (validate_branch, "../main"),
        (validate_domain, "http://example.com"),
        (validate_command, "npm install && cat .env"),
    ],
)
def test_validators_reject_unsafe_values(validator, value):
    with pytest.raises(ValueError):
        validator(value)


def test_token_uses_effective_jwt_secret():
    settings = get_settings()
    token = create_access_token("123", timedelta(minutes=5))
    payload = jwt.decode(token, settings.effective_jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "123"


def test_secret_encryption_roundtrip():
    encrypted = encrypt_secret("super-secret-value")
    assert encrypted != "super-secret-value"
    assert decrypt_secret(encrypted) == "super-secret-value"
