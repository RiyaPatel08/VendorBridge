from collections import defaultdict

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_roles
from app.common.enums import UserRole
from app.db.optimizations import VENDOR_KPI_VIEW, is_postgres, refresh_vendor_kpis
from app.db.session import get_db
from app.models.entities import (
    RFQ,
    ActivityLog,
    ApprovalRequest,
    Invoice,
    PurchaseOrder,
    Quotation,
    RFQVendorInvite,
    User,
    Vendor,
    VendorCategory,
)

router = APIRouter(tags=["dashboard"])


def _vendor_kpi_rows(db: Session) -> list[dict]:
    """Top vendors by performance.

    On PostgreSQL this reads from the ``vendor_kpi_dashboard`` materialized view
    so the dashboard loads in O(1) regardless of how many orders/invoices exist
    (the heavy aggregation was pre-computed). On SQLite it falls back to a live
    query so tests and quick local dev keep working.
    """

    if is_postgres(db):
        rows = db.execute(
            text(
                f"""
                SELECT vendor_id, vendor_name, rating, lifecycle_stage,
                       total_purchase_orders, total_spend, avg_rating,
                       completed_orders_count
                FROM {VENDOR_KPI_VIEW}
                ORDER BY total_spend DESC, rating DESC
                LIMIT 8
                """
            )
        ).mappings()
        return [
            {
                "id": row["vendor_id"],
                "name": row["vendor_name"],
                "rating": float(row["rating"]),
                "lifecycle_stage": row["lifecycle_stage"],
                "total_purchase_orders": int(row["total_purchase_orders"]),
                "total_spend": float(row["total_spend"]),
                "avg_rating": float(row["avg_rating"]),
                "completed_orders_count": row["completed_orders_count"],
            }
            for row in rows
        ]
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
    return vendor_rows


@router.get("/dashboard/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> dict:
    is_vendor_actor = actor.role == UserRole.vendor.value
    vendor = None
    rfq_id_filter: list[int] | None = None
    if is_vendor_actor:
        vendor = db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))
        if vendor is None:
            rfq_id_filter = []
        else:
            rfq_id_filter = [
                invite.rfq_id
                for invite in db.scalars(
                    select(RFQVendorInvite).where(RFQVendorInvite.vendor_id == vendor.id)
                ).all()
            ]

    if is_vendor_actor:
        vendor_count = 1 if vendor is not None else 0
        active_vendors = 1 if vendor is not None and vendor.status == "active" else 0
    else:
        vendor_count = db.scalar(select(func.count()).select_from(Vendor)) or 0
        active_vendors = (
            db.scalar(select(func.count()).select_from(Vendor).where(Vendor.status == "active"))
            or 0
        )
    rfq_query = select(func.count()).select_from(RFQ)
    active_rfq_query = select(func.count()).select_from(RFQ).where(RFQ.status == "sent")
    po_query = select(func.count()).select_from(PurchaseOrder)
    invoice_query = select(func.count()).select_from(Invoice)
    recent_po_query = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(5)
    recent_invoice_query = select(Invoice).order_by(Invoice.created_at.desc()).limit(5)
    if rfq_id_filter is not None:
        rfq_query = rfq_query.where(RFQ.id.in_(rfq_id_filter))
        active_rfq_query = active_rfq_query.where(RFQ.id.in_(rfq_id_filter))
    if vendor is not None:
        po_query = po_query.where(PurchaseOrder.vendor_id == vendor.id)
        invoice_query = invoice_query.where(Invoice.vendor_id == vendor.id)
        recent_po_query = recent_po_query.where(PurchaseOrder.vendor_id == vendor.id)
        recent_invoice_query = recent_invoice_query.where(Invoice.vendor_id == vendor.id)

    rfq_count = db.scalar(rfq_query) or 0
    po_count = db.scalar(po_query) or 0
    invoice_count = db.scalar(invoice_query) or 0
    ledger_count = db.scalar(select(func.count()).select_from(ActivityLog)) or 0
    pending_approvals = 0 if is_vendor_actor else (
        db.scalar(
            select(func.count())
            .select_from(ApprovalRequest)
            .where(ApprovalRequest.status == "pending")
        )
        or 0
    )
    active_rfqs = db.scalar(active_rfq_query) or 0
    recent_pos = []
    for po in db.scalars(recent_po_query).all():
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
    for invoice in db.scalars(recent_invoice_query).all():
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
    _: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.procurement_officer,
            UserRole.manager,
            UserRole.finance_manager,
        )
    ),
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

    vendor_rows = _vendor_kpi_rows(db)
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


@router.post("/reports/refresh-kpis")
def refresh_kpi_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.procurement_officer)),
) -> dict:
    """Recompute the vendor KPI materialized view.

    Returns ``refreshed: false`` on SQLite, where the dashboard already reads
    live data and no materialized view exists.
    """

    refreshed = refresh_vendor_kpis(db)
    db.commit()
    return {"refreshed": refreshed, "view": VENDOR_KPI_VIEW if refreshed else None}


@router.get("/reports/export.csv")
def export_reports_csv(
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.procurement_officer,
            UserRole.manager,
            UserRole.finance_manager,
        )
    ),
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
