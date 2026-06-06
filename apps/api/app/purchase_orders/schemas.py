from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderItemRead(BaseModel):
    id: int
    item_name: str
    hsn_sac: str
    quantity: Decimal
    unit_price: Decimal
    received_quantity: Decimal
    accepted_quantity: Decimal

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderRead(BaseModel):
    id: int
    po_number: str
    approval_request_id: int | None
    vendor_id: int
    vendor_name: str = ""
    status: str
    acceptance_status: str
    delivery_status: str
    subtotal: Decimal
    gst_total: Decimal
    grand_total: Decimal
    items: list[PurchaseOrderItemRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderListItem(BaseModel):
    id: int
    po_number: str
    vendor_name: str
    status: str
    acceptance_status: str
    delivery_status: str
    grand_total: Decimal
    created_at: datetime


class POAcceptanceRequest(BaseModel):
    remarks: str | None = Field(default=None, max_length=500)


class DeliveryUpdateRequest(BaseModel):
    status: str
