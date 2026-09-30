from jose import jwt
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification():
    raw_pass = "SecureStudioPassword123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert hashed.startswith("pbkdf2:sha256:")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_access_token_generation():
    subject = "user-uuid-12345"
    token = create_access_token(subject=subject)
    assert isinstance(token, str)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == subject
    assert decoded["type"] == "access"
    assert "exp" in decoded


def test_jwt_refresh_token_generation():
    subject = "user-uuid-67890"
    token = create_refresh_token(subject=subject)
    assert isinstance(token, str)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == subject
    assert decoded["type"] == "refresh"
    assert "exp" in decoded
