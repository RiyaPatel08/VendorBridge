from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ApprovalStatus


class ApprovalDecision(BaseModel):
    remarks: str = Field(min_length=1, max_length=500)


class ApprovalStepRead(BaseModel):
    id: int
    approver_id: int
    approver_name: str = ""
    sequence: int
    status: ApprovalStatus
    remarks: str | None
    decided_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ApprovalRead(BaseModel):
    id: int
    rfq_id: int
    rfq_title: str = ""
    quotation_id: int
    vendor_id: int = 0
    vendor_name: str = ""
    requested_by_id: int
    status: ApprovalStatus
    risk_tier: str | None
    risk_breakdown: dict | None
    budget_impact: dict | None
    policy_reasons: list[str] | None
    remarks: str | None
    quote_total: Decimal = Decimal("0.00")
    steps: list[ApprovalStepRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalListItem(BaseModel):
    id: int
    rfq_title: str
    vendor_name: str
    status: ApprovalStatus
    quote_total: Decimal
    risk_tier: str | None
    created_at: datetime
