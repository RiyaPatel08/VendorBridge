from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvoiceItemRead(BaseModel):
    id: int
    item_name: str
    hsn_sac: str
    quantity: Decimal
    unit_price: Decimal
    gst_percent: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceRead(BaseModel):
    id: int
    invoice_number: str
    purchase_order_id: int
    po_number: str = ""
    vendor_id: int
    vendor_name: str = ""
    vendor_gstin: str = ""
    invoice_date: date
    due_date: date
    status: str
    subtotal: Decimal
    cgst_total: Decimal
    sgst_total: Decimal
    igst_total: Decimal
    grand_total: Decimal
    match_status: str
    items: list[InvoiceItemRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListItem(BaseModel):
    id: int
    invoice_number: str
    po_number: str
    vendor_name: str
    status: str
    match_status: str
    grand_total: Decimal
    due_date: date


class EmailInvoiceRequest(BaseModel):
    to_email: EmailStr
    message: str | None = Field(default=None, max_length=1000)


class EmailOutboxRead(BaseModel):
    id: int
    to_email: str
    subject: str
    status: str
    invoice_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
