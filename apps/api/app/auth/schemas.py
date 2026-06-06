from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import UserRole
from app.common.validators import is_valid_email


def _normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if not is_valid_email(normalized):
        raise ValueError("Invalid email format")
    return normalized


class UserRead(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: str = Field(max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    role: UserRole = UserRole.procurement_officer
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ForgotPasswordRequest(BaseModel):
    email: str = Field(max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class ForgotPasswordResponse(BaseModel):
    message: str
