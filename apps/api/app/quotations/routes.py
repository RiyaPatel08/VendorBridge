from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_roles
from app.common.enums import UserRole
from app.db.session import get_db
from app.models.entities import RFQ, Quotation, QuotationItem, RFQItem, User, Vendor
from app.quotations.schemas import (
    ComparisonResponse,
    ComparisonRow,
    QuotationDraft,
    QuotationItemRead,
    QuotationListItem,
    QuotationRead,
)
from app.quotations.service import (
    coverage_label,
    recompute_scores,
    submit_quotation,
    upsert_quotation,
)

router = APIRouter(tags=["quotations"])


def _quotation_read(db: Session, quotation: Quotation) -> QuotationRead:
    vendor = db.get(Vendor, quotation.vendor_id)
    rfq_items = {
        item.id: item.item_name
        for item in db.scalars(select(RFQItem).where(RFQItem.rfq_id == quotation.rfq_id)).all()
    }
    items = []
    for item in db.scalars(
        select(QuotationItem)
        .where(QuotationItem.quotation_id == quotation.id)
        .order_by(QuotationItem.id)
    ).all():
        read = QuotationItemRead.model_validate(item).model_copy(
            update={"item_name": rfq_items.get(item.rfq_item_id)}
        )
        items.append(read)
    return QuotationRead.model_validate(quotation).model_copy(
        update={"vendor_name": vendor.name if vendor else None, "items": items}
    )


@router.get("/quotations", response_model=list[QuotationListItem])
def list_quotations(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> list[QuotationListItem]:
    query = select(Quotation).order_by(Quotation.created_at.desc())
    if actor.role == UserRole.vendor.value:
        vendor = db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))
        if vendor is None:
            return []
        query = query.where(Quotation.vendor_id == vendor.id)
    elif actor.role not in {
        UserRole.procurement_officer.value,
        UserRole.manager.value,
        UserRole.finance_manager.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    quotations = db.scalars(query).all()
    rows = []
    for quotation in quotations:
        rfq = db.get(RFQ, quotation.rfq_id)
        vendor = db.get(Vendor, quotation.vendor_id)
        rows.append(
            QuotationListItem(
                id=quotation.id,
                rfq_id=quotation.rfq_id,
                rfq_title=rfq.title if rfq else "RFQ",
                vendor_id=quotation.vendor_id,
                vendor_name=vendor.name if vendor else "Vendor",
                status=quotation.status,
                grand_total=quotation.grand_total,
                delivery_days=quotation.delivery_days,
                best_value_score=quotation.best_value_score,
                submitted_at=quotation.submitted_at,
            )
        )
    return rows


@router.post(
    "/quotations/drafts", response_model=QuotationRead, status_code=status.HTTP_201_CREATED
)
def save_quotation_draft(
    payload: QuotationDraft,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.vendor)),
) -> QuotationRead:
    quotation = upsert_quotation(db, payload, actor)
    db.commit()
    db.refresh(quotation)
    return _quotation_read(db, quotation)


@router.post("/quotations/{quotation_id}/submit", response_model=QuotationRead)
def post_submit_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.vendor)),
) -> QuotationRead:
    quotation = db.get(Quotation, quotation_id)
    if quotation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found")
    quotation = submit_quotation(db, quotation, actor)
    db.commit()
    db.refresh(quotation)
    return _quotation_read(db, quotation)


@router.get("/quotations/{quotation_id}", response_model=QuotationRead)
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> QuotationRead:
    quotation = db.get(Quotation, quotation_id)
    if quotation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found")
    if actor.role == UserRole.vendor.value:
        vendor = db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))
        if vendor is None or quotation.vendor_id != vendor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access this quotation"
            )
    elif actor.role not in {
        UserRole.procurement_officer.value,
        UserRole.manager.value,
        UserRole.finance_manager.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return _quotation_read(db, quotation)


@router.get("/rfqs/{rfq_id}/comparison", response_model=ComparisonResponse)
def compare_rfq_quotations(
    rfq_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(UserRole.procurement_officer, UserRole.manager, UserRole.finance_manager)
    ),
) -> ComparisonResponse:
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    recompute_scores(db, rfq_id)
    quotations = db.scalars(
        select(Quotation)
        .where(Quotation.rfq_id == rfq_id, Quotation.status.in_(["submitted", "selected"]))
        .order_by(Quotation.grand_total.asc())
    ).all()
    db.commit()
    lowest = min((quote.grand_total for quote in quotations), default=None)
    rows = []
    for quotation in quotations:
        vendor = db.get(Vendor, quotation.vendor_id)
        rows.append(
            ComparisonRow(
                quotation_id=quotation.id,
                vendor_id=quotation.vendor_id,
                vendor_name=vendor.name if vendor else "Vendor",
                vendor_rating=vendor.rating if vendor else 0,
                lifecycle_stage=vendor.lifecycle_stage if vendor else "potential",
                status=quotation.status,
                subtotal=quotation.subtotal,
                gst_total=quotation.gst_total,
                grand_total=quotation.grand_total,
                delivery_days=quotation.delivery_days,
                payment_terms_days=quotation.payment_terms_days,
                best_value_score=quotation.best_value_score,
                score_breakdown=quotation.score_breakdown or {},
                is_lowest_price=lowest is not None and quotation.grand_total == lowest,
                coverage_label=coverage_label(db, quotation),
            )
        )
    return ComparisonResponse(rfq_id=rfq.id, rfq_title=rfq.title, rows=rows)
