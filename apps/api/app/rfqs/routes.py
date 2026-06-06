from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_roles
from app.common.enums import UserRole
from app.db.session import get_db
from app.models.entities import (
    RFQ,
    Quotation,
    RFQItem,
    RFQVendorInvite,
    User,
    Vendor,
    VendorCategory,
)
from app.quotations.service import vendor_for_user
from app.rfqs.schemas import (
    RFQCreate,
    RFQInviteRead,
    RFQItemRead,
    RFQListItem,
    RFQRead,
    RFQUpdate,
    SelectQuotationRequest,
)
from app.rfqs.service import create_rfq, select_quotation_for_approval, send_rfq, update_rfq

router = APIRouter(prefix="/rfqs", tags=["rfqs"])


def _rfq_read(db: Session, rfq: RFQ) -> RFQRead:
    category = db.get(VendorCategory, rfq.category_id)
    items = db.scalars(select(RFQItem).where(RFQItem.rfq_id == rfq.id).order_by(RFQItem.id)).all()
    invites = db.scalars(
        select(RFQVendorInvite).where(RFQVendorInvite.rfq_id == rfq.id).order_by(RFQVendorInvite.id)
    ).all()
    invite_reads = []
    for invite in invites:
        vendor = db.get(Vendor, invite.vendor_id)
        invite_reads.append(
            RFQInviteRead(
                id=invite.id,
                vendor_id=invite.vendor_id,
                vendor_name=vendor.name if vendor else "Vendor",
                status=invite.status,
                discovery_source=invite.discovery_source,
                vendor_lifecycle_stage_at_invite=invite.vendor_lifecycle_stage_at_invite,
            )
        )
    return RFQRead(
        id=rfq.id,
        title=rfq.title,
        category_id=rfq.category_id,
        category_name=category.name if category else None,
        description=rfq.description,
        deadline=rfq.deadline,
        status=rfq.status,
        created_by_id=rfq.created_by_id,
        items=[RFQItemRead.model_validate(item) for item in items],
        invites=invite_reads,
        created_at=rfq.created_at,
        updated_at=rfq.updated_at,
    )


def _rfq_list_item(db: Session, rfq: RFQ) -> RFQListItem:
    category = db.get(VendorCategory, rfq.category_id)
    quote_count = db.scalar(
        select(func.count()).select_from(Quotation).where(Quotation.rfq_id == rfq.id)
    )
    invite_count = db.scalar(
        select(func.count()).select_from(RFQVendorInvite).where(RFQVendorInvite.rfq_id == rfq.id)
    )
    return RFQListItem(
        id=rfq.id,
        title=rfq.title,
        category_name=category.name if category else None,
        deadline=rfq.deadline,
        status=rfq.status,
        quote_count=quote_count or 0,
        invite_count=invite_count or 0,
        created_at=rfq.created_at,
    )


@router.get("", response_model=list[RFQListItem])
def list_rfqs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RFQListItem]:
    if current_user.role == UserRole.vendor.value:
        vendor = vendor_for_user(db, current_user)
        if vendor is None:
            return []
        rfq_ids = [
            invite.rfq_id
            for invite in db.scalars(
                select(RFQVendorInvite).where(RFQVendorInvite.vendor_id == vendor.id)
            ).all()
        ]
        rfqs = db.scalars(
            select(RFQ).where(RFQ.id.in_(rfq_ids)).order_by(RFQ.created_at.desc())
        ).all()
    else:
        rfqs = db.scalars(select(RFQ).order_by(RFQ.created_at.desc())).all()
    return [_rfq_list_item(db, rfq) for rfq in rfqs]


@router.get("/vendor", response_model=list[RFQRead])
def list_vendor_rfqs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.vendor)),
) -> list[RFQRead]:
    vendor = vendor_for_user(db, current_user)
    if vendor is None:
        return []
    rfq_ids = [
        invite.rfq_id
        for invite in db.scalars(
            select(RFQVendorInvite).where(RFQVendorInvite.vendor_id == vendor.id)
        ).all()
    ]
    rfqs = db.scalars(select(RFQ).where(RFQ.id.in_(rfq_ids)).order_by(RFQ.created_at.desc())).all()
    return [_rfq_read(db, rfq) for rfq in rfqs]


@router.post("", response_model=RFQRead, status_code=status.HTTP_201_CREATED)
def post_rfq(
    payload: RFQCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
) -> RFQRead:
    rfq = create_rfq(db, payload, actor)
    db.commit()
    db.refresh(rfq)
    return _rfq_read(db, rfq)


@router.get("/{rfq_id}", response_model=RFQRead)
def get_rfq(
    rfq_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RFQRead:
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    return _rfq_read(db, rfq)


@router.patch("/{rfq_id}", response_model=RFQRead)
def patch_rfq(
    rfq_id: int,
    payload: RFQUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
) -> RFQRead:
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    rfq = update_rfq(db, rfq, payload, actor)
    db.commit()
    db.refresh(rfq)
    return _rfq_read(db, rfq)


@router.post("/{rfq_id}/send", response_model=RFQRead)
def post_send_rfq(
    rfq_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
) -> RFQRead:
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    rfq = send_rfq(db, rfq, actor)
    db.commit()
    db.refresh(rfq)
    return _rfq_read(db, rfq)


@router.post("/{rfq_id}/select-quotation")
def post_select_quotation(
    rfq_id: int,
    payload: SelectQuotationRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
) -> dict:
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    approval = select_quotation_for_approval(db, rfq, payload.quotation_id, actor)
    db.commit()
    return {"approval_request_id": approval.id}
