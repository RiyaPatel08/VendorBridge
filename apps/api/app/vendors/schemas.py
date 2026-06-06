from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import LifecycleStage, VendorStatus
from app.common.validators import is_valid_email
from app.vendors.validators import normalize_gstin, normalize_pan


def _normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if not is_valid_email(normalized):
        raise ValueError("Invalid email format")
    return normalized


class VendorCategoryRead(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class VendorBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    legal_name: str | None = Field(default=None, max_length=200)
    category_id: int
    gstin: str = Field(min_length=15, max_length=15)
    pan: str | None = Field(default=None, min_length=10, max_length=10)
    state: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=100)
    contact_name: str = Field(min_length=2, max_length=120)
    contact_email: str = Field(max_length=255)
    contact_phone: str = Field(min_length=7, max_length=32)
    status: VendorStatus = VendorStatus.pending
    completed_orders_count: int = Field(default=0, ge=0)
    rating: Decimal = Field(default=Decimal("0.00"), ge=0, le=5)
    reliability_score: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    delivery_score: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    completion_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    satisfaction_score: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    compliance_notes: str | None = None
    custom_attributes: dict = Field(default_factory=dict)

    @field_validator("gstin")
    @classmethod
    def normalize_gstin_value(cls, value: str) -> str:
        return normalize_gstin(value)

    @field_validator("pan")
    @classmethod
    def normalize_pan_value(cls, value: str | None) -> str | None:
        return normalize_pan(value)

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, value: str) -> str:
        return _normalize_email(value)


class VendorCreate(VendorBase):
    pass


class VendorSelfRegister(BaseModel):
    """Vendor self-registration — contact info is derived from the authenticated user."""

    name: str = Field(min_length=2, max_length=160)
    legal_name: str | None = Field(default=None, max_length=200)
    category_id: int
    gstin: str = Field(min_length=15, max_length=15)
    pan: str | None = Field(default=None, min_length=10, max_length=10)
    state: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=100)
    contact_phone: str = Field(min_length=7, max_length=32)
    compliance_notes: str | None = None

    @field_validator("gstin")
    @classmethod
    def normalize_gstin_value(cls, value: str) -> str:
        return normalize_gstin(value)

    @field_validator("pan")
    @classmethod
    def normalize_pan_value(cls, value: str | None) -> str | None:
        return normalize_pan(value)


class VendorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    legal_name: str | None = Field(default=None, max_length=200)
    category_id: int | None = None
    gstin: str | None = Field(default=None, min_length=15, max_length=15)
    pan: str | None = Field(default=None, min_length=10, max_length=10)
    state: str | None = Field(default=None, min_length=2, max_length=80)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    contact_name: str | None = Field(default=None, min_length=2, max_length=120)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, min_length=7, max_length=32)
    status: VendorStatus | None = None
    completed_orders_count: int | None = Field(default=None, ge=0)
    rating: Decimal | None = Field(default=None, ge=0, le=5)
    reliability_score: Decimal | None = Field(default=None, ge=0, le=100)
    delivery_score: Decimal | None = Field(default=None, ge=0, le=100)
    completion_rate: Decimal | None = Field(default=None, ge=0, le=100)
    satisfaction_score: Decimal | None = Field(default=None, ge=0, le=100)
    compliance_notes: str | None = None
    custom_attributes: dict | None = None

    @field_validator("gstin")
    @classmethod
    def normalize_gstin_value(cls, value: str | None) -> str | None:
        return normalize_gstin(value) if value else None

    @field_validator("pan")
    @classmethod
    def normalize_pan_value(cls, value: str | None) -> str | None:
        return normalize_pan(value)

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, value: str | None) -> str | None:
        return _normalize_email(value) if value is not None else None


class VendorRead(BaseModel):
    id: int
    name: str
    legal_name: str | None
    category_id: int
    gstin: str
    pan: str | None
    state: str
    city: str
    contact_name: str
    contact_email: str
    contact_phone: str
    status: VendorStatus
    lifecycle_stage: LifecycleStage
    completed_orders_count: int
    rating: Decimal
    reliability_score: Decimal
    delivery_score: Decimal
    completion_rate: Decimal
    satisfaction_score: Decimal
    is_gstin_verified: bool
    is_pan_verified: bool
    compliance_notes: str | None
    custom_attributes: dict = Field(default_factory=dict)
    compliance_badge: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VendorListResponse(BaseModel):
    items: list[VendorRead]
    page: int
    page_size: int
    total: int
