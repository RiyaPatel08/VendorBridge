from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.approvals.schemas import ApprovalDecision, ApprovalListItem, ApprovalRead, ApprovalStepRead
from app.approvals.service import approve_request, reject_request
from app.common.dependencies import require_roles
from app.common.enums import UserRole
from app.db.session import get_db
from app.models.entities import RFQ, ApprovalRequest, ApprovalStep, Quotation, User, Vendor

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _approval_read(db: Session, approval: ApprovalRequest) -> ApprovalRead:
    rfq = db.get(RFQ, approval.rfq_id)
    quotation = db.get(Quotation, approval.quotation_id)
    vendor = db.get(Vendor, quotation.vendor_id) if quotation else None
    steps = []
    for step in db.scalars(
        select(ApprovalStep)
        .where(ApprovalStep.approval_request_id == approval.id)
        .order_by(ApprovalStep.sequence.asc())
    ).all():
        approver = db.get(User, step.approver_id)
        steps.append(
            ApprovalStepRead.model_validate(step).model_copy(
                update={
                    "approver_name": f"{approver.first_name} {approver.last_name}"
                    if approver
                    else "Approver"
                }
            )
        )
    return ApprovalRead.model_validate(approval).model_copy(
        update={
            "rfq_title": rfq.title if rfq else "RFQ",
            "vendor_id": vendor.id if vendor else 0,
            "vendor_name": vendor.name if vendor else "Vendor",
            "quote_total": quotation.grand_total if quotation else 0,
            "steps": steps,
        }
    )


@router.get("", response_model=list[ApprovalListItem])
def list_approvals(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.manager, UserRole.finance_manager)),
) -> list[ApprovalListItem]:
    approvals = db.scalars(
        select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
    ).all()
    rows = []
    for approval in approvals:
        rfq = db.get(RFQ, approval.rfq_id)
        quotation = db.get(Quotation, approval.quotation_id)
        vendor = db.get(Vendor, quotation.vendor_id) if quotation else None
        rows.append(
            ApprovalListItem(
                id=approval.id,
                rfq_title=rfq.title if rfq else "RFQ",
                vendor_name=vendor.name if vendor else "Vendor",
                status=approval.status,
                quote_total=quotation.grand_total if quotation else 0,
                risk_tier=approval.risk_tier,
                created_at=approval.created_at,
            )
        )
    return rows


@router.get("/{approval_id}", response_model=ApprovalRead)
def get_approval(
    approval_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.manager, UserRole.finance_manager)),
) -> ApprovalRead:
    approval = db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    return _approval_read(db, approval)


@router.post("/{approval_id}/approve", response_model=ApprovalRead)
def post_approve(
    approval_id: int,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_roles(UserRole.manager, UserRole.finance_manager)
    ),
) -> ApprovalRead:
    approval = db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    approval = approve_request(db, approval, actor, payload.remarks)
    db.commit()
    db.refresh(approval)
    return _approval_read(db, approval)


@router.post("/{approval_id}/reject", response_model=ApprovalRead)
def post_reject(
    approval_id: int,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_roles(UserRole.manager, UserRole.finance_manager)
    ),
) -> ApprovalRead:
    approval = db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    approval = reject_request(db, approval, actor, payload.remarks)
    db.commit()
    db.refresh(approval)
    return _approval_read(db, approval)
