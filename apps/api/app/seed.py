"""Rich demo seed data for VendorBridge UI walkthroughs."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select

from app.activity.service import append_activity_log, seal_activity_block
from app.approvals.service import approve_request, reject_request
from app.common.enums import LifecycleStage, UserRole, VendorStatus
from app.core.security import hash_password
from app.db.optimizations import refresh_vendor_kpis
from app.db.session import SessionLocal
from app.invoices.service import generate_invoice, mark_payable, queue_invoice_email
from app.models.entities import (
    RFQ,
    ActivityLog,
    ActivityLogBlock,
    ApprovalRequest,
    ApprovalStep,
    Budget,
    EmailOutbox,
    Invoice,
    InvoiceItem,
    Notification,
    PurchaseOrder,
    PurchaseOrderItem,
    Quotation,
    QuotationItem,
    RFQItem,
    RFQVendorInvite,
    User,
    Vendor,
    VendorCategory,
    VendorRating,
)
from app.notifications import notify
from app.purchase_orders.service import (
    confirm_receipt,
    generate_purchase_order,
    set_acceptance,
    update_delivery,
)
from app.quotations.schemas import QuotationDraft
from app.quotations.service import submit_quotation, upsert_quotation
from app.rfqs.contracts import QuotationItemDraftContract, RFQItemCreate
from app.rfqs.schemas import RFQCreate
from app.rfqs.service import create_rfq, select_quotation_for_approval, send_rfq
from app.vendors.service import seed_category

DEMO_PASSWORD = "VendorBridge@123"


def upsert_user(
    db,
    *,
    email: str,
    first_name: str,
    last_name: str,
    role: UserRole,
    phone: str = "+91 90000 00000",
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role.value,
        hashed_password=hash_password(DEMO_PASSWORD),
        is_active=True,
    )
    db.add(user)
    db.flush()
    append_activity_log(
        db,
        actor_id=user.id,
        event_type="seed.user",
        entity_type="user",
        entity_id=user.id,
        summary=f"Seeded {role.value} user {email}",
        payload={"role": role.value},
    )
    return user


def upsert_vendor(db, *, actor: User, category_id: int, **values) -> Vendor:
    vendor = db.scalar(select(Vendor).where(Vendor.gstin == values["gstin"]))
    if vendor:
        for key, value in values.items():
            setattr(vendor, key, value)
        vendor.category_id = category_id
        db.flush()
        return vendor
    vendor = Vendor(category_id=category_id, created_by_id=actor.id, **values)
    db.add(vendor)
    db.flush()
    append_activity_log(
        db,
        actor_id=actor.id,
        event_type="seed.vendor",
        entity_type="vendor",
        entity_id=vendor.id,
        summary=f"Seeded vendor {vendor.name}",
        payload={"status": vendor.status, "lifecycle_stage": vendor.lifecycle_stage},
    )
    return vendor


def vendor_actor(db, vendor: Vendor) -> User | None:
    return db.scalar(select(User).where(User.email == vendor.contact_email))


def rfq_item_ids(db, rfq_id: int) -> list[int]:
    return [
        item.id
        for item in db.scalars(
            select(RFQItem).where(RFQItem.rfq_id == rfq_id).order_by(RFQItem.id)
        ).all()
    ]


def seed_quotation(
    db,
    *,
    rfq_id: int,
    vendor: Vendor,
    delivery_days: int,
    payment_terms_days: int,
    notes: str,
    line_specs: list[dict],
) -> Quotation | None:
    actor = vendor_actor(db, vendor)
    if actor is None:
        return None
    items = [
        QuotationItemDraftContract(
            rfq_item_id=spec["rfq_item_id"],
            quantity=spec["quantity"],
            unit_price=spec["unit_price"],
            gst_percent=spec.get("gst_percent", Decimal("18.00")),
            available_quantity=spec.get("available_quantity", spec["quantity"]),
            additional_quantity=spec.get("additional_quantity", Decimal("0.00")),
            additional_available_days=spec.get("additional_available_days"),
        )
        for spec in line_specs
    ]
    quotation = upsert_quotation(
        db,
        QuotationDraft(
            rfq_id=rfq_id,
            vendor_id=vendor.id,
            delivery_days=delivery_days,
            payment_terms_days=payment_terms_days,
            notes=notes,
            items=items,
        ),
        actor,
    )
    return submit_quotation(db, quotation, actor)


def rfq_exists(db, title: str) -> bool:
    return db.scalar(select(RFQ).where(RFQ.title == title)) is not None


def seed_completed_furniture_rfq(
    db,
    *,
    officer: User,
    manager: User,
    finance: User,
    infra_user: User,
    furniture,
    infra: Vendor,
    techcore: Vendor,
    officeneed: Vendor,
) -> None:
    title = "Office Furniture Procurement Q2"
    if rfq_exists(db, title):
        return
    rfq = create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=furniture.id,
            description="Ergonomic chairs and standing desks for the Q2 office expansion.",
            deadline=datetime.now(UTC) + timedelta(days=14),
            vendor_ids=[infra.id, techcore.id, officeneed.id],
            items=[
                RFQItemCreate(
                    item_name="Ergonomic chair",
                    hsn_sac="9403",
                    quantity=Decimal("25"),
                    unit="NOS",
                    target_price=Decimal("5000.00"),
                ),
                RFQItemCreate(
                    item_name="Standing desk",
                    hsn_sac="9403",
                    quantity=Decimal("10"),
                    unit="NOS",
                    target_price=Decimal("9000.00"),
                ),
            ],
        ),
        officer,
    )
    send_rfq(db, rfq, officer)
    item_ids = rfq_item_ids(db, rfq.id)
    for vendor, delivery_days, terms, chair_price, desk_price, notes, partial in [
        (infra, 10, 30, Decimal("4200.00"), Decimal("5200.00"), "Full quantity from Surat warehouse.", False),
        (techcore, 7, 15, Decimal("4700.00"), Decimal("6300.00"), "Fast delivery, shorter payment terms.", False),
        (officeneed, 14, 30, Decimal("4550.00"), Decimal("5650.00"), "15 chairs now, remaining batch in one week.", True),
    ]:
        seed_quotation(
            db,
            rfq_id=rfq.id,
            vendor=vendor,
            delivery_days=delivery_days,
            payment_terms_days=terms,
            notes=notes,
            line_specs=[
                {
                    "rfq_item_id": item_ids[0],
                    "quantity": Decimal("25"),
                    "unit_price": chair_price,
                    "available_quantity": Decimal("15") if partial else Decimal("25"),
                    "additional_quantity": Decimal("10") if partial else Decimal("0"),
                    "additional_available_days": 7 if partial else None,
                },
                {
                    "rfq_item_id": item_ids[1],
                    "quantity": Decimal("10"),
                    "unit_price": desk_price,
                    "available_quantity": Decimal("10"),
                },
            ],
        )
    quotations = db.scalars(select(Quotation).where(Quotation.rfq_id == rfq.id)).all()
    approval = select_quotation_for_approval(db, rfq, quotations[0].id, officer)
    approve_request(db, approval, manager, "Approved based on best value and budget fit.")
    approve_request(db, approval, finance, "Finance reviewed and approved.")
    po = generate_purchase_order(db, approval, officer)
    set_acceptance(db, po, infra_user, "accepted", "Vendor accepted PO terms.")
    update_delivery(db, po, infra_user, "shipped")
    update_delivery(db, po, infra_user, "in_transit")
    confirm_receipt(db, po, officer)
    invoice = generate_invoice(db, po, officer)
    mark_payable(db, invoice, finance)
    queue_invoice_email(
        db,
        invoice,
        officer,
        "accounts@infrasupplies.test",
        "Invoice queued from VendorBridge demo outbox.",
    )


def seed_laptop_rfq_pending_approval(
    db,
    *,
    officer: User,
    it,
    techcore: Vendor,
    globalit: Vendor,
    officeneed: Vendor,
) -> None:
    title = "Laptop Fleet Refresh 2026"
    if rfq_exists(db, title):
        return
    rfq = create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=it.id,
            description="Dell Latitude laptops for engineering and finance teams.",
            deadline=datetime.now(UTC) + timedelta(days=10),
            vendor_ids=[techcore.id, globalit.id, officeneed.id],
            items=[
                RFQItemCreate(
                    item_name="Dell Latitude 5540",
                    hsn_sac="8471",
                    quantity=Decimal("20"),
                    unit="NOS",
                    target_price=Decimal("72000.00"),
                ),
                RFQItemCreate(
                    item_name="USB-C docking station",
                    hsn_sac="8473",
                    quantity=Decimal("20"),
                    unit="NOS",
                    target_price=Decimal("8500.00"),
                ),
            ],
        ),
        officer,
    )
    send_rfq(db, rfq, officer)
    item_ids = rfq_item_ids(db, rfq.id)
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=techcore,
        delivery_days=12,
        payment_terms_days=30,
        notes="Standard warranty 3 years on-site.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("20"), "unit_price": Decimal("71500.00")},
            {"rfq_item_id": item_ids[1], "quantity": Decimal("20"), "unit_price": Decimal("8200.00")},
        ],
    )
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=globalit,
        delivery_days=8,
        payment_terms_days=45,
        notes="Preferred vendor pricing with extended warranty.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("20"), "unit_price": Decimal("69800.00")},
            {"rfq_item_id": item_ids[1], "quantity": Decimal("20"), "unit_price": Decimal("7900.00")},
        ],
    )
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=officeneed,
        delivery_days=15,
        payment_terms_days=30,
        notes="Can supply 12 laptops immediately, balance in 10 days.",
        line_specs=[
            {
                "rfq_item_id": item_ids[0],
                "quantity": Decimal("20"),
                "unit_price": Decimal("70500.00"),
                "available_quantity": Decimal("12"),
                "additional_quantity": Decimal("8"),
                "additional_available_days": 10,
            },
            {"rfq_item_id": item_ids[1], "quantity": Decimal("20"), "unit_price": Decimal("8100.00")},
        ],
    )
    quotations = db.scalars(
        select(Quotation).where(Quotation.rfq_id == rfq.id).order_by(Quotation.grand_total.asc())
    ).all()
    select_quotation_for_approval(db, rfq, quotations[0].id, officer)


def seed_office_supplies_partial_quotes(
    db,
    *,
    officer: User,
    office,
    infra: Vendor,
    officeneed: Vendor,
    greendesk: Vendor,
) -> None:
    title = "Annual Office Supplies Bundle"
    if rfq_exists(db, title):
        return
    rfq = create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=office.id,
            description="Paper, toner, stationery, and pantry consumables for FY26.",
            deadline=datetime.now(UTC) + timedelta(days=21),
            vendor_ids=[infra.id, officeneed.id, greendesk.id],
            items=[
                RFQItemCreate(
                    item_name="A4 copier paper (500 sheets)",
                    hsn_sac="4802",
                    quantity=Decimal("200"),
                    unit="NOS",
                    target_price=Decimal("280.00"),
                ),
                RFQItemCreate(
                    item_name="Laser printer toner cartridge",
                    hsn_sac="8443",
                    quantity=Decimal("40"),
                    unit="NOS",
                    target_price=Decimal("4200.00"),
                ),
            ],
        ),
        officer,
    )
    send_rfq(db, rfq, officer)
    item_ids = rfq_item_ids(db, rfq.id)
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=infra,
        delivery_days=5,
        payment_terms_days=30,
        notes="Bulk warehouse stock available.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("200"), "unit_price": Decimal("265.00")},
            {"rfq_item_id": item_ids[1], "quantity": Decimal("40"), "unit_price": Decimal("4050.00")},
        ],
    )
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=officeneed,
        delivery_days=7,
        payment_terms_days=30,
        notes="Competitive pricing for emerging vendor growth.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("200"), "unit_price": Decimal("272.00")},
            {"rfq_item_id": item_ids[1], "quantity": Decimal("40"), "unit_price": Decimal("4100.00")},
        ],
    )


def seed_network_rfq_draft(db, *, officer: User, it, globalit: Vendor, techcore: Vendor) -> None:
    title = "Network Infrastructure Upgrade"
    if rfq_exists(db, title):
        return
    create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=it.id,
            description="Core switches and Wi-Fi access points for HQ expansion — draft pending review.",
            deadline=datetime.now(UTC) + timedelta(days=30),
            vendor_ids=[globalit.id, techcore.id],
            items=[
                RFQItemCreate(
                    item_name="48-port managed switch",
                    hsn_sac="8517",
                    quantity=Decimal("6"),
                    unit="NOS",
                    target_price=Decimal("85000.00"),
                ),
                RFQItemCreate(
                    item_name="Enterprise Wi-Fi 6 AP",
                    hsn_sac="8517",
                    quantity=Decimal("24"),
                    unit="NOS",
                    target_price=Decimal("18500.00"),
                ),
            ],
        ),
        officer,
    )


def seed_rejected_approval_rfq(
    db,
    *,
    officer: User,
    manager: User,
    office,
    officeneed: Vendor,
    greendesk: Vendor,
) -> None:
    title = "Cloud Storage Subscription Renewal"
    if rfq_exists(db, title):
        return
    rfq = create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=office.id,
            description="Annual SaaS renewal for document management platform.",
            deadline=datetime.now(UTC) + timedelta(days=7),
            vendor_ids=[officeneed.id, greendesk.id],
            items=[
                RFQItemCreate(
                    item_name="Enterprise SaaS license (100 users)",
                    hsn_sac="9983",
                    quantity=Decimal("1"),
                    unit="NOS",
                    target_price=Decimal("450000.00"),
                ),
            ],
        ),
        officer,
    )
    send_rfq(db, rfq, officer)
    item_ids = rfq_item_ids(db, rfq.id)
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=officeneed,
        delivery_days=3,
        payment_terms_days=15,
        notes="Includes onboarding support.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("1"), "unit_price": Decimal("468000.00")},
        ],
    )
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=greendesk,
        delivery_days=5,
        payment_terms_days=30,
        notes="Lower annual fee with quarterly billing.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("1"), "unit_price": Decimal("442000.00")},
        ],
    )
    quote = db.scalar(
        select(Quotation).where(Quotation.rfq_id == rfq.id, Quotation.vendor_id == officeneed.id)
    )
    if quote:
        approval = select_quotation_for_approval(db, rfq, quote.id, officer)
        reject_request(db, approval, manager, "Price exceeds budget threshold for SaaS renewals.")


def seed_av_setup_pending_finance(
    db,
    *,
    officer: User,
    manager: User,
    it,
    techcore: Vendor,
    globalit: Vendor,
) -> None:
    title = "Conference Room AV Setup"
    if rfq_exists(db, title):
        return
    rfq = create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=it.id,
            description="Projectors, displays, and conferencing kits for 3 meeting rooms.",
            deadline=datetime.now(UTC) + timedelta(days=12),
            vendor_ids=[techcore.id, globalit.id],
            items=[
                RFQItemCreate(
                    item_name="75-inch interactive display",
                    hsn_sac="8528",
                    quantity=Decimal("3"),
                    unit="NOS",
                    target_price=Decimal("125000.00"),
                ),
                RFQItemCreate(
                    item_name="Video conferencing bar",
                    hsn_sac="8517",
                    quantity=Decimal("3"),
                    unit="NOS",
                    target_price=Decimal("68000.00"),
                ),
            ],
        ),
        officer,
    )
    send_rfq(db, rfq, officer)
    item_ids = rfq_item_ids(db, rfq.id)
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=techcore,
        delivery_days=10,
        payment_terms_days=30,
        notes="Includes installation and calibration.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("3"), "unit_price": Decimal("122000.00")},
            {"rfq_item_id": item_ids[1], "quantity": Decimal("3"), "unit_price": Decimal("65500.00")},
        ],
    )
    seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=globalit,
        delivery_days=9,
        payment_terms_days=45,
        notes="Premium AV bundle with 2-year warranty.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("3"), "unit_price": Decimal("119500.00")},
            {"rfq_item_id": item_ids[1], "quantity": Decimal("3"), "unit_price": Decimal("64000.00")},
        ],
    )
    quote = db.scalar(
        select(Quotation).where(Quotation.rfq_id == rfq.id, Quotation.vendor_id == globalit.id)
    )
    if quote:
        approval = select_quotation_for_approval(db, rfq, quote.id, officer)
        approve_request(db, approval, manager, "AV vendor selected for best value and delivery.")
        # Finance step still pending — no PO until finance approves.


def seed_shelving_po_in_transit(
    db,
    *,
    officer: User,
    manager: User,
    finance: User,
    furniture,
    infra: Vendor,
    infra_user: User,
) -> None:
    title = "Warehouse Shelving Units"
    if rfq_exists(db, title):
        return
    rfq = create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=furniture.id,
            description="Heavy-duty steel shelving for the Surat warehouse.",
            deadline=datetime.now(UTC) + timedelta(days=18),
            vendor_ids=[infra.id],
            items=[
                RFQItemCreate(
                    item_name="Steel storage rack (4-tier)",
                    hsn_sac="9403",
                    quantity=Decimal("30"),
                    unit="NOS",
                    target_price=Decimal("12000.00"),
                ),
            ],
        ),
        officer,
    )
    send_rfq(db, rfq, officer)
    item_ids = rfq_item_ids(db, rfq.id)
    quote = seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=infra,
        delivery_days=14,
        payment_terms_days=30,
        notes="Custom powder-coat finish included.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("30"), "unit_price": Decimal("11500.00")},
        ],
    )
    if quote is None:
        return
    approval = select_quotation_for_approval(db, rfq, quote.id, officer)
    approve_request(db, approval, manager, "Shelving approved for warehouse expansion.")
    approve_request(db, approval, finance, "Finance cleared capital expenditure.")
    po = generate_purchase_order(db, approval, officer)
    set_acceptance(db, po, infra_user, "accepted", "Production slot confirmed.")
    update_delivery(db, po, infra_user, "shipped")
    update_delivery(db, po, infra_user, "in_transit")


def seed_printing_po_draft_invoice(
    db,
    *,
    officer: User,
    manager: User,
    finance: User,
    office,
    officeneed: Vendor,
    officeneed_user: User,
) -> None:
    title = "Marketing Print Run Q1"
    if rfq_exists(db, title):
        return
    rfq = create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=office.id,
            description="Brochures, banners, and event collateral for product launch.",
            deadline=datetime.now(UTC) + timedelta(days=9),
            vendor_ids=[officeneed.id],
            items=[
                RFQItemCreate(
                    item_name="Tri-fold brochure (A4)",
                    hsn_sac="4911",
                    quantity=Decimal("5000"),
                    unit="NOS",
                    target_price=Decimal("8.50"),
                ),
                RFQItemCreate(
                    item_name="Roll-up banner",
                    hsn_sac="4911",
                    quantity=Decimal("12"),
                    unit="NOS",
                    target_price=Decimal("1800.00"),
                ),
            ],
        ),
        officer,
    )
    send_rfq(db, rfq, officer)
    item_ids = rfq_item_ids(db, rfq.id)
    quote = seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=officeneed,
        delivery_days=6,
        payment_terms_days=15,
        notes="Express print and delivery before launch event.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("5000"), "unit_price": Decimal("8.20")},
            {"rfq_item_id": item_ids[1], "quantity": Decimal("12"), "unit_price": Decimal("1750.00")},
        ],
    )
    if quote is None:
        return
    approval = select_quotation_for_approval(db, rfq, quote.id, officer)
    approve_request(db, approval, manager, "Approved for marketing launch timeline.")
    approve_request(db, approval, finance, "Within campaign budget.")
    po = generate_purchase_order(db, approval, officer)
    set_acceptance(db, po, officeneed_user, "accepted", "Print job completed.")
    update_delivery(db, po, officeneed_user, "shipped")
    update_delivery(db, po, officeneed_user, "in_transit")
    update_delivery(db, po, officeneed_user, "delivered")
    confirm_receipt(db, po, officer)
    generate_invoice(db, po, officer)


def seed_igst_invoice(
    db,
    *,
    officer: User,
    manager: User,
    finance: User,
    logistics,
    fastlog: Vendor,
    fastlog_user: User,
) -> None:
    """Inter-state PO from Maharashtra vendor — IGST on invoice."""
    title = "Inter-city Freight Support"
    if rfq_exists(db, title):
        return
    rfq = create_rfq(
        db,
        RFQCreate(
            title=title,
            category_id=logistics.id,
            description="Dedicated freight lanes for Mumbai-to-Surat equipment moves.",
            deadline=datetime.now(UTC) + timedelta(days=14),
            vendor_ids=[fastlog.id],
            items=[
                RFQItemCreate(
                    item_name="Dedicated freight trip",
                    hsn_sac="9965",
                    quantity=Decimal("8"),
                    unit="NOS",
                    target_price=Decimal("18000.00"),
                ),
            ],
        ),
        officer,
    )
    send_rfq(db, rfq, officer)
    item_ids = rfq_item_ids(db, rfq.id)
    quote = seed_quotation(
        db,
        rfq_id=rfq.id,
        vendor=fastlog,
        delivery_days=4,
        payment_terms_days=15,
        notes="Unblocked temporarily for inter-state demo shipment.",
        line_specs=[
            {"rfq_item_id": item_ids[0], "quantity": Decimal("8"), "unit_price": Decimal("17200.00")},
        ],
    )
    if quote is None:
        return
    approval = select_quotation_for_approval(db, rfq, quote.id, officer)
    approve_request(db, approval, manager, "Logistics vendor approved for pilot route.")
    approve_request(db, approval, finance, "Freight budget available.")
    po = generate_purchase_order(db, approval, officer)
    set_acceptance(db, po, fastlog_user, "accepted", "Fleet assigned.")
    update_delivery(db, po, fastlog_user, "shipped")
    confirm_receipt(db, po, officer)
    invoice = generate_invoice(db, po, officer)
    mark_payable(db, invoice, finance)


def seed_vendor_ratings(db, *, officer: User, infra: Vendor, techcore: Vendor, globalit: Vendor) -> None:
    if db.scalar(select(func.count()).select_from(VendorRating)) >= 6:
        return
    pos = db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.id.asc()).limit(4)).all()
    samples = [
        (infra, 5, 5, 4, 5, "Consistently reliable furniture deliveries."),
        (techcore, 4, 4, 4, 4, "Good IT hardware support."),
        (globalit, 5, 5, 5, 5, "Preferred vendor — excellent service."),
        (infra, 4, 5, 4, 4, "Minor delay on one line item, resolved quickly."),
    ]
    for index, (vendor, quality, delivery, comm, service, remarks) in enumerate(samples):
        po_id = pos[index].id if index < len(pos) else None
        if po_id and db.scalar(
            select(VendorRating).where(VendorRating.purchase_order_id == po_id)
        ):
            continue
        db.add(
            VendorRating(
                vendor_id=vendor.id,
                purchase_order_id=po_id,
                quality_score=quality,
                delivery_speed_score=delivery,
                communication_score=comm,
                service_score=service,
                remarks=remarks,
                created_by_id=officer.id,
            )
        )
    db.flush()


def seed_notifications(
    db,
    *,
    admin: User,
    officer: User,
    manager: User,
    finance: User,
    infra_user: User,
) -> None:
    if db.scalar(select(func.count()).select_from(Notification)) >= 10:
        return
    pending = (
        db.scalar(
            select(func.count())
            .select_from(Quotation)
            .where(Quotation.status == "submitted")
        )
        or 0
    )
    entries = [
        (officer.id, "New quotation submitted", f"{pending} quotations awaiting comparison review.", "quotation", None),
        (manager.id, "Approval pending", "Laptop Fleet Refresh 2026 is waiting for your decision.", "approval_request", None),
        (finance.id, "Finance review required", "Conference Room AV Setup needs finance sign-off.", "approval_request", None),
        (infra_user.id, "PO in transit", "Warehouse Shelving Units shipment is on the way.", "purchase_order", None),
        (admin.id, "Ledger sealed", "Activity ledger block sealed successfully during demo seed.", "activity_log", None),
        (officer.id, "RFQ deadline approaching", "Annual Office Supplies Bundle closes in 3 weeks.", "rfq", None),
        (manager.id, "Budget alert", "Procurement budget utilization crossed 75% for Q2.", "budget", None),
        (officer.id, "Vendor verified", "GlobalIT Solutions moved to Preferred vendor tier.", "vendor", None),
    ]
    for user_id, title, message, entity_type, entity_id in entries:
        notify(
            db,
            user_id=user_id,
            title=title,
            message=message,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
        )


def spread_demo_timeline(db) -> None:
    """Back-date invoices and POs so charts and recent lists look realistic."""
    month_offsets = [5, 35, 65, 95, 125, 20, 50, 80]
    invoices = db.scalars(select(Invoice).order_by(Invoice.id.asc())).all()
    for index, invoice in enumerate(invoices):
        days_ago = month_offsets[index % len(month_offsets)]
        stamp = datetime.now(UTC) - timedelta(days=days_ago)
        invoice.created_at = stamp
        invoice.invoice_date = (date.today() - timedelta(days=days_ago))
        invoice.due_date = invoice.invoice_date + timedelta(days=30)
    pos = db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.id.asc())).all()
    for index, po in enumerate(pos):
        days_ago = max(1, month_offsets[index % len(month_offsets)] - 7)
        po.created_at = datetime.now(UTC) - timedelta(days=days_ago)
    db.flush()


def sync_budget_spent(db) -> None:
    budget = db.scalar(select(Budget).where(Budget.department == "Procurement"))
    if budget is None:
        return
    total = db.scalar(
        select(func.coalesce(func.sum(Invoice.grand_total), 0)).where(
            Invoice.status.in_(["payable", "draft"])
        )
    ) or Decimal("0")
    budget.spent_amount = total
    db.flush()


def clear_demo_data(db) -> None:
    """Remove all transactional demo rows so ``--fresh`` seed starts clean."""
    for model in (
        EmailOutbox,
        Notification,
        VendorRating,
        InvoiceItem,
        Invoice,
        PurchaseOrderItem,
        PurchaseOrder,
        ApprovalStep,
        ApprovalRequest,
        QuotationItem,
        Quotation,
        RFQVendorInvite,
        RFQItem,
        RFQ,
        ActivityLog,
        ActivityLogBlock,
        Vendor,
        VendorCategory,
        Budget,
        User,
    ):
        db.execute(delete(model))
    db.flush()


def seed() -> None:
    db = SessionLocal()
    try:
        admin = upsert_user(
            db,
            email="admin@vendorbridge.test",
            first_name="Asha",
            last_name="Admin",
            role=UserRole.admin,
        )
        officer = upsert_user(
            db,
            email="officer@vendorbridge.test",
            first_name="Neel",
            last_name="Shah",
            role=UserRole.procurement_officer,
        )
        manager = upsert_user(
            db,
            email="rahul.mehta@vendorbridge.test",
            first_name="Rahul",
            last_name="Mehta",
            role=UserRole.manager,
        )
        finance = upsert_user(
            db,
            email="priya.shah@vendorbridge.test",
            first_name="Priya",
            last_name="Shah",
            role=UserRole.finance_manager,
        )
        infra_user = upsert_user(
            db,
            email="vendor@infrasupplies.test",
            first_name="Meera",
            last_name="Patel",
            role=UserRole.vendor,
            phone="+91 98765 10001",
        )
        techcore_user = upsert_user(
            db,
            email="quotes@techcore.test",
            first_name="Harsh",
            last_name="Mehta",
            role=UserRole.vendor,
            phone="+91 98765 10002",
        )
        officeneed_user = upsert_user(
            db,
            email="hello@officeneed.test",
            first_name="Ravi",
            last_name="Desai",
            role=UserRole.vendor,
            phone="+91 98765 10003",
        )
        fastlog_user = upsert_user(
            db,
            email="ops@fastlog.test",
            first_name="Sana",
            last_name="Khan",
            role=UserRole.vendor,
            phone="+91 98765 10004",
        )
        globalit_user = upsert_user(
            db,
            email="vendor@globalit.test",
            first_name="Kiran",
            last_name="Rao",
            role=UserRole.vendor,
            phone="+91 98765 10005",
        )
        greendesk_user = upsert_user(
            db,
            email="sales@greendesk.test",
            first_name="Anita",
            last_name="Sharma",
            role=UserRole.vendor,
            phone="+91 98765 10006",
        )
        printhub_user = upsert_user(
            db,
            email="pending@printhub.test",
            first_name="Vikram",
            last_name="Singh",
            role=UserRole.vendor,
            phone="+91 98765 10007",
        )

        furniture = seed_category(db, "Furniture", "FURN")
        office = seed_category(db, "Office Supplies", "OFFICE")
        it = seed_category(db, "IT Equipment", "IT")
        logistics = seed_category(db, "Logistics", "LOG")

        infra = upsert_vendor(
            db,
            actor=admin,
            category_id=furniture.id,
            name="Infra Supplies Pvt Ltd",
            legal_name="Infra Supplies Private Limited",
            gstin="24INFRA1234F1Z5",
            pan="INFRA1234F",
            state="Gujarat",
            city="Surat",
            contact_name="Meera Patel",
            contact_email="vendor@infrasupplies.test",
            contact_phone="+91 98765 10001",
            status=VendorStatus.active.value,
            lifecycle_stage=LifecycleStage.trusted.value,
            completed_orders_count=32,
            rating=Decimal("4.50"),
            reliability_score=Decimal("91.00"),
            delivery_score=Decimal("88.00"),
            completion_rate=Decimal("96.00"),
            satisfaction_score=Decimal("90.00"),
            is_gstin_verified=True,
            is_pan_verified=True,
            compliance_notes="GST and PAN verified for demo.",
            custom_attributes={
                "iso_certified": True,
                "msme_registration": "UDYAM-GJ-01-0001234",
                "preferred_payment": "NEFT",
                "delivery_radius_km": 250,
            },
        )
        techcore = upsert_vendor(
            db,
            actor=admin,
            category_id=it.id,
            name="TechCore Ltd",
            legal_name="TechCore Limited",
            gstin="24TECHC2727Q1Z1",
            pan="TECHC2727Q",
            state="Gujarat",
            city="Ahmedabad",
            contact_name="Harsh Mehta",
            contact_email="quotes@techcore.test",
            contact_phone="+91 98765 10002",
            status=VendorStatus.active.value,
            lifecycle_stage=LifecycleStage.verified.value,
            completed_orders_count=11,
            rating=Decimal("3.80"),
            reliability_score=Decimal("78.00"),
            delivery_score=Decimal("84.00"),
            completion_rate=Decimal("86.00"),
            satisfaction_score=Decimal("76.00"),
            is_gstin_verified=True,
            is_pan_verified=True,
            compliance_notes=None,
            custom_attributes={"iso_certified": True, "msme_registration": "UDYAM-GJ-01-0007788"},
        )
        officeneed = upsert_vendor(
            db,
            actor=admin,
            category_id=office.id,
            name="OfficeNeed Co",
            legal_name="OfficeNeed Company",
            gstin="24OFFIC4321N1Z3",
            pan="OFFIC4321N",
            state="Gujarat",
            city="Vadodara",
            contact_name="Ravi Desai",
            contact_email="hello@officeneed.test",
            contact_phone="+91 98765 10003",
            status=VendorStatus.active.value,
            lifecycle_stage=LifecycleStage.emerging.value,
            completed_orders_count=3,
            rating=Decimal("4.20"),
            reliability_score=Decimal("82.00"),
            delivery_score=Decimal("73.00"),
            completion_rate=Decimal("80.00"),
            satisfaction_score=Decimal("85.00"),
            is_gstin_verified=True,
            is_pan_verified=True,
        )
        fastlog = upsert_vendor(
            db,
            actor=admin,
            category_id=logistics.id,
            name="FastLog Transport",
            legal_name="FastLog Transport Services",
            gstin="27FASTL5555P1Z8",
            pan="FASTL5555P",
            state="Maharashtra",
            city="Mumbai",
            contact_name="Sana Khan",
            contact_email="ops@fastlog.test",
            contact_phone="+91 98765 10004",
            status=VendorStatus.active.value,
            lifecycle_stage=LifecycleStage.verified.value,
            completed_orders_count=8,
            rating=Decimal("3.60"),
            reliability_score=Decimal("72.00"),
            delivery_score=Decimal("79.00"),
            completion_rate=Decimal("88.00"),
            satisfaction_score=Decimal("74.00"),
            is_gstin_verified=True,
            is_pan_verified=True,
            compliance_notes="Unblocked for inter-state freight demo.",
        )
        globalit = upsert_vendor(
            db,
            actor=admin,
            category_id=it.id,
            name="GlobalIT Solutions",
            legal_name="GlobalIT Solutions Private Limited",
            gstin="24GLOBA1234G1Z5",
            pan="GLOBA1234G",
            state="Gujarat",
            city="Gandhinagar",
            contact_name="Kiran Rao",
            contact_email="vendor@globalit.test",
            contact_phone="+91 98765 10005",
            status=VendorStatus.active.value,
            lifecycle_stage=LifecycleStage.preferred.value,
            completed_orders_count=105,
            rating=Decimal("4.85"),
            reliability_score=Decimal("96.00"),
            delivery_score=Decimal("94.00"),
            completion_rate=Decimal("98.00"),
            satisfaction_score=Decimal("95.00"),
            is_gstin_verified=True,
            is_pan_verified=True,
            compliance_notes="Preferred vendor — top performer.",
            custom_attributes={"iso_certified": True, "preferred_payment": "RTGS"},
        )
        greendesk = upsert_vendor(
            db,
            actor=admin,
            category_id=office.id,
            name="GreenDesk Supplies",
            legal_name="GreenDesk Supplies LLP",
            gstin="24GREEN1234D1Z7",
            pan="GREEN1234D",
            state="Gujarat",
            city="Rajkot",
            contact_name="Anita Sharma",
            contact_email="sales@greendesk.test",
            contact_phone="+91 98765 10006",
            status=VendorStatus.active.value,
            lifecycle_stage=LifecycleStage.potential.value,
            completed_orders_count=0,
            rating=Decimal("0.00"),
            reliability_score=Decimal("55.00"),
            delivery_score=Decimal("50.00"),
            completion_rate=Decimal("0.00"),
            satisfaction_score=Decimal("0.00"),
            is_gstin_verified=True,
            is_pan_verified=False,
            compliance_notes="New vendor gaining marketplace visibility.",
        )
        upsert_vendor(
            db,
            actor=admin,
            category_id=office.id,
            name="PrintHub India",
            legal_name="PrintHub India Private Limited",
            gstin="24PRINT1234P1Z3",
            pan="PRINT1234P",
            state="Gujarat",
            city="Surat",
            contact_name="Vikram Singh",
            contact_email="pending@printhub.test",
            contact_phone="+91 98765 10007",
            status=VendorStatus.pending.value,
            lifecycle_stage=LifecycleStage.potential.value,
            completed_orders_count=0,
            rating=Decimal("0.00"),
            reliability_score=Decimal("0.00"),
            delivery_score=Decimal("0.00"),
            completion_rate=Decimal("0.00"),
            satisfaction_score=Decimal("0.00"),
            is_gstin_verified=False,
            is_pan_verified=False,
            compliance_notes="Awaiting GST verification.",
        )

        if not db.scalar(select(Budget).where(Budget.department == "Procurement")):
            db.add(
                Budget(
                    department="Procurement",
                    fiscal_year=2026,
                    amount=Decimal("2500000.00"),
                    spent_amount=Decimal("0.00"),
                )
            )
        if not db.scalar(select(Budget).where(Budget.department == "Marketing")):
            db.add(
                Budget(
                    department="Marketing",
                    fiscal_year=2026,
                    amount=Decimal("800000.00"),
                    spent_amount=Decimal("125000.00"),
                )
            )
        db.flush()

        seed_completed_furniture_rfq(
            db,
            officer=officer,
            manager=manager,
            finance=finance,
            infra_user=infra_user,
            furniture=furniture,
            infra=infra,
            techcore=techcore,
            officeneed=officeneed,
        )
        seed_laptop_rfq_pending_approval(
            db,
            officer=officer,
            it=it,
            techcore=techcore,
            globalit=globalit,
            officeneed=officeneed,
        )
        seed_office_supplies_partial_quotes(
            db,
            officer=officer,
            office=office,
            infra=infra,
            officeneed=officeneed,
            greendesk=greendesk,
        )
        seed_network_rfq_draft(db, officer=officer, it=it, globalit=globalit, techcore=techcore)
        seed_rejected_approval_rfq(
            db,
            officer=officer,
            manager=manager,
            office=office,
            officeneed=officeneed,
            greendesk=greendesk,
        )
        seed_av_setup_pending_finance(
            db,
            officer=officer,
            manager=manager,
            it=it,
            techcore=techcore,
            globalit=globalit,
        )
        seed_shelving_po_in_transit(
            db,
            officer=officer,
            manager=manager,
            finance=finance,
            furniture=furniture,
            infra=infra,
            infra_user=infra_user,
        )
        seed_printing_po_draft_invoice(
            db,
            officer=officer,
            manager=manager,
            finance=finance,
            office=office,
            officeneed=officeneed,
            officeneed_user=officeneed_user,
        )
        seed_igst_invoice(
            db,
            officer=officer,
            manager=manager,
            finance=finance,
            logistics=logistics,
            fastlog=fastlog,
            fastlog_user=fastlog_user,
        )

        seed_vendor_ratings(db, officer=officer, infra=infra, techcore=techcore, globalit=globalit)
        seed_notifications(
            db,
            admin=admin,
            officer=officer,
            manager=manager,
            finance=finance,
            infra_user=infra_user,
        )
        spread_demo_timeline(db)
        sync_budget_spent(db)

        seal_activity_block(db)
        db.commit()
        refresh_vendor_kpis(db)
        db.commit()

        rfq_count = db.scalar(select(func.count()).select_from(RFQ)) or 0
        vendor_count = db.scalar(select(func.count()).select_from(Vendor)) or 0
        po_count = db.scalar(select(func.count()).select_from(PurchaseOrder)) or 0
        invoice_count = db.scalar(select(func.count()).select_from(Invoice)) or 0
        quote_count = db.scalar(select(func.count()).select_from(Quotation)) or 0
        pending_approvals = (
            db.scalar(
                select(func.count())
                .select_from(Quotation)
                .join(RFQ, Quotation.rfq_id == RFQ.id)
                .where(Quotation.status == "submitted")
            )
            or 0
        )
        print("Seeded VendorBridge demo data.")
        print(
            f"  {vendor_count} vendors | {rfq_count} RFQs | {quote_count} quotations | "
            f"{po_count} POs | {invoice_count} invoices"
        )
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if "--fresh" in sys.argv:
        reset_db = SessionLocal()
        try:
            clear_demo_data(reset_db)
            reset_db.commit()
            print("Cleared existing demo data.")
        finally:
            reset_db.close()
    seed()
