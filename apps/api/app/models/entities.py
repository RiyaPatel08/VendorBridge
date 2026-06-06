from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import (
    ApprovalStatus,
    LifecycleStage,
    QuotationStatus,
    RFQStatus,
    UserRole,
    VendorStatus,
)
from app.db.optimizations import JSONColumn
from app.db.session import Base

# All semi-structured columns use ``JSONColumn`` so they are stored as native
# binary ``jsonb`` on PostgreSQL (indexable + containment queries) and fall back
# to plain ``JSON`` on SQLite for tests.
JSON = JSONColumn


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(32), default=UserRole.procurement_officer.value)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "role in ('admin','procurement_officer','vendor','manager','finance_manager')",
            name="ck_users_role",
        ),
    )


class VendorCategory(Base, TimestampMixin):
    __tablename__ = "vendor_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    vendors: Mapped[list["Vendor"]] = relationship(back_populates="category")


class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    legal_name: Mapped[str | None] = mapped_column(String(200))
    category_id: Mapped[int] = mapped_column(ForeignKey("vendor_categories.id"))
    gstin: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    pan: Mapped[str | None] = mapped_column(String(10), index=True)
    state: Mapped[str] = mapped_column(String(80), default="Gujarat")
    city: Mapped[str] = mapped_column(String(100))
    contact_name: Mapped[str] = mapped_column(String(120))
    contact_email: Mapped[str] = mapped_column(String(255), index=True)
    contact_phone: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24), default=VendorStatus.pending.value, index=True)
    lifecycle_stage: Mapped[str] = mapped_column(
        String(24), default=LifecycleStage.potential.value, index=True
    )
    completed_orders_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"))
    reliability_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    delivery_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    completion_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    satisfaction_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    is_gstin_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pan_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    compliance_notes: Mapped[str | None] = mapped_column(Text)
    # Tenant-defined custom fields (e.g. MSME number, ISO certification flags).
    # Stored as GIN-indexed JSONB on PostgreSQL so new fields are queryable in
    # milliseconds with no schema migration.
    custom_attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    category: Mapped[VendorCategory] = relationship(back_populates="vendors")
    ratings: Mapped[list["VendorRating"]] = relationship(back_populates="vendor")

    __table_args__ = (
        CheckConstraint("status in ('pending','active','blocked')", name="ck_vendors_status"),
        CheckConstraint(
            "lifecycle_stage in ('potential','emerging','verified','trusted','preferred')",
            name="ck_vendors_lifecycle_stage",
        ),
        CheckConstraint("completed_orders_count >= 0", name="ck_vendors_completed_orders"),
        CheckConstraint("rating >= 0 and rating <= 5", name="ck_vendors_rating"),
        Index("ix_vendors_status_category", "status", "category_id"),
    )


class VendorRating(Base):
    __tablename__ = "vendor_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"))
    quality_score: Mapped[int] = mapped_column(Integer)
    delivery_speed_score: Mapped[int] = mapped_column(Integer)
    communication_score: Mapped[int] = mapped_column(Integer)
    service_score: Mapped[int] = mapped_column(Integer)
    remarks: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vendor: Mapped[Vendor] = relationship(back_populates="ratings")

    __table_args__ = (
        CheckConstraint("quality_score between 1 and 5", name="ck_vendor_ratings_quality"),
        CheckConstraint("delivery_speed_score between 1 and 5", name="ck_vendor_ratings_delivery"),
        CheckConstraint(
            "communication_score between 1 and 5", name="ck_vendor_ratings_communication"
        ),
        CheckConstraint("service_score between 1 and 5", name="ck_vendor_ratings_service"),
    )


class RFQ(Base, TimestampMixin):
    __tablename__ = "rfqs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("vendor_categories.id"))
    description: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), default=RFQStatus.draft.value, index=True)
    custom_attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    items: Mapped[list["RFQItem"]] = relationship(cascade="all, delete-orphan")
    invites: Mapped[list["RFQVendorInvite"]] = relationship(cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status in ('draft','sent','closed','cancelled')", name="ck_rfqs_status"),
    )


class RFQItem(Base):
    __tablename__ = "rfq_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"), index=True)
    item_name: Mapped[str] = mapped_column(String(180))
    hsn_sac: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit: Mapped[str] = mapped_column(String(24), default="NOS")
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    __table_args__ = (CheckConstraint("quantity > 0", name="ck_rfq_items_quantity_positive"),)


