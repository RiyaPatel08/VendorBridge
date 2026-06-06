from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.common.enums import QuotationStatus
from app.rfqs.contracts import QuotationDraftContract


class QuotationItemRead(BaseModel):
    id: int
    rfq_item_id: int
    item_name: str | None = None
    quantity: Decimal
    unit_price: Decimal
    gst_percent: Decimal
    available_quantity: Decimal
    additional_quantity: Decimal
    additional_available_days: int | None
    line_subtotal: Decimal
    line_gst: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class QuotationRead(BaseModel):
    id: int
    rfq_id: int
    vendor_id: int
    vendor_name: str | None = None
    status: QuotationStatus
    delivery_days: int
    payment_terms_days: int
    notes: str | None
    subtotal: Decimal
    gst_total: Decimal
    grand_total: Decimal
    best_value_score: Decimal
    score_breakdown: dict | None
    submitted_at: datetime | None
    items: list[QuotationItemRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuotationListItem(BaseModel):
    id: int
    rfq_id: int
    rfq_title: str
    vendor_id: int
    vendor_name: str
    status: QuotationStatus
    grand_total: Decimal
    delivery_days: int
    best_value_score: Decimal
    submitted_at: datetime | None


class ComparisonRow(BaseModel):
    quotation_id: int
    vendor_id: int
    vendor_name: str
    vendor_rating: Decimal
    lifecycle_stage: str
    status: QuotationStatus
    subtotal: Decimal
    gst_total: Decimal
    grand_total: Decimal
    delivery_days: int
    payment_terms_days: int
    best_value_score: Decimal
    score_breakdown: dict
    is_lowest_price: bool
    coverage_label: str


class ComparisonResponse(BaseModel):
    rfq_id: int
    rfq_title: str
    rows: list[ComparisonRow]


QuotationDraft = QuotationDraftContract
