from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.activity.schemas import ActivityLogRead, LedgerVerificationResult
from app.activity.service import seal_activity_block, verify_activity_integrity
from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.models.entities import ActivityLog, User

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/logs", response_model=list[ActivityLogRead])
def list_activity_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ActivityLog]:
    safe_limit = max(1, min(limit, 200))
    return db.scalars(select(ActivityLog).order_by(ActivityLog.id.desc()).limit(safe_limit)).all()


@router.post("/seal", response_model=dict)
def seal_activity_ledger(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    block = seal_activity_block(db)
    db.commit()
    return {"sealed": block is not None, "block_id": block.id if block else None}


@router.get("/verify", response_model=LedgerVerificationResult)
def verify_activity_ledger(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LedgerVerificationResult:
    ok, entries, blocks, message, first_error_log_id = verify_activity_integrity(db)
    return LedgerVerificationResult(
        ok=ok,
        checked_entries=entries,
        checked_blocks=blocks,
        message=message,
        first_error_log_id=first_error_log_id,
    )
