from __future__ import annotations

import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.activity.service import append_activity_log
from app.common.enums import ApprovalStatus, QuotationStatus, RFQStatus
from app.common.procurement import budget_impact, risk_assessment
from app.models.entities import (
    RFQ,
    ApprovalRequest,
    ApprovalStep,
    Quotation,
    RFQItem,
    RFQVendorInvite,
    User,
    Vendor,
    VendorCategory,
)
from app.rfqs.schemas import RFQCreate, RFQUpdate
from app.vendors.validators import is_valid_hsn_sac


def _ensure_future_deadline(deadline: datetime) -> None:
    normalized = deadline if deadline.tzinfo else deadline.replace(tzinfo=UTC)
    if normalized <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="RFQ deadline must be future"
        )


def _ensure_category(db: Session, category_id: int) -> VendorCategory:
    category = db.get(VendorCategory, category_id)
    if category is None or not category.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RFQ category")
    return category


def _ensure_vendors(db: Session, vendor_ids: list[int]) -> list[Vendor]:
    vendors = db.scalars(select(Vendor).where(Vendor.id.in_(vendor_ids))).all()
    found = {vendor.id for vendor in vendors}
    missing = [vendor_id for vendor_id in vendor_ids if vendor_id not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid vendor ids: {missing}"
        )
    if not vendors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Select at least one vendor"
        )
    return vendors


def _replace_items_and_invites(
    db: Session,
    rfq: RFQ,
    *,
    items,
    vendors: list[Vendor],
    discovery_source: str = "manual",
) -> None:
    db.execute(delete(RFQItem).where(RFQItem.rfq_id == rfq.id))
    db.execute(delete(RFQVendorInvite).where(RFQVendorInvite.rfq_id == rfq.id))
    db.flush()

    for item in items:
        if not is_valid_hsn_sac(item.hsn_sac):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid HSN/SAC"
            )
        db.add(
            RFQItem(
                rfq_id=rfq.id,
                item_name=item.item_name,
                hsn_sac=item.hsn_sac,
                quantity=item.quantity,
                unit=item.unit,
                target_price=item.target_price,
            )
        )
    for vendor in vendors:
        db.add(
            RFQVendorInvite(
                rfq_id=rfq.id,
                vendor_id=vendor.id,
                invite_token=secrets.token_urlsafe(24),
                discovery_source=discovery_source,
                vendor_lifecycle_stage_at_invite=vendor.lifecycle_stage,
                status="invited",
            )
        )
    db.flush()


def create_rfq(db: Session, payload: RFQCreate, actor: User) -> RFQ:
    _ensure_future_deadline(payload.deadline)
    _ensure_category(db, payload.category_id)
    vendors = _ensure_vendors(db, payload.vendor_ids)
    rfq = RFQ(
        title=payload.title,
        category_id=payload.category_id,
        description=payload.description,
        deadline=payload.deadline,
        status=RFQStatus.draft.value,
        created_by_id=actor.id,
    )
    db.add(rfq)
    db.flush()
    _replace_items_and_invites(db, rfq, items=payload.items, vendors=vendors)
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="rfq.created",
        entity_type="rfq",
        entity_id=rfq.id,
        summary=f"RFQ {rfq.title} created",
        payload={
            "vendor_count": len(vendors),
            "item_count": len(payload.items),
            "status": rfq.status,
        },
    )
    return rfq