class RFQVendorInvite(Base, TimestampMixin):
    __tablename__ = "rfq_vendor_invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    invite_token: Mapped[str] = mapped_column(String(96), unique=True)
    discovery_source: Mapped[str] = mapped_column(String(40), default="manual")
    vendor_lifecycle_stage_at_invite: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), default="invited")

    __table_args__ = (
        UniqueConstraint("rfq_id", "vendor_id", name="uq_rfq_vendor_invites_rfq_vendor"),
    )


class Quotation(Base, TimestampMixin):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    status: Mapped[str] = mapped_column(String(24), default=QuotationStatus.draft.value, index=True)
    delivery_days: Mapped[int] = mapped_column(Integer)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30)
    notes: Mapped[str | None] = mapped_column(Text)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    gst_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    best_value_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    score_breakdown: Mapped[dict | None] = mapped_column(JSON)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("rfq_id", "vendor_id", name="uq_quotations_rfq_vendor"),
        CheckConstraint(
            "status in ('draft','submitted','selected','rejected')", name="ck_quotations_status"
        ),
        CheckConstraint("delivery_days >= 0", name="ck_quotations_delivery_days"),
    )


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id"), index=True)
    rfq_item_id: Mapped[int] = mapped_column(ForeignKey("rfq_items.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gst_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("18.00"))
    available_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    additional_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    additional_available_days: Mapped[int | None] = mapped_column(Integer)
    line_subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    line_gst: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_quotation_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_quotation_items_unit_price"),
        CheckConstraint("gst_percent >= 0", name="ck_quotation_items_gst_percent"),
    )


class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    department: Mapped[str] = mapped_column(String(120), unique=True)
    fiscal_year: Mapped[int] = mapped_column(Integer)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))


class ApprovalRequest(Base, TimestampMixin):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"), index=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id"), index=True)
    requested_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(
        String(24), default=ApprovalStatus.pending.value, index=True
    )
    risk_tier: Mapped[str | None] = mapped_column(String(16))
    risk_breakdown: Mapped[dict | None] = mapped_column(JSON)
    budget_impact: Mapped[dict | None] = mapped_column(JSON)
    policy_reasons: Mapped[list | None] = mapped_column(JSON)
    remarks: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("status in ('pending','approved','rejected')", name="ck_approval_status"),
    )


class ApprovalStep(Base, TimestampMixin):
    __tablename__ = "approval_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    approval_request_id: Mapped[int] = mapped_column(ForeignKey("approval_requests.id"), index=True)
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    sequence: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default=ApprovalStatus.pending.value)
    remarks: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    approval_request_id: Mapped[int | None] = mapped_column(ForeignKey("approval_requests.id"))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    acceptance_status: Mapped[str] = mapped_column(String(32), default="pending")
    delivery_status: Mapped[str] = mapped_column(String(32), default="not_started")
    split_group_id: Mapped[str | None] = mapped_column(String(40), index=True)
    split_label: Mapped[str | None] = mapped_column(String(4))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    gst_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    item_name: Mapped[str] = mapped_column(String(180))
    hsn_sac: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    accepted_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    invoice_date: Mapped[Date] = mapped_column(Date)
    due_date: Mapped[Date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    cgst_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    sgst_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    igst_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    match_status: Mapped[str] = mapped_column(String(32), default="pending")

    __table_args__ = (
        # The database itself refuses to mark an invoice payable/paid unless the
        # 3-way match has passed. Business integrity is enforced at the schema
        # level, not only in Python.
        CheckConstraint(
            "status not in ('payable','paid') or match_status = 'matched'",
            name="ck_invoices_three_way_match",
        ),
    )


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    item_name: Mapped[str] = mapped_column(String(180))
    hsn_sac: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gst_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("18.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)
    summary: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    previous_hash: Mapped[str] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True)
    block_id: Mapped[int | None] = mapped_column(ForeignKey("activity_log_blocks.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_activity_logs_chain", "id", "previous_hash", "entry_hash"),)


class ActivityLogBlock(Base):
    __tablename__ = "activity_log_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_log_id: Mapped[int] = mapped_column(Integer)
    end_log_id: Mapped[int] = mapped_column(Integer)
    merkle_root: Mapped[str] = mapped_column(String(64))
    previous_block_hash: Mapped[str] = mapped_column(String(64))
    block_hash: Mapped[str] = mapped_column(String(64), unique=True)
    sealed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(80))
    related_entity_id: Mapped[int | None] = mapped_column(Integer)


class EmailOutbox(Base, TimestampMixin):
    __tablename__ = "email_outbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    to_email: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    body_html: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
