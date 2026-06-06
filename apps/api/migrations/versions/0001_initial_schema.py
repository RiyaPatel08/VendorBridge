"""Initial VendorBridge schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "role in ('admin','procurement_officer','vendor','manager','finance_manager')",
            name="ck_users_role",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "vendor_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("spent_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("department"),
    )

    op.create_table(
        "activity_log_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_log_id", sa.Integer(), nullable=False),
        sa.Column("end_log_id", sa.Integer(), nullable=False),
        sa.Column("merkle_root", sa.String(length=64), nullable=False),
        sa.Column("previous_block_hash", sa.String(length=64), nullable=False),
        sa.Column("block_hash", sa.String(length=64), nullable=False),
        sa.Column("sealed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("block_hash"),
    )

    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("legal_name", sa.String(length=200), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("gstin", sa.String(length=15), nullable=False),
        sa.Column("pan", sa.String(length=10), nullable=True),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("contact_name", sa.String(length=120), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("lifecycle_stage", sa.String(length=24), nullable=False),
        sa.Column("completed_orders_count", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), nullable=False),
        sa.Column("reliability_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("delivery_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("completion_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("satisfaction_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("is_gstin_verified", sa.Boolean(), nullable=False),
        sa.Column("is_pan_verified", sa.Boolean(), nullable=False),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("completed_orders_count >= 0", name="ck_vendors_completed_orders"),
        sa.CheckConstraint(
            "lifecycle_stage in ('potential','emerging','verified','trusted','preferred')",
            name="ck_vendors_lifecycle_stage",
        ),
        sa.CheckConstraint("rating >= 0 and rating <= 5", name="ck_vendors_rating"),
        sa.CheckConstraint("status in ('pending','active','blocked')", name="ck_vendors_status"),
        sa.ForeignKeyConstraint(["category_id"], ["vendor_categories.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gstin"),
    )
    op.create_index(op.f("ix_vendors_contact_email"), "vendors", ["contact_email"], unique=False)
    op.create_index(op.f("ix_vendors_gstin"), "vendors", ["gstin"], unique=False)
    op.create_index(op.f("ix_vendors_lifecycle_stage"), "vendors", ["lifecycle_stage"], unique=False)
    op.create_index(op.f("ix_vendors_name"), "vendors", ["name"], unique=False)
    op.create_index(op.f("ix_vendors_pan"), "vendors", ["pan"], unique=False)
    op.create_index(op.f("ix_vendors_status"), "vendors", ["status"], unique=False)
    op.create_index("ix_vendors_status_category", "vendors", ["status", "category_id"], unique=False)

    op.create_table(
        "rfqs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status in ('draft','sent','closed','cancelled')", name="ck_rfqs_status"),
        sa.ForeignKeyConstraint(["category_id"], ["vendor_categories.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rfqs_status"), "rfqs", ["status"], unique=False)
    op.create_index(op.f("ix_rfqs_title"), "rfqs", ["title"], unique=False)

    op.create_table(
        "vendor_ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=False),
        sa.Column("delivery_speed_score", sa.Integer(), nullable=False),
        sa.Column("communication_score", sa.Integer(), nullable=False),
        sa.Column("service_score", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("communication_score between 1 and 5", name="ck_vendor_ratings_communication"),
        sa.CheckConstraint("delivery_speed_score between 1 and 5", name="ck_vendor_ratings_delivery"),
        sa.CheckConstraint("quality_score between 1 and 5", name="ck_vendor_ratings_quality"),
        sa.CheckConstraint("service_score between 1 and 5", name="ck_vendor_ratings_service"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendor_ratings_vendor_id"), "vendor_ratings", ["vendor_id"], unique=False)

    op.create_table(
        "rfq_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rfq_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=180), nullable=False),
        sa.Column("hsn_sac", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit", sa.String(length=24), nullable=False),
        sa.Column("target_price", sa.Numeric(12, 2), nullable=True),
        sa.CheckConstraint("quantity > 0", name="ck_rfq_items_quantity_positive"),
        sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rfq_items_rfq_id"), "rfq_items", ["rfq_id"], unique=False)

    op.create_table(
        "rfq_vendor_invites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rfq_id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("invite_token", sa.String(length=96), nullable=False),
        sa.Column("discovery_source", sa.String(length=40), nullable=False),
        sa.Column("vendor_lifecycle_stage_at_invite", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_token"),
        sa.UniqueConstraint("rfq_id", "vendor_id", name="uq_rfq_vendor_invites_rfq_vendor"),
    )
    op.create_index(op.f("ix_rfq_vendor_invites_rfq_id"), "rfq_vendor_invites", ["rfq_id"], unique=False)
    op.create_index(
        op.f("ix_rfq_vendor_invites_vendor_id"), "rfq_vendor_invites", ["vendor_id"], unique=False
    )

    op.create_table(
        "quotations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rfq_id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("delivery_days", sa.Integer(), nullable=False),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("grand_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("best_value_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_breakdown", sa.JSON(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("delivery_days >= 0", name="ck_quotations_delivery_days"),
        sa.CheckConstraint(
            "status in ('draft','submitted','selected','rejected')", name="ck_quotations_status"
        ),
        sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rfq_id", "vendor_id", name="uq_quotations_rfq_vendor"),
    )
    op.create_index(op.f("ix_quotations_rfq_id"), "quotations", ["rfq_id"], unique=False)
    op.create_index(op.f("ix_quotations_status"), "quotations", ["status"], unique=False)
    op.create_index(op.f("ix_quotations_vendor_id"), "quotations", ["vendor_id"], unique=False)

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("rfq_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("gst_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("available_quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("additional_quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("additional_available_days", sa.Integer(), nullable=True),
        sa.Column("line_subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_gst", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.CheckConstraint("gst_percent >= 0", name="ck_quotation_items_gst_percent"),
        sa.CheckConstraint("quantity > 0", name="ck_quotation_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_quotation_items_unit_price"),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"]),
        sa.ForeignKeyConstraint(["rfq_item_id"], ["rfq_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quotation_items_quotation_id"), "quotation_items", ["quotation_id"], unique=False)

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rfq_id", sa.Integer(), nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("risk_tier", sa.String(length=16), nullable=True),
        sa.Column("risk_breakdown", sa.JSON(), nullable=True),
        sa.Column("budget_impact", sa.JSON(), nullable=True),
        sa.Column("policy_reasons", sa.JSON(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status in ('pending','approved','rejected')", name="ck_approval_status"),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"]),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_approval_requests_rfq_id"), "approval_requests", ["rfq_id"], unique=False)
    op.create_index(op.f("ix_approval_requests_status"), "approval_requests", ["status"], unique=False)
    op.create_index(
        op.f("ix_approval_requests_quotation_id"), "approval_requests", ["quotation_id"], unique=False
    )

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("po_number", sa.String(length=40), nullable=False),
        sa.Column("approval_request_id", sa.Integer(), nullable=True),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("acceptance_status", sa.String(length=32), nullable=False),
        sa.Column("delivery_status", sa.String(length=32), nullable=False),
        sa.Column("split_group_id", sa.String(length=40), nullable=True),
        sa.Column("split_label", sa.String(length=4), nullable=True),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("grand_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("po_number"),
    )
    op.create_index(op.f("ix_purchase_orders_po_number"), "purchase_orders", ["po_number"], unique=False)
    op.create_index(op.f("ix_purchase_orders_split_group_id"), "purchase_orders", ["split_group_id"], unique=False)
    op.create_index(op.f("ix_purchase_orders_status"), "purchase_orders", ["status"], unique=False)
    op.create_index(op.f("ix_purchase_orders_vendor_id"), "purchase_orders", ["vendor_id"], unique=False)

    op.create_foreign_key(
        "fk_vendor_ratings_purchase_order_id",
        "vendor_ratings",
        "purchase_orders",
        ["purchase_order_id"],
        ["id"],
    )

    op.create_table(
        "approval_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("approval_request_id", sa.Integer(), nullable=False),
        sa.Column("approver_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_approval_steps_approval_request_id"), "approval_steps", ["approval_request_id"], unique=False
    )

    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=180), nullable=False),
        sa.Column("hsn_sac", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("received_quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("accepted_quantity", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_purchase_order_items_purchase_order_id"),
        "purchase_order_items",
        ["purchase_order_id"],
        unique=False,
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(length=40), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("cgst_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("sgst_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("igst_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("grand_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("match_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number"),
    )
    op.create_index(op.f("ix_invoices_invoice_number"), "invoices", ["invoice_number"], unique=False)
    op.create_index(op.f("ix_invoices_purchase_order_id"), "invoices", ["purchase_order_id"], unique=False)
    op.create_index(op.f("ix_invoices_status"), "invoices", ["status"], unique=False)
    op.create_index(op.f("ix_invoices_vendor_id"), "invoices", ["vendor_id"], unique=False)

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=180), nullable=False),
        sa.Column("hsn_sac", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("gst_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invoice_items_invoice_id"), "invoice_items", ["invoice_id"], unique=False)

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=False),
        sa.Column("entry_hash", sa.String(length=64), nullable=False),
        sa.Column("block_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["block_id"], ["activity_log_blocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entry_hash"),
    )
    op.create_index(op.f("ix_activity_logs_actor_id"), "activity_logs", ["actor_id"], unique=False)
    op.create_index(op.f("ix_activity_logs_block_id"), "activity_logs", ["block_id"], unique=False)
    op.create_index("ix_activity_logs_chain", "activity_logs", ["id", "previous_hash", "entry_hash"], unique=False)
    op.create_index(op.f("ix_activity_logs_entity_id"), "activity_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_activity_logs_entity_type"), "activity_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_activity_logs_event_type"), "activity_logs", ["event_type"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("related_entity_type", sa.String(length=80), nullable=True),
        sa.Column("related_entity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)

    op.create_table(
        "email_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_outbox_to_email"), "email_outbox", ["to_email"], unique=False)

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION forbid_activity_ledger_mutation()
            RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION 'activity ledger tables are append-only';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute(
            """
            CREATE TRIGGER activity_logs_no_update_delete
            BEFORE UPDATE OR DELETE ON activity_logs
            FOR EACH ROW EXECUTE FUNCTION forbid_activity_ledger_mutation();
            """
        )
        op.execute(
            """
            CREATE TRIGGER activity_log_blocks_no_update_delete
            BEFORE UPDATE OR DELETE ON activity_log_blocks
            FOR EACH ROW EXECUTE FUNCTION forbid_activity_ledger_mutation();
            """
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS activity_logs_no_update_delete ON activity_logs")
        op.execute("DROP TRIGGER IF EXISTS activity_log_blocks_no_update_delete ON activity_log_blocks")
        op.execute("DROP FUNCTION IF EXISTS forbid_activity_ledger_mutation")

    op.drop_index(op.f("ix_email_outbox_to_email"), table_name="email_outbox")
    op.drop_table("email_outbox")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_activity_logs_event_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_entity_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_entity_id"), table_name="activity_logs")
    op.drop_index("ix_activity_logs_chain", table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_block_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_actor_id"), table_name="activity_logs")
    op.drop_table("activity_logs")
    op.drop_index(op.f("ix_invoice_items_invoice_id"), table_name="invoice_items")
    op.drop_table("invoice_items")
    op.drop_index(op.f("ix_invoices_vendor_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_status"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_purchase_order_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_invoice_number"), table_name="invoices")
    op.drop_table("invoices")
    op.drop_index(op.f("ix_purchase_order_items_purchase_order_id"), table_name="purchase_order_items")
    op.drop_table("purchase_order_items")
    op.drop_index(op.f("ix_approval_steps_approval_request_id"), table_name="approval_steps")
    op.drop_table("approval_steps")
    op.drop_constraint("fk_vendor_ratings_purchase_order_id", "vendor_ratings", type_="foreignkey")
    op.drop_index(op.f("ix_purchase_orders_vendor_id"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_status"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_split_group_id"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_po_number"), table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_index(op.f("ix_approval_requests_quotation_id"), table_name="approval_requests")
    op.drop_index(op.f("ix_approval_requests_status"), table_name="approval_requests")
    op.drop_index(op.f("ix_approval_requests_rfq_id"), table_name="approval_requests")
    op.drop_table("approval_requests")
    op.drop_index(op.f("ix_quotation_items_quotation_id"), table_name="quotation_items")
    op.drop_table("quotation_items")
    op.drop_index(op.f("ix_quotations_vendor_id"), table_name="quotations")
    op.drop_index(op.f("ix_quotations_status"), table_name="quotations")
    op.drop_index(op.f("ix_quotations_rfq_id"), table_name="quotations")
    op.drop_table("quotations")
    op.drop_index(op.f("ix_rfq_vendor_invites_vendor_id"), table_name="rfq_vendor_invites")
    op.drop_index(op.f("ix_rfq_vendor_invites_rfq_id"), table_name="rfq_vendor_invites")
    op.drop_table("rfq_vendor_invites")
    op.drop_index(op.f("ix_rfq_items_rfq_id"), table_name="rfq_items")
    op.drop_table("rfq_items")
    op.drop_index(op.f("ix_vendor_ratings_vendor_id"), table_name="vendor_ratings")
    op.drop_table("vendor_ratings")
    op.drop_index(op.f("ix_rfqs_title"), table_name="rfqs")
    op.drop_index(op.f("ix_rfqs_status"), table_name="rfqs")
    op.drop_table("rfqs")
    op.drop_index("ix_vendors_status_category", table_name="vendors")
    op.drop_index(op.f("ix_vendors_status"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_pan"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_name"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_lifecycle_stage"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_gstin"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_contact_email"), table_name="vendors")
    op.drop_table("vendors")
    op.drop_table("activity_log_blocks")
    op.drop_table("budgets")
    op.drop_table("vendor_categories")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

