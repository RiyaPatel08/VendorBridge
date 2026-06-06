from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_roles
from app.common.enums import UserRole
from app.db.session import get_db
from app.invoices.schemas import (
    EmailInvoiceRequest,
    EmailOutboxRead,
    InvoiceItemRead,
    InvoiceListItem,
    InvoiceRead,
)
from app.invoices.service import (
    generate_invoice,
    log_invoice_action,
    mark_payable,
    queue_invoice_email,
)
from app.models.entities import EmailOutbox, Invoice, InvoiceItem, PurchaseOrder, User, Vendor

router = APIRouter(tags=["invoices"])


def _invoice_read(db: Session, invoice: Invoice) -> InvoiceRead:
    po = db.get(PurchaseOrder, invoice.purchase_order_id)
    vendor = db.get(Vendor, invoice.vendor_id)
    items = db.scalars(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id).order_by(InvoiceItem.id)
    ).all()
    return InvoiceRead.model_validate(invoice).model_copy(
        update={
            "po_number": po.po_number if po else "",
            "vendor_name": vendor.name if vendor else "",
            "vendor_gstin": vendor.gstin if vendor else "",
            "items": [InvoiceItemRead.model_validate(item) for item in items],
        }
    )


@router.get("/invoices", response_model=list[InvoiceListItem])
def list_invoices(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> list[InvoiceListItem]:
    query = select(Invoice).order_by(Invoice.created_at.desc())
    if actor.role == UserRole.vendor.value:
        vendor = db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))
        if vendor is None:
            return []
        query = query.where(Invoice.vendor_id == vendor.id)
    invoices = db.scalars(query).all()
    rows = []
    for invoice in invoices:
        po = db.get(PurchaseOrder, invoice.purchase_order_id)
        vendor = db.get(Vendor, invoice.vendor_id)
        rows.append(
            InvoiceListItem(
                id=invoice.id,
                invoice_number=invoice.invoice_number,
                po_number=po.po_number if po else "",
                vendor_name=vendor.name if vendor else "",
                status=invoice.status,
                match_status=invoice.match_status,
                grand_total=invoice.grand_total,
                due_date=invoice.due_date,
            )
        )
    return rows


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> InvoiceRead:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if actor.role == UserRole.vendor.value:
        vendor = db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))
        if vendor is None or vendor.id != invoice.vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access this invoice"
            )
    return _invoice_read(db, invoice)


@router.post("/purchase-orders/{po_id}/invoice", response_model=InvoiceRead)
def post_generate_invoice(
    po_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_roles(UserRole.procurement_officer, UserRole.manager)
    ),
) -> InvoiceRead:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    invoice = generate_invoice(db, po, actor)
    db.commit()
    db.refresh(invoice)
    return _invoice_read(db, invoice)


@router.post("/invoices/{invoice_id}/payable", response_model=InvoiceRead)
def post_mark_payable(
    invoice_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(
        require_roles(
            UserRole.manager,
            UserRole.finance_manager,
        )
    ),
) -> InvoiceRead:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    invoice = mark_payable(db, invoice, actor)
    db.commit()
    db.refresh(invoice)
    return _invoice_read(db, invoice)


@router.post("/invoices/{invoice_id}/print", response_model=dict)
def post_print_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> dict:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if actor.role == UserRole.vendor.value:
        vendor = db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))
        if vendor is None or vendor.id != invoice.vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access this invoice"
            )
    log_invoice_action(db, invoice, actor, "printed")
    db.commit()
    return {"ok": True}


@router.get("/invoices/{invoice_id}/download")
def download_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> Response:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if actor.role == UserRole.vendor.value:
        vendor = db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))
        if vendor is None or vendor.id != invoice.vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access this invoice"
            )
    log_invoice_action(db, invoice, actor, "downloaded")
    db.commit()
    html = f"""
    <html><body>
      <h1>{invoice.invoice_number}</h1>
      <p>Grand total: INR {invoice.grand_total}</p>
      <p>CGST: {invoice.cgst_total} SGST: {invoice.sgst_total} IGST: {invoice.igst_total}</p>
    </body></html>
    """
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={invoice.invoice_number}.html"},
    )


@router.post("/invoices/{invoice_id}/email", response_model=EmailOutboxRead)
def post_email_invoice(
    invoice_id: int,
    payload: EmailInvoiceRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> EmailOutboxRead:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if actor.role == UserRole.vendor.value:
        vendor = db.scalar(select(Vendor).where(Vendor.contact_email == actor.email))
        if vendor is None or vendor.id != invoice.vendor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access this invoice"
            )
    outbox = queue_invoice_email(db, invoice, actor, str(payload.to_email), payload.message)
    db.commit()
    db.refresh(outbox)
    return EmailOutboxRead.model_validate(outbox)


@router.get("/email-outbox", response_model=list[EmailOutboxRead])
def list_email_outbox(
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(UserRole.admin, UserRole.procurement_officer, UserRole.manager)
    ),
) -> list[EmailOutbox]:
    return db.scalars(select(EmailOutbox).order_by(EmailOutbox.created_at.desc())).all()
