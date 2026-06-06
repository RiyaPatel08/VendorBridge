from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.common.enums import RFQStatus
from app.rfqs.contracts import RFQCreateContract, RFQItemCreate


class RFQItemRead(BaseModel):
    id: int
    item_name: str
    hsn_sac: str
    quantity: Decimal
    unit: str
    target_price: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class RFQInviteRead(BaseModel):
    id: int
    vendor_id: int
    vendor_name: str
    status: str
    discovery_source: str
    vendor_lifecycle_stage_at_invite: str


class RFQRead(BaseModel):
    id: int
    title: str
    category_id: int
    category_name: str | None = None
    description: str | None
    deadline: datetime
    status: RFQStatus
    created_by_id: int
    items: list[RFQItemRead] = []
    invites: list[RFQInviteRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RFQListItem(BaseModel):
    id: int
    title: str
    category_name: str | None
    deadline: datetime
    status: RFQStatus
    quote_count: int
    invite_count: int
    created_at: datetime


class RFQUpdate(BaseModel):
    title: str | None = None
    category_id: int | None = None
    description: str | None = None
    deadline: datetime | None = None
    vendor_ids: list[int] | None = None
    items: list[RFQItemCreate] | None = None


class SelectQuotationRequest(BaseModel):
    quotation_id: int


RFQCreate = RFQCreateContract
