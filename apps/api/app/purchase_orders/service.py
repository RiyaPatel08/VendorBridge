from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.activity.service import append_activity_log
from app.common.enums import ApprovalStatus
from app.models.entities import (
    ApprovalRequest,
    PurchaseOrder,
    PurchaseOrderItem,
    Quotation,
    QuotationItem,
    RFQItem,
    User,
)

DELIVERY_SEQUENCE = ["not_started", "packed", "shipped", "in_transit", "delivered"]


def next_po_number(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(PurchaseOrder)) or 0
    return f"PO-2026-{count + 1:04d}"


def generate_purchase_order(db: Session, approval: ApprovalRequest, actor: User) -> PurchaseOrder:
    if approval.status != ApprovalStatus.approved.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Approval must be approved"
        )
    existing = db.scalar(
        select(PurchaseOrder).where(PurchaseOrder.approval_request_id == approval.id)
    )
    if existing:
        return existing
    quotation = db.get(Quotation, approval.quotation_id)
    if quotation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found")
    po = PurchaseOrder(
        po_number=next_po_number(db),
        approval_request_id=approval.id,
        vendor_id=quotation.vendor_id,
        status="issued",
        acceptance_status="pending",
        delivery_status="not_started",
        subtotal=quotation.subtotal,
        gst_total=quotation.gst_total,
        grand_total=quotation.grand_total,
    )
    db.add(po)
    db.flush()
    rfq_items = {item.id: item for item in db.scalars(select(RFQItem)).all()}
    for quote_item in db.scalars(
        select(QuotationItem).where(QuotationItem.quotation_id == quotation.id)
    ).all():
        rfq_item = rfq_items[quote_item.rfq_item_id]
        db.add(
            PurchaseOrderItem(
                purchase_order_id=po.id,
                item_name=rfq_item.item_name,
                hsn_sac=rfq_item.hsn_sac,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                received_quantity=Decimal("0.00"),
                accepted_quantity=Decimal("0.00"),
            )
        )
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="purchase_order.generated",
        entity_type="purchase_order",
        entity_id=po.id,
        summary=f"Purchase order {po.po_number} generated",
        payload={"approval_request_id": approval.id, "grand_total": float(po.grand_total)},
    )
    return po


def set_acceptance(
    db: Session, po: PurchaseOrder, actor: User, acceptance_status: str, remarks: str | None = None
) -> PurchaseOrder:
    if acceptance_status not in {"accepted", "rejected", "modification_requested"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid acceptance status"
        )
    po.acceptance_status = acceptance_status
    if acceptance_status == "accepted" and po.delivery_status == "not_started":
        po.delivery_status = "packed"
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type=f"purchase_order.{acceptance_status}",
        entity_type="purchase_order",
        entity_id=po.id,
        summary=f"PO {po.po_number} marked {acceptance_status}",
        payload={"remarks": remarks},
    )
    return po


def update_delivery(
    db: Session, po: PurchaseOrder, actor: User, delivery_status: str
) -> PurchaseOrder:
    if delivery_status not in DELIVERY_SEQUENCE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid delivery status"
        )
    current_index = DELIVERY_SEQUENCE.index(po.delivery_status)
    next_index = DELIVERY_SEQUENCE.index(delivery_status)
    if next_index < current_index:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Delivery cannot move backwards"
        )
    po.delivery_status = delivery_status
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="purchase_order.delivery_updated",
        entity_type="purchase_order",
        entity_id=po.id,
        summary=f"PO {po.po_number} delivery moved to {delivery_status}",
        payload={"delivery_status": delivery_status},
    )
    return po


def confirm_receipt(db: Session, po: PurchaseOrder, actor: User) -> PurchaseOrder:
    for item in db.scalars(
        select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po.id)
    ).all():
        item.received_quantity = item.quantity
        item.accepted_quantity = item.quantity
    po.status = "received"
    po.delivery_status = "delivered"
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="purchase_order.received",
        entity_type="purchase_order",
        entity_id=po.id,
        summary=f"PO {po.po_number} receipt confirmed",
        payload={"status": po.status},
    )
    return po
