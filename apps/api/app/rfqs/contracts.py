from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.vendors.validators import is_valid_hsn_sac


class RFQItemCreate(BaseModel):
    item_name: str = Field(min_length=2, max_length=180)
    hsn_sac: str = Field(min_length=4, max_length=8)
    quantity: Decimal = Field(gt=0)
    unit: str = Field(default="NOS", min_length=1, max_length=24)
    target_price: Decimal | None = Field(default=None, ge=0)

    @field_validator("hsn_sac")
    @classmethod
    def validate_hsn_sac(cls, value: str) -> str:
        if not is_valid_hsn_sac(value):
            raise ValueError("HSN/SAC must be 4, 6, or 8 digits")
        return value


class RFQCreateContract(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    category_id: int
    description: str | None = None
    deadline: datetime
    vendor_ids: list[int] = Field(min_length=1)
    items: list[RFQItemCreate] = Field(min_length=1)


class QuotationItemDraftContract(BaseModel):
    rfq_item_id: int
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    gst_percent: Decimal = Field(default=Decimal("18.00"), ge=0)
    available_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    additional_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    additional_available_days: int | None = Field(default=None, ge=0)


class QuotationDraftContract(BaseModel):
    rfq_id: int
    vendor_id: int
    delivery_days: int = Field(ge=0)
    payment_terms_days: int = Field(default=30, ge=0)
    notes: str | None = None
    items: list[QuotationItemDraftContract] = Field(min_length=1)


class ComparisonScoreBreakdown(BaseModel):
    price_score: Decimal
    delivery_score: Decimal
    vendor_rating_score: Decimal
    compliance_score: Decimal
    payment_terms_score: Decimal


class ComparisonRowContract(BaseModel):
    quotation_id: int
    vendor_id: int
    vendor_name: str
    grand_total: Decimal
    delivery_days: int
    best_value_score: Decimal
    is_lowest_price: bool
    score_breakdown: ComparisonScoreBreakdown
