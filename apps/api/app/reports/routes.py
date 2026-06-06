from collections import defaultdict

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.models.entities import (
    RFQ,
    ActivityLog,
    ApprovalRequest,
    Invoice,
    PurchaseOrder,
    Quotation,
    User,
    Vendor,
    VendorCategory,
)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats")
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
    pending_approvals = (
        db.scalar(
            select(func.count())
            .select_from(ApprovalRequest)
            .where(ApprovalRequest.status == "pending")
        )
        or 0
    )
    active_rfqs = db.scalar(select(func.count()).select_from(RFQ).where(RFQ.status == "sent")) or 0
    recent_pos = []
    for po in db.scalars(
        select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(5)
    ).all():
        vendor = db.get(Vendor, po.vendor_id)
        recent_pos.append(
            {
                "id": po.id,
                "po_number": po.po_number,
                "vendor_name": vendor.name if vendor else "",
                "status": po.status,
                "delivery_status": po.delivery_status,
                "grand_total": float(po.grand_total),
            }
        )
    recent_invoices = []
    for invoice in db.scalars(select(Invoice).order_by(Invoice.created_at.desc()).limit(5)).all():
        vendor = db.get(Vendor, invoice.vendor_id)
        recent_invoices.append(
            {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "vendor_name": vendor.name if vendor else "",
                "status": invoice.status,
                "match_status": invoice.match_status,
                "grand_total": float(invoice.grand_total),
            }
        )
    return {
        "vendors": vendor_count,
        "active_vendors": active_vendors,
        "rfqs": rfq_count,
        "active_rfqs": active_rfqs,
        "pending_approvals": pending_approvals,
        "purchase_orders": po_count,
        "invoices": invoice_count,
        "ledger_entries": ledger_count,
        "recent_purchase_orders": recent_pos,
        "recent_invoices": recent_invoices,
    }


@router.get("/reports/summary")
def reports_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    total_spend = db.scalar(select(func.coalesce(func.sum(Invoice.grand_total), 0))) or 0
    pending_approvals = (
        db.scalar(
            select(func.count())
            .select_from(ApprovalRequest)
            .where(ApprovalRequest.status == "pending")
        )
        or 0
    )
    invoices = db.scalars(select(Invoice).order_by(Invoice.created_at.asc())).all()
    monthly_totals: dict[str, float] = defaultdict(float)
    for invoice in invoices:
        month = invoice.created_at.strftime("%b")
        monthly_totals[month] += float(invoice.grand_total)
    monthly_spend = [{"month": month, "spend": spend} for month, spend in monthly_totals.items()]

    category_spend: dict[int, float] = defaultdict(float)
    for invoice in invoices:
        vendor = db.get(Vendor, invoice.vendor_id)
        if vendor:
            category_spend[vendor.category_id] += float(invoice.grand_total)

    category_rows = []
    for category in db.scalars(select(VendorCategory).order_by(VendorCategory.name)).all():
        vendor_count = (
            db.scalar(
                select(func.count()).select_from(Vendor).where(Vendor.category_id == category.id)
            )
            or 0
        )
        category_rows.append(
            {
                "category": category.name,
                "vendors": vendor_count,
                "spend": category_spend.get(category.id, 0),
            }
        )

    vendor_rows = []
    for vendor in db.scalars(select(Vendor).order_by(Vendor.rating.desc()).limit(8)).all():
        vendor_rows.append(
            {
                "id": vendor.id,
                "name": vendor.name,
                "rating": float(vendor.rating),
                "lifecycle_stage": vendor.lifecycle_stage,
                "reliability_score": float(vendor.reliability_score),
                "delivery_score": float(vendor.delivery_score),
                "completed_orders_count": vendor.completed_orders_count,
            }
        )
    quote_count = db.scalar(select(func.count()).select_from(Quotation)) or 0
    return {
        "kpis": {
            "total_spend": float(total_spend),
            "pending_approvals": pending_approvals,
            "rfqs": db.scalar(select(func.count()).select_from(RFQ)) or 0,
            "quotations": quote_count,
        },
        "monthly_spend": monthly_spend,
        "categories": category_rows,
        "vendors": vendor_rows,
    }


@router.get("/reports/export.csv")
def export_reports_csv(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    rows = ["vendor,status,lifecycle_stage,rating,completed_orders"]
    for vendor in db.scalars(select(Vendor).order_by(Vendor.name)).all():
        rows.append(
            f"{vendor.name},{vendor.status},{vendor.lifecycle_stage},{vendor.rating},"
            f"{vendor.completed_orders_count}"
        )
    return Response(
        "\n".join(rows),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vendorbridge-report.csv"},
    )