def update_rfq(db: Session, rfq: RFQ, payload: RFQUpdate, actor: User) -> RFQ:
    if rfq.status != RFQStatus.draft.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only draft RFQs can be edited"
        )
    data = payload.model_dump(exclude_unset=True)
    if "deadline" in data and data["deadline"] is not None:
        _ensure_future_deadline(data["deadline"])
    if "category_id" in data and data["category_id"] is not None:
        _ensure_category(db, data["category_id"])

    for field in ("title", "category_id", "description", "deadline"):
        if field in data and data[field] is not None:
            setattr(rfq, field, data[field])

    if payload.items is not None or payload.vendor_ids is not None:
        items = payload.items or db.scalars(select(RFQItem).where(RFQItem.rfq_id == rfq.id)).all()
        vendor_ids = payload.vendor_ids or [
            invite.vendor_id
            for invite in db.scalars(
                select(RFQVendorInvite).where(RFQVendorInvite.rfq_id == rfq.id)
            ).all()
        ]
        vendors = _ensure_vendors(db, vendor_ids)
        _replace_items_and_invites(db, rfq, items=items, vendors=vendors)

    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="rfq.updated",
        entity_type="rfq",
        entity_id=rfq.id,
        summary=f"RFQ {rfq.title} updated",
        payload={"changed_fields": sorted(data.keys())},
    )
    return rfq


def send_rfq(db: Session, rfq: RFQ, actor: User) -> RFQ:
    if rfq.status != RFQStatus.draft.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only draft RFQs can be sent"
        )
    item_count = db.scalar(
        select(func.count()).select_from(RFQItem).where(RFQItem.rfq_id == rfq.id)
    )
    invite_count = db.scalar(
        select(func.count()).select_from(RFQVendorInvite).where(RFQVendorInvite.rfq_id == rfq.id)
    )
    if not item_count or not invite_count:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="RFQ needs items and vendors"
        )
    rfq.status = RFQStatus.sent.value
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="rfq.sent",
        entity_type="rfq",
        entity_id=rfq.id,
        summary=f"RFQ {rfq.title} sent",
        payload={"invite_count": invite_count},
    )
    return rfq


def select_quotation_for_approval(
    db: Session, rfq: RFQ, quotation_id: int, actor: User
) -> ApprovalRequest:
    quotation = db.get(Quotation, quotation_id)
    if quotation is None or quotation.rfq_id != rfq.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found for RFQ"
        )
    if quotation.status not in {QuotationStatus.submitted.value, QuotationStatus.selected.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Quotation must be submitted"
        )

    quote_count = db.scalar(
        select(func.count())
        .select_from(Quotation)
        .where(Quotation.rfq_id == rfq.id, Quotation.status.in_(["submitted", "selected"]))
    )
    for quote in db.scalars(select(Quotation).where(Quotation.rfq_id == rfq.id)).all():
        quote.status = (
            QuotationStatus.selected.value
            if quote.id == quotation.id
            else QuotationStatus.rejected.value
        )

    vendor = db.get(Vendor, quotation.vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    quote_count = quote_count or 1
    tier, breakdown, reasons = risk_assessment(
        db=db,
        selected_quote=quotation,
        vendor=vendor,
        quote_count=quote_count,
    )
    impact = budget_impact(db, quotation.grand_total)
    if impact["health"] in {"yellow", "red"}:
        reasons.append(f"Budget impact is {impact['health']}")

    approval = ApprovalRequest(
        rfq_id=rfq.id,
        quotation_id=quotation.id,
        requested_by_id=actor.id,
        status=ApprovalStatus.pending.value,
        risk_tier=tier,
        risk_breakdown=breakdown,
        budget_impact=impact,
        policy_reasons=reasons,
    )
    db.add(approval)
    db.flush()

    approvers = db.scalars(
        select(User).where(User.role.in_(["manager", "finance_manager"]), User.is_active.is_(True))
    ).all()
    for index, approver in enumerate(approvers[:2], start=1):
        db.add(
            ApprovalStep(
                approval_request_id=approval.id,
                approver_id=approver.id,
                sequence=index,
                status=ApprovalStatus.pending.value,
            )
        )
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="quotation.selected",
        entity_type="quotation",
        entity_id=quotation.id,
        summary=f"Quotation #{quotation.id} selected for approval",
        payload={"rfq_id": rfq.id, "approval_request_id": approval.id, "risk_tier": tier},
    )
    return approval
