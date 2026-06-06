from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.activity.service import append_activity_log, seal_activity_block
from app.approvals.service import approve_request
from app.common.enums import LifecycleStage, UserRole, VendorStatus
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.invoices.service import generate_invoice, mark_payable, queue_invoice_email
from app.models.entities import RFQ, Budget, Quotation, RFQItem, User, Vendor
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
        upsert_user(
            db,
            email="vendor@infrasupplies.test",
            first_name="Vendor",
            last_name="Portal",
            role=UserRole.vendor,
        )

        furniture = seed_category(db, "Furniture", "FURN")
        office = seed_category(db, "Office Supplies", "OFFICE")
        it = seed_category(db, "IT Equipment", "IT")
        logistics = seed_category(db, "Logistics", "LOG")

        infra = upsert_vendor(
            db,
            actor=officer,
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
        )
        techcore = upsert_vendor(
            db,
            actor=officer,
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
        )
        officeneed = upsert_vendor(
            db,
            actor=officer,
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
            compliance_notes=None,
        )
        upsert_vendor(
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
            status=VendorStatus.blocked.value,
            lifecycle_stage=LifecycleStage.potential.value,
            completed_orders_count=0,
            rating=Decimal("2.10"),
            reliability_score=Decimal("42.00"),
            delivery_score=Decimal("49.00"),
            completion_rate=Decimal("60.00"),
            satisfaction_score=Decimal("45.00"),
            is_gstin_verified=True,
            is_pan_verified=True,
            compliance_notes="Blocked in demo for delayed deliveries.",
        )

        if not db.scalar(select(Budget).where(Budget.department == "Procurement")):
            db.add(
                Budget(
                    department="Procurement",
                    fiscal_year=2026,
                    amount=Decimal("500000.00"),
                    spent_amount=Decimal("80000.00"),
                )
            )

        if not db.scalar(select(RFQ).where(RFQ.title == "Office Furniture Procurement Q2")):
            rfq = create_rfq(
                db,
                RFQCreate(
                    title="Office Furniture Procurement Q2",
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
            item_ids = [
                item.id
                for item in db.scalars(
                    select(RFQItem).where(RFQItem.rfq_id == rfq.id).order_by(RFQItem.id)
                ).all()
            ]
            quote_payloads = [
                (
                    infra,
                    10,
                    30,
                    Decimal("4200.00"),
                    Decimal("5200.00"),
                    "Can deliver full quantity from Surat warehouse.",
                ),
                (
                    techcore,
                    7,
                    15,
                    Decimal("4700.00"),
                    Decimal("6300.00"),
                    "Fast delivery, shorter payment terms.",
                ),
                (
                    officeneed,
                    14,
                    30,
                    Decimal("4550.00"),
                    Decimal("5650.00"),
                    "15 chairs now, remaining batch in one week.",
                ),
            ]
            quotations: list[Quotation] = []
            for vendor, delivery_days, terms, chair_price, desk_price, notes in quote_payloads:
                quotation = upsert_quotation(
                    db,
                    QuotationDraft(
                        rfq_id=rfq.id,
                        vendor_id=vendor.id,
                        delivery_days=delivery_days,
                        payment_terms_days=terms,
                        notes=notes,
                        items=[
                            QuotationItemDraftContract(
                                rfq_item_id=item_ids[0],
                                quantity=Decimal("25"),
                                unit_price=chair_price,
                                gst_percent=Decimal("18.00"),
                                available_quantity=Decimal("25")
                                if vendor != officeneed
                                else Decimal("15"),
                                additional_quantity=Decimal("0")
                                if vendor != officeneed
                                else Decimal("10"),
                                additional_available_days=None if vendor != officeneed else 7,
                            ),
                            QuotationItemDraftContract(
                                rfq_item_id=item_ids[1],
                                quantity=Decimal("10"),
                                unit_price=desk_price,
                                gst_percent=Decimal("18.00"),
                                available_quantity=Decimal("10"),
                                additional_quantity=Decimal("0"),
                            ),
                        ],
                    ),
                    officer,
                )
                quotations.append(submit_quotation(db, quotation, officer))
            approval = select_quotation_for_approval(db, rfq, quotations[0].id, officer)
            approve_request(db, approval, manager, "Approved based on best value and budget fit.")
            approve_request(db, approval, finance, "Finance reviewed and approved.")
            po = generate_purchase_order(db, approval, officer)
            set_acceptance(db, po, officer, "accepted", "Vendor accepted PO terms.")
            update_delivery(db, po, officer, "shipped")
            update_delivery(db, po, officer, "in_transit")
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

        seal_activity_block(db)
        db.commit()
        print("Seeded VendorBridge demo data.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
