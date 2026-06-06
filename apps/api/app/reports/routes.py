from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.models.entities import RFQ, ActivityLog, Invoice, PurchaseOrder, User, Vendor

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    vendor_count = db.scalar(select(func.count()).select_from(Vendor)) or 0
    active_vendors = (
        db.scalar(select(func.count()).select_from(Vendor).where(Vendor.status == "active")) or 0
    )
    rfq_count = db.scalar(select(func.count()).select_from(RFQ)) or 0
    po_count = db.scalar(select(func.count()).select_from(PurchaseOrder)) or 0
    invoice_count = db.scalar(select(func.count()).select_from(Invoice)) or 0
    ledger_count = db.scalar(select(func.count()).select_from(ActivityLog)) or 0
    return {
        "vendors": vendor_count,
        "active_vendors": active_vendors,
        "rfqs": rfq_count,
        "purchase_orders": po_count,
        "invoices": invoice_count,
        "ledger_entries": ledger_count,
    }
