from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.activity.service import append_activity_log
from app.auth.schemas import RegisterRequest
from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import User


def create_user(db: Session, payload: RegisterRequest) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        )
    user = User(
        email=payload.email.lower(),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        phone=payload.phone,
        role=payload.role.value,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.flush()
    append_activity_log(
        db,
        actor_id=user.id,
        event_type="user.registered",
        entity_type="user",
        entity_id=user.id,
        summary=f"{user.email} registered as {user.role}",
        payload={"role": user.role},
    )
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email.lower(), User.is_active.is_(True)))
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def issue_token(user: User) -> str:
    return create_access_token(
        subject=str(user.id), claims={"role": user.role, "email": user.email}
    )


def can_self_register_role(role: UserRole) -> bool:
    return role in {UserRole.procurement_officer, UserRole.vendor, UserRole.manager}
