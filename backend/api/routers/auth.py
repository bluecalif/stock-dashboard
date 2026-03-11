"""Auth endpoints — signup, login, refresh, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from api.services import auth_service
from db.models import User

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> UserResponse:
    user = auth_service.signup(
        db, email=body.email, password=body.password, nickname=body.nickname,
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    tokens = auth_service.login(db, email=body.email, password=body.password)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    tokens = auth_service.refresh(db, refresh_token=body.refresh_token)
    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
