from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import decode_access_token
from app.db.optimizations import set_rls_context
from app.db.session import get_db
from app.models.entities import User, Vendor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _bind_tenant_context(db: Session, user: User) -> None:
    """Push the principal into the DB session for row-level security.

    Vendor users are mapped to their vendor record by contact email so the RLS
    policies can isolate quotations/invites to that single vendor. For all other
    roles no vendor id is bound, which the policy treats as full visibility.
    """

    vendor_id: int | None = None
    if user.role == UserRole.vendor.value:
        vendor_id = db.scalar(select(Vendor.id).where(Vendor.contact_email == user.email))
    set_rls_context(db, role=user.role, vendor_id=vendor_id)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_error
        user_id = int(subject)
    except (jwt.PyJWTError, ValueError):
        raise credentials_error from None

    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise credentials_error
    _bind_tenant_context(db, user)
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in {role.value for role in roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
            )
        return current_user

    return dependency
