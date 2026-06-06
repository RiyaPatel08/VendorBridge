from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.activity.service import append_activity_log
from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from app.auth.service import authenticate_user, can_self_register_role, create_user, issue_token
from app.common.dependencies import get_current_user
from app.core.rate_limit import RateLimitExceeded, login_rate_limiter
from app.db.session import get_db
from app.models.entities import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if not can_self_register_role(payload.role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role cannot self-register"
        )
    user = create_user(db, payload)
    token = issue_token(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    key = f"{request.client.host if request.client else 'unknown'}:{payload.email.lower()}"
    try:
        login_rate_limiter.check(key)
    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        ) from None

    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    append_activity_log(
        db,
        actor_id=user.id,
        event_type="auth.login",
        entity_type="user",
        entity_id=user.id,
        summary=f"{user.email} signed in",
        payload={"role": user.role},
    )
    token = issue_token(user)
    db.commit()
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    append_activity_log(
        db,
        actor_id=None,
        event_type="auth.password_reset_requested",
        entity_type="user",
        entity_id=None,
        summary="Password reset placeholder requested",
        payload={"email": payload.email.lower()},
    )
    db.commit()
    return ForgotPasswordResponse(
        message="If an account exists, password reset instructions will be queued."
    )
