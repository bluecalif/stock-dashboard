"""Tests for auth_service — password hashing, JWT, signup/login/refresh."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    login,
    refresh,
    signup,
    verify_password,
)


def test_hash_and_verify_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token():
    uid = uuid.uuid4()
    token = create_access_token(uid)
    decoded_uid = decode_access_token(token)
    assert decoded_uid == uid


def test_decode_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("invalid.token.here")
    assert exc_info.value.status_code == 401


# --- signup ---


@patch("api.services.auth_service.user_repo")
def test_signup_success(mock_user_repo):
    db = MagicMock(spec=Session)
    mock_user_repo.get_by_email.return_value = None

    fake_user = MagicMock()
    fake_user.id = uuid.uuid4()
    fake_user.email = "test@example.com"
    mock_user_repo.create_user.return_value = fake_user

    result = signup(db, email="test@example.com", password="pass123")
    assert result == fake_user
    mock_user_repo.create_user.assert_called_once()
    db.commit.assert_called_once()


@patch("api.services.auth_service.user_repo")
def test_signup_duplicate_email(mock_user_repo):
    db = MagicMock(spec=Session)
    mock_user_repo.get_by_email.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        signup(db, email="dup@example.com", password="pass123")
    assert exc_info.value.status_code == 409


# --- login ---


@patch("api.services.auth_service.session_repo")
@patch("api.services.auth_service.user_repo")
def test_login_success(mock_user_repo, mock_session_repo):
    db = MagicMock(spec=Session)
    fake_user = MagicMock()
    fake_user.id = uuid.uuid4()
    fake_user.is_active = True
    fake_user.password_hash = hash_password("correct")
    mock_user_repo.get_by_email.return_value = fake_user

    result = login(db, email="test@example.com", password="correct")
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"
    mock_session_repo.create_session.assert_called_once()


@patch("api.services.auth_service.user_repo")
def test_login_wrong_password(mock_user_repo):
    db = MagicMock(spec=Session)
    fake_user = MagicMock()
    fake_user.password_hash = hash_password("correct")
    mock_user_repo.get_by_email.return_value = fake_user

    with pytest.raises(HTTPException) as exc_info:
        login(db, email="test@example.com", password="wrong")
    assert exc_info.value.status_code == 401


@patch("api.services.auth_service.user_repo")
def test_login_nonexistent_user(mock_user_repo):
    db = MagicMock(spec=Session)
    mock_user_repo.get_by_email.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        login(db, email="noone@example.com", password="pass")
    assert exc_info.value.status_code == 401


# --- refresh ---


@patch("api.services.auth_service.session_repo")
@patch("api.services.auth_service.user_repo")
def test_refresh_success(mock_user_repo, mock_session_repo):
    db = MagicMock(spec=Session)
    fake_session = MagicMock()
    fake_session.id = uuid.uuid4()
    fake_session.user_id = uuid.uuid4()
    mock_session_repo.get_by_token_hash.return_value = fake_session

    fake_user = MagicMock()
    fake_user.id = fake_session.user_id
    fake_user.is_active = True
    mock_user_repo.get_by_id.return_value = fake_user

    result = refresh(db, refresh_token="some-token")
    assert "access_token" in result
    assert "refresh_token" in result
    mock_session_repo.delete_session.assert_called_once_with(db, fake_session.id)
    mock_session_repo.create_session.assert_called_once()


@patch("api.services.auth_service.session_repo")
def test_refresh_invalid_token(mock_session_repo):
    db = MagicMock(spec=Session)
    mock_session_repo.get_by_token_hash.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        refresh(db, refresh_token="bad-token")
    assert exc_info.value.status_code == 401
