from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.activity.service import append_activity_log
from app.common.enums import QuotationStatus, RFQStatus, UserRole
from app.common.procurement import (
    best_value_breakdown,
    calculate_line_totals,
    money,
    now_utc,
    score,
)
from app.models.entities import (
    RFQ,
    Quotation,
    QuotationItem,
    RFQItem,
    RFQVendorInvite,
    User,
    Vendor,
)
from app.quotations.schemas import QuotationDraft


def _deadline_guard(rfq: RFQ) -> None:
    deadline = rfq.deadline if rfq.deadline.tzinfo else rfq.deadline.replace(tzinfo=UTC)
    if deadline < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="RFQ deadline has passed")


def _ensure_vendor_invited(db: Session, rfq_id: int, vendor_id: int) -> None:
    invite = db.scalar(
        select(RFQVendorInvite).where(
            RFQVendorInvite.rfq_id == rfq_id,
            RFQVendorInvite.vendor_id == vendor_id,
        )
    )
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Vendor is not invited to this RFQ"
        )


def vendor_for_user(db: Session, user: User) -> Vendor | None:
    if user.role != UserRole.vendor.value:
        return None
    vendor = db.scalar(select(Vendor).where(Vendor.contact_email == user.email))
    if vendor:
        return vendor
    return db.scalar(select(Vendor).where(Vendor.status == "active").order_by(Vendor.id.asc()))


def upsert_quotation(db: Session, payload: QuotationDraft, actor: User) -> Quotation:
    rfq = db.get(RFQ, payload.rfq_id)
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    if rfq.status != RFQStatus.sent.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="RFQ must be sent before quoting"
        )
    _deadline_guard(rfq)

    if actor.role == UserRole.vendor.value:
        vendor = vendor_for_user(db, actor)
        if vendor is None or vendor.id != payload.vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot quote for this vendor"
            )
    _ensure_vendor_invited(db, payload.rfq_id, payload.vendor_id)

    quotation = db.scalar(
        select(Quotation).where(
            Quotation.rfq_id == payload.rfq_id,
            Quotation.vendor_id == payload.vendor_id,
        )
    )
    if quotation and quotation.status == QuotationStatus.submitted.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Submitted quotation cannot be edited"
        )
    if quotation is None:
        quotation = Quotation(
            rfq_id=payload.rfq_id,
            vendor_id=payload.vendor_id,
            status=QuotationStatus.draft.value,
            delivery_days=payload.delivery_days,
            payment_terms_days=payload.payment_terms_days,
            notes=payload.notes,
        )
        db.add(quotation)
        db.flush()
    else:
        quotation.delivery_days = payload.delivery_days
        quotation.payment_terms_days = payload.payment_terms_days
        quotation.notes = payload.notes

    rfq_items = {
        item.id: item for item in db.scalars(select(RFQItem).where(RFQItem.rfq_id == rfq.id)).all()
    }
    db.execute(delete(QuotationItem).where(QuotationItem.quotation_id == quotation.id))
    subtotal = Decimal("0.00")
    gst_total = Decimal("0.00")
    for item in payload.items:
        if item.rfq_item_id not in rfq_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RFQ item")
        line_subtotal, line_gst, line_total = calculate_line_totals(
            item.quantity, item.unit_price, item.gst_percent
        )
        subtotal += line_subtotal
        gst_total += line_gst
        db.add(
            QuotationItem(
                quotation_id=quotation.id,
                rfq_item_id=item.rfq_item_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                gst_percent=item.gst_percent,
                available_quantity=item.available_quantity,
                additional_quantity=item.additional_quantity,
                additional_available_days=item.additional_available_days,
                line_subtotal=line_subtotal,
                line_gst=line_gst,
                line_total=line_total,
            )
        )
    quotation.subtotal = money(subtotal)
    quotation.gst_total = money(gst_total)
    quotation.grand_total = money(subtotal + gst_total)
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="quotation.draft_saved",
        entity_type="quotation",
        entity_id=quotation.id,
        summary=f"Quotation #{quotation.id} draft saved",
        payload={
            "rfq_id": rfq.id,
            "vendor_id": payload.vendor_id,
            "grand_total": float(quotation.grand_total),
        },
    )
    return quotation


def recompute_scores(db: Session, rfq_id: int) -> None:
    quotations = db.scalars(
        select(Quotation).where(
            Quotation.rfq_id == rfq_id,
            Quotation.status.in_([QuotationStatus.submitted.value, QuotationStatus.selected.value]),
        )
    ).all()
    if not quotations:
        return
    min_total = min(quote.grand_total for quote in quotations)
    max_delivery = max(quote.delivery_days for quote in quotations)
    max_payment_terms = max(quote.payment_terms_days for quote in quotations)
    vendors = {vendor.id: vendor for vendor in db.scalars(select(Vendor)).all()}
    for quote in quotations:
        vendor = vendors[quote.vendor_id]
        breakdown = best_value_breakdown(
            quotation=quote,
            vendor=vendor,
            min_total=min_total,
            max_delivery=max_delivery,
            max_payment_terms=max_payment_terms,
        )
        quote.score_breakdown = breakdown
        quote.best_value_score = score(breakdown["final_score"])
    db.flush()


def submit_quotation(db: Session, quotation: Quotation, actor: User) -> Quotation:
    rfq = db.get(RFQ, quotation.rfq_id)
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    _deadline_guard(rfq)
    if actor.role == UserRole.vendor.value:
        vendor = vendor_for_user(db, actor)
        if vendor is None or vendor.id != quotation.vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot submit this quotation"
            )
    quotation.status = QuotationStatus.submitted.value
    quotation.submitted_at = now_utc()
    db.flush()
    recompute_scores(db, quotation.rfq_id)
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="quotation.submitted",
        entity_type="quotation",
        entity_id=quotation.id,
        summary=f"Quotation #{quotation.id} submitted",
        payload={"rfq_id": quotation.rfq_id, "grand_total": float(quotation.grand_total)},
    )
    return quotation


def coverage_label(db: Session, quotation: Quotation) -> str:
    items = db.scalars(
        select(QuotationItem).where(QuotationItem.quotation_id == quotation.id)
    ).all()
    if not items:
        return "No coverage"
    now_qty = sum((item.available_quantity for item in items), Decimal("0"))
    total_qty = sum((item.quantity for item in items), Decimal("0"))
    later_qty = sum((item.additional_quantity for item in items), Decimal("0"))
    if now_qty >= total_qty:
        return "Full coverage now"
    if now_qty + later_qty >= total_qty:
        return f"{now_qty} now, {later_qty} later"
    return f"Partial coverage: {now_qty} of {total_qty} now"
