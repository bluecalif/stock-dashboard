"""Tests for auth router endpoints — signup, login, refresh, me."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def client(mock_db):
    from api.dependencies import get_db

    def _override():
        yield mock_db

    app.dependency_overrides[get_db] = _override
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _make_user(
    user_id=None, email="test@example.com", nickname="tester", is_active=True,
):
    u = MagicMock()
    u.id = user_id or uuid.uuid4()
    u.email = email
    u.nickname = nickname
    u.is_active = is_active
    u.created_at = datetime.now(timezone.utc)
    u.updated_at = datetime.now(timezone.utc)
    return u


# --- POST /v1/auth/signup ---


@patch("api.routers.auth.auth_service")
def test_signup_success(mock_service, client):
    fake_user = _make_user()
    mock_service.signup.return_value = fake_user

    resp = client.post("/v1/auth/signup", json={
        "email": "new@example.com", "password": "pass123", "nickname": "nick",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@patch("api.routers.auth.auth_service")
def test_signup_invalid_email(mock_service, client):
    resp = client.post("/v1/auth/signup", json={
        "email": "not-an-email", "password": "pass123",
    })
    assert resp.status_code == 422


# --- POST /v1/auth/login ---


@patch("api.routers.auth.auth_service")
def test_login_success(mock_service, client):
    mock_service.login.return_value = {
        "access_token": "acc123",
        "refresh_token": "ref456",
        "token_type": "bearer",
    }

    resp = client.post("/v1/auth/login", json={
        "email": "test@example.com", "password": "pass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "acc123"
    assert data["token_type"] == "bearer"


# --- POST /v1/auth/refresh ---


@patch("api.routers.auth.auth_service")
def test_refresh_success(mock_service, client):
    mock_service.refresh.return_value = {
        "access_token": "new_acc",
        "refresh_token": "new_ref",
        "token_type": "bearer",
    }

    resp = client.post("/v1/auth/refresh", json={"refresh_token": "old_ref"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "new_acc"


# --- GET /v1/auth/me ---


def test_me_no_token(client):
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token(client, mock_db):
    from api.dependencies import get_current_user

    fake_user = _make_user()

    def _override_user():
        return fake_user

    app.dependency_overrides[get_current_user] = _override_user

    resp = client.get("/v1/auth/me", headers={"Authorization": "Bearer valid-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"

    del app.dependency_overrides[get_current_user]


# --- DELETE /v1/auth/me (withdraw) ---


@patch("api.routers.auth.auth_service")
def test_withdraw_success(mock_service, client, mock_db):
    from api.dependencies import get_current_user

    fake_user = _make_user()

    def _override_user():
        return fake_user

    app.dependency_overrides[get_current_user] = _override_user

    resp = client.request(
        "DELETE", "/v1/auth/me",
        content=json.dumps({"password": "pass123"}),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 204
    mock_service.withdraw.assert_called_once_with(
        mock_db, user=fake_user, password="pass123",
    )

    del app.dependency_overrides[get_current_user]


def test_withdraw_no_token(client):
    resp = client.request(
        "DELETE", "/v1/auth/me",
        content=json.dumps({"password": "pass123"}),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 401
