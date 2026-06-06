from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.activity.service import append_activity_log
from app.common.procurement import money, tax_split
from app.models.entities import (
    EmailOutbox,
    Invoice,
    InvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    User,
    Vendor,
)


def next_invoice_number(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(Invoice)) or 0
    return f"INV-2026-{count + 1:04d}"


def match_purchase_order(
    db: Session, po: PurchaseOrder, invoice: Invoice | None = None
) -> tuple[str, dict]:
    po_items = db.scalars(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po.id)
    ).all()
    quantity_ok = all(item.accepted_quantity == item.quantity for item in po_items)
    amount_ok = True if invoice is None else money(invoice.grand_total) == money(po.grand_total)
    status_value = "matched" if quantity_ok and amount_ok else "mismatch"
    return status_value, {
        "quantity_ok": quantity_ok,
        "amount_ok": amount_ok,
        "po_total": float(money(po.grand_total)),
        "invoice_total": float(money(invoice.grand_total)) if invoice else None,
    }


def generate_invoice(db: Session, po: PurchaseOrder, actor: User) -> Invoice:
    if po.status not in {"issued", "received"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="PO is not ready for invoicing"
        )
    existing = db.scalar(select(Invoice).where(Invoice.purchase_order_id == po.id))
    if existing:
        return existing
    vendor = db.get(Vendor, po.vendor_id)
    split = tax_split(po.subtotal, po.gst_total, vendor.state if vendor else "")
    invoice = Invoice(
        invoice_number=next_invoice_number(db),
        purchase_order_id=po.id,
        vendor_id=po.vendor_id,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        status="draft",
        subtotal=po.subtotal,
        cgst_total=split["cgst_total"],
        sgst_total=split["sgst_total"],
        igst_total=split["igst_total"],
        grand_total=po.grand_total,
        match_status="pending",
    )
    db.add(invoice)
    db.flush()
    for po_item in db.scalars(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po.id)
    ).all():
        line_total = money(po_item.quantity * po_item.unit_price * Decimal("1.18"))
        db.add(
            InvoiceItem(
                invoice_id=invoice.id,
                item_name=po_item.item_name,
                hsn_sac=po_item.hsn_sac,
                quantity=po_item.quantity,
                unit_price=po_item.unit_price,
                gst_percent=Decimal("18.00"),
                line_total=line_total,
            )
        )
    match_status, match_payload = match_purchase_order(db, po, invoice)
    invoice.match_status = match_status
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="invoice.generated",
        entity_type="invoice",
        entity_id=invoice.id,
        summary=f"Invoice {invoice.invoice_number} generated",
        payload={"po_id": po.id, "match": match_payload, "grand_total": float(invoice.grand_total)},
    )
    return invoice


def mark_payable(db: Session, invoice: Invoice, actor: User) -> Invoice:
    if invoice.match_status != "matched":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="3-way match must pass first"
        )
    invoice.status = "payable"
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="invoice.payable",
        entity_type="invoice",
        entity_id=invoice.id,
        summary=f"Invoice {invoice.invoice_number} marked payable",
        payload={"status": invoice.status},
    )
    return invoice


def log_invoice_action(db: Session, invoice: Invoice, actor: User, action: str) -> None:
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type=f"invoice.{action}",
        entity_type="invoice",
        entity_id=invoice.id,
        summary=f"Invoice {invoice.invoice_number} {action}",
        payload={"invoice_number": invoice.invoice_number},
    )


def queue_invoice_email(
    db: Session, invoice: Invoice, actor: User, to_email: str, message: str | None
) -> EmailOutbox:
    outbox = EmailOutbox(
        to_email=to_email,
        subject=f"VendorBridge invoice {invoice.invoice_number}",
        body_html=message
        or f"<p>Invoice {invoice.invoice_number} for INR {invoice.grand_total} is ready.</p>",
        status="queued",
        invoice_id=invoice.id,
    )
    db.add(outbox)
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="invoice.emailed",
        entity_type="invoice",
        entity_id=invoice.id,
        summary=f"Invoice {invoice.invoice_number} queued for email",
        payload={"to_email": to_email, "outbox_id": outbox.id},
    )
    return outbox
