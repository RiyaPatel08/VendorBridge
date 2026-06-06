from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.activity.service import append_activity_log
from app.common.enums import ApprovalStatus
from app.models.entities import ApprovalRequest, ApprovalStep, User


def approve_request(
    db: Session, approval: ApprovalRequest, actor: User, remarks: str
) -> ApprovalRequest:
    if approval.status != ApprovalStatus.pending.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Approval is already decided"
        )
    step = db.scalar(
        select(ApprovalStep)
        .where(
            ApprovalStep.approval_request_id == approval.id,
            ApprovalStep.approver_id == actor.id,
            ApprovalStep.status == ApprovalStatus.pending.value,
        )
        .order_by(ApprovalStep.sequence.asc())
    )
    if step is None:
        step = db.scalar(
            select(ApprovalStep)
            .where(
                ApprovalStep.approval_request_id == approval.id,
                ApprovalStep.status == ApprovalStatus.pending.value,
            )
            .order_by(ApprovalStep.sequence.asc())
        )
    if step is None:
        approval.status = ApprovalStatus.approved.value
    else:
        step.status = ApprovalStatus.approved.value
        step.remarks = remarks
        step.decided_at = datetime.now(UTC)
        db.flush()
        pending_steps = db.scalars(
            select(ApprovalStep).where(
                ApprovalStep.approval_request_id == approval.id,
                ApprovalStep.status == ApprovalStatus.pending.value,
            )
        ).all()
        if not pending_steps:
            approval.status = ApprovalStatus.approved.value
    approval.remarks = remarks
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="approval.approved",
        entity_type="approval_request",
        entity_id=approval.id,
        summary=f"Approval #{approval.id} approved",
        payload={"remarks": remarks, "status": approval.status},
    )
    return approval


def reject_request(
    db: Session, approval: ApprovalRequest, actor: User, remarks: str
) -> ApprovalRequest:
    if approval.status != ApprovalStatus.pending.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Approval is already decided"
        )
    approval.status = ApprovalStatus.rejected.value
    approval.remarks = remarks
    for step in db.scalars(
        select(ApprovalStep).where(ApprovalStep.approval_request_id == approval.id)
    ).all():
        if step.status == ApprovalStatus.pending.value:
            step.status = ApprovalStatus.rejected.value
            step.remarks = remarks
            step.decided_at = datetime.now(UTC)
            break
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="approval.rejected",
        entity_type="approval_request",
        entity_id=approval.id,
        summary=f"Approval #{approval.id} rejected",
        payload={"remarks": remarks},
    )
    return approval
