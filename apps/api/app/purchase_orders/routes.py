from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_roles
from app.common.enums import UserRole
from app.db.session import get_db
from app.models.entities import ApprovalRequest, PurchaseOrder, PurchaseOrderItem, User, Vendor
from app.purchase_orders.schemas import (
    DeliveryUpdateRequest,
    POAcceptanceRequest,
    PurchaseOrderItemRead,
    PurchaseOrderListItem,
    PurchaseOrderRead,
)
from app.purchase_orders.service import (
    confirm_receipt,
    generate_purchase_order,
    set_acceptance,
    update_delivery,
)

router = APIRouter(tags=["purchase_orders"])


def _vendor_for_actor(db: Session, actor: User) -> Vendor | None:
    if actor.role != UserRole.vendor.value:
        return None
    return db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))


def _ensure_po_access(db: Session, po: PurchaseOrder, actor: User, *, manage: bool = False) -> None:
    if actor.role == UserRole.vendor.value:
        vendor = _vendor_for_actor(db, actor)
        if vendor is None or vendor.id != po.vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vendor cannot access this purchase order",
            )
        return
    if manage and actor.role not in {
        UserRole.admin.value,
        UserRole.procurement_officer.value,
        UserRole.manager.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this purchase order",
        )


def _po_read(db: Session, po: PurchaseOrder) -> PurchaseOrderRead:
    vendor = db.get(Vendor, po.vendor_id)
    items = db.scalars(
        select(PurchaseOrderItem)
        .where(PurchaseOrderItem.purchase_order_id == po.id)
        .order_by(PurchaseOrderItem.id)
    ).all()
    return PurchaseOrderRead.model_validate(po).model_copy(
        update={
            "vendor_name": vendor.name if vendor else "Vendor",
            "items": [PurchaseOrderItemRead.model_validate(item) for item in items],
        }
    )


@router.get("/purchase-orders", response_model=list[PurchaseOrderListItem])
def list_purchase_orders(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> list[PurchaseOrderListItem]:
    query = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
    if actor.role == UserRole.vendor.value:
        vendor = _vendor_for_actor(db, actor)
        if vendor is None:
            return []
        query = query.where(PurchaseOrder.vendor_id == vendor.id)
    orders = db.scalars(query).all()
    rows = []
    for po in orders:
        vendor = db.get(Vendor, po.vendor_id)
        rows.append(
            PurchaseOrderListItem(
                id=po.id,
                po_number=po.po_number,
                vendor_name=vendor.name if vendor else "Vendor",
                status=po.status,
                acceptance_status=po.acceptance_status,
                delivery_status=po.delivery_status,
                grand_total=po.grand_total,
                created_at=po.created_at,
            )
        )
    return rows


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderRead)
def get_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    _ensure_po_access(db, po, actor)
    return _po_read(db, po)


@router.post("/approvals/{approval_id}/purchase-order", response_model=PurchaseOrderRead)
def post_generate_purchase_order(
    approval_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_roles(UserRole.procurement_officer, UserRole.manager)
    ),
) -> PurchaseOrderRead:
    approval = db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    po = generate_purchase_order(db, approval, actor)
    db.commit()
    db.refresh(po)
    return _po_read(db, po)


@router.post("/purchase-orders/{po_id}/accept", response_model=PurchaseOrderRead)
def post_accept_po(
    po_id: int,
    payload: POAcceptanceRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    _ensure_po_access(db, po, actor, manage=True)
    po = set_acceptance(db, po, actor, "accepted", payload.remarks)
    db.commit()
    db.refresh(po)
    return _po_read(db, po)


@router.post("/purchase-orders/{po_id}/reject", response_model=PurchaseOrderRead)
def post_reject_po(
    po_id: int,
    payload: POAcceptanceRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    _ensure_po_access(db, po, actor, manage=True)
    po = set_acceptance(db, po, actor, "rejected", payload.remarks)
    db.commit()
    db.refresh(po)
    return _po_read(db, po)


@router.post("/purchase-orders/{po_id}/request-modification", response_model=PurchaseOrderRead)
def post_request_modification(
    po_id: int,
    payload: POAcceptanceRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    _ensure_po_access(db, po, actor, manage=True)
    po = set_acceptance(db, po, actor, "modification_requested", payload.remarks)
    db.commit()
    db.refresh(po)
    return _po_read(db, po)


@router.post("/purchase-orders/{po_id}/delivery", response_model=PurchaseOrderRead)
def post_delivery_update(
    po_id: int,
    payload: DeliveryUpdateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    _ensure_po_access(db, po, actor, manage=True)
    po = update_delivery(db, po, actor, payload.status)
    db.commit()
    db.refresh(po)
    return _po_read(db, po)


@router.post("/purchase-orders/{po_id}/receive", response_model=PurchaseOrderRead)
def post_confirm_receipt(
    po_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_roles(UserRole.procurement_officer, UserRole.manager)
    ),
) -> PurchaseOrderRead:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    po = confirm_receipt(db, po, actor)
    db.commit()
    db.refresh(po)
    return _po_read(db, po)
