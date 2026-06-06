"""PostgreSQL-native performance, scale and security optimizations.

This migration turns the schema from a plain relational store into an actively
optimized PostgreSQL workload. Everything Postgres-specific is guarded behind a
dialect check so the same migration still runs cleanly on the SQLite database
used for fast local dev and the test-suite (the Postgres-only objects are simply
skipped there, and the equivalent guarantees are kept at the application layer).

Features added on PostgreSQL:

1. JSONB ``custom_attributes`` on ``vendors`` and ``rfqs`` with GIN indexes,
   plus an upgrade of existing JSON columns to binary ``jsonb``.
2. Native full-text search on ``vendors`` via a generated ``tsvector`` column
   and a GIN index (no ElasticSearch needed).
3. Declarative range partitioning of the append-only ``activity_logs`` ledger
   by month, for partition pruning as the audit trail grows.
4. A ``vendor_kpi_dashboard`` materialized view for O(1) dashboard loads.
5. Partial (filtered) indexes for the hot "open work" queries.
6. A schema-level CHECK that forbids marking an invoice payable/paid unless the
   3-way match passed.
7. Row-level security policies enforcing vendor data isolation at the database.

Revision ID: 0002_postgres_optimizations
Revises: 0001_initial_schema
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.db.optimizations import JSONColumn

revision: str = "0002_postgres_optimizations"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Monthly partitions seeded around the hackathon timeframe. The DEFAULT
# partition guarantees correctness for any date outside this window.
_PARTITION_MONTHS = [
    ("2026_04", "2026-04-01", "2026-05-01"),
    ("2026_05", "2026-05-01", "2026-06-01"),
    ("2026_06", "2026-06-01", "2026-07-01"),
    ("2026_07", "2026-07-01", "2026-08-01"),
    ("2026_08", "2026-08-01", "2026-09-01"),
]


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Semi-structured custom fields (works on both dialects).
    # ------------------------------------------------------------------ #
    op.add_column(
        "vendors",
        sa.Column(
            "custom_attributes",
            JSONColumn,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column(
        "rfqs",
        sa.Column(
            "custom_attributes",
            JSONColumn,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )

    if not _is_postgres():
        # SQLite path: the JSON column above is enough. The CHECK constraint,
        # RLS, FTS, partitioning and materialized view are PostgreSQL features;
        # the application layer upholds the equivalent guarantees in tests.
        return

    # ------------------------------------------------------------------ #
    # 2. Upgrade existing JSON columns to binary, indexable JSONB.
    # ------------------------------------------------------------------ #
    for table, column in (
        ("vendors", "custom_attributes"),
        ("rfqs", "custom_attributes"),
        ("quotations", "score_breakdown"),
        ("approval_requests", "risk_breakdown"),
        ("approval_requests", "budget_impact"),
        ("approval_requests", "policy_reasons"),
    ):
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE jsonb "
            f"USING {column}::jsonb"
        )

    # GIN indexes make ``custom_attributes @> '{{...}}'`` containment queries
    # use an index instead of a sequential scan.
    op.execute(
        "CREATE INDEX ix_vendors_custom_attributes_gin "
        "ON vendors USING gin (custom_attributes jsonb_path_ops)"
    )
    op.execute(
        "CREATE INDEX ix_rfqs_custom_attributes_gin "
        "ON rfqs USING gin (custom_attributes jsonb_path_ops)"
    )

    # ------------------------------------------------------------------ #
    # 3. Native full-text search on vendors (generated tsvector + GIN).
    # ------------------------------------------------------------------ #
    op.execute(
        """
        ALTER TABLE vendors ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector(
                'english',
                coalesce(name, '') || ' ' ||
                coalesce(legal_name, '') || ' ' ||
                coalesce(city, '') || ' ' ||
                coalesce(state, '') || ' ' ||
                coalesce(gstin, '')
            )
        ) STORED
        """
    )
    op.execute("CREATE INDEX ix_vendors_search_vector ON vendors USING gin (search_vector)")

    # ------------------------------------------------------------------ #
    # 4. Declarative range partitioning of the immutable ledger by month.
    #    The table is empty at migration time, so we recreate it partitioned.
    # ------------------------------------------------------------------ #
    op.execute("DROP TABLE activity_logs CASCADE")
    op.execute(
        """
        CREATE TABLE activity_logs (
            id integer GENERATED BY DEFAULT AS IDENTITY,
            actor_id integer REFERENCES users (id),
            event_type varchar(80) NOT NULL,
            entity_type varchar(80) NOT NULL,
            entity_id integer,
            summary varchar(255) NOT NULL,
            payload jsonb NOT NULL,
            previous_hash varchar(64) NOT NULL,
            entry_hash varchar(64) NOT NULL,
            block_id integer REFERENCES activity_log_blocks (id),
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (id, created_at),
            UNIQUE (entry_hash, created_at)
        ) PARTITION BY RANGE (created_at)
        """
    )
    for suffix, start, end in _PARTITION_MONTHS:
        op.execute(
            f"CREATE TABLE activity_logs_{suffix} PARTITION OF activity_logs "
            f"FOR VALUES FROM ('{start}') TO ('{end}')"
        )
    op.execute(
        "CREATE TABLE activity_logs_default PARTITION OF activity_logs DEFAULT"
    )

    op.create_index("ix_activity_logs_actor_id", "activity_logs", ["actor_id"])
    op.create_index("ix_activity_logs_block_id", "activity_logs", ["block_id"])
    op.create_index(
        "ix_activity_logs_chain", "activity_logs", ["id", "previous_hash", "entry_hash"]
    )
    op.create_index("ix_activity_logs_entity_id", "activity_logs", ["entity_id"])
    op.create_index("ix_activity_logs_entity_type", "activity_logs", ["entity_type"])
    op.create_index("ix_activity_logs_event_type", "activity_logs", ["event_type"])

    # Re-apply append-only protection. A BEFORE ROW trigger on the partitioned
    # parent cascades to every current and future partition (PostgreSQL 13+).
    op.execute(
        """
        CREATE TRIGGER activity_logs_no_update_delete
        BEFORE UPDATE OR DELETE ON activity_logs
        FOR EACH ROW EXECUTE FUNCTION forbid_activity_ledger_mutation()
        """
    )

    # ------------------------------------------------------------------ #
    # 5. Materialized view for the vendor KPI dashboard.
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE MATERIALIZED VIEW vendor_kpi_dashboard AS
        SELECT
            v.id                       AS vendor_id,
            v.name                     AS vendor_name,
            v.lifecycle_stage          AS lifecycle_stage,
            v.status                   AS status,
            v.category_id              AS category_id,
            v.rating                   AS rating,
            v.completed_orders_count   AS completed_orders_count,
            (SELECT count(*) FROM purchase_orders po WHERE po.vendor_id = v.id)
                                       AS total_purchase_orders,
            (SELECT coalesce(sum(i.grand_total), 0) FROM invoices i WHERE i.vendor_id = v.id)
                                       AS total_spend,
            (SELECT coalesce(
                        avg((r.quality_score + r.delivery_speed_score
                             + r.communication_score + r.service_score) / 4.0), 0)
                FROM vendor_ratings r WHERE r.vendor_id = v.id)
                                       AS avg_rating
        FROM vendors v
        WITH DATA
        """
    )
    # Unique index is mandatory for REFRESH MATERIALIZED VIEW CONCURRENTLY.
    op.execute(
        "CREATE UNIQUE INDEX ix_vendor_kpi_dashboard_vendor_id "
        "ON vendor_kpi_dashboard (vendor_id)"
    )
    op.execute(
        "CREATE INDEX ix_vendor_kpi_dashboard_spend ON vendor_kpi_dashboard (total_spend DESC)"
    )

    # ------------------------------------------------------------------ #
    # 6. Partial (filtered) indexes for hot "open work" queries.
    # ------------------------------------------------------------------ #
    op.execute(
        "CREATE INDEX ix_approval_requests_pending ON approval_requests (created_at) "
        "WHERE status = 'pending'"
    )
    op.execute(
        "CREATE INDEX ix_rfqs_active ON rfqs (deadline) WHERE status = 'sent'"
    )
    op.execute(
        "CREATE INDEX ix_quotations_open ON quotations (rfq_id) "
        "WHERE status IN ('draft', 'submitted')"
    )
    op.execute(
        "CREATE INDEX ix_invoices_outstanding ON invoices (due_date) "
        "WHERE status IN ('sent', 'payable', 'overdue')"
    )
    op.execute(
        "CREATE INDEX ix_purchase_orders_in_flight ON purchase_orders (created_at) "
        "WHERE status NOT IN ('closed', 'cancelled')"
    )

    # ------------------------------------------------------------------ #
    # 7. Schema-level 3-way match enforcement on invoices.
    # ------------------------------------------------------------------ #
    op.create_check_constraint(
        "ck_invoices_three_way_match",
        "invoices",
        "status not in ('payable','paid') or match_status = 'matched'",
    )

    # ------------------------------------------------------------------ #
    # 8. Row-level security: vendor data isolation at the database layer.
    # ------------------------------------------------------------------ #
    for table in ("quotations", "rfq_vendor_invites"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        # FORCE so the table owner (the app's own role) is also subject to the
        # policy — otherwise RLS would be silently bypassed for the app user.
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            FOR ALL
            USING (
                current_setting('vendorbridge.role', true) IS DISTINCT FROM 'vendor'
                OR vendor_id = NULLIF(current_setting('vendorbridge.vendor_id', true), '')::int
            )
            WITH CHECK (
                current_setting('vendorbridge.role', true) IS DISTINCT FROM 'vendor'
                OR vendor_id = NULLIF(current_setting('vendorbridge.vendor_id', true), '')::int
            )
            """
        )


def downgrade() -> None:
    if _is_postgres():
        for table in ("quotations", "rfq_vendor_invites"):
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
            op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

        op.drop_constraint("ck_invoices_three_way_match", "invoices", type_="check")

        for name in (
            "ix_purchase_orders_in_flight",
            "ix_invoices_outstanding",
            "ix_quotations_open",
            "ix_rfqs_active",
            "ix_approval_requests_pending",
        ):
            op.execute(f"DROP INDEX IF EXISTS {name}")

        op.execute("DROP MATERIALIZED VIEW IF EXISTS vendor_kpi_dashboard")

        # Rebuild activity_logs as a plain (non-partitioned) table.
        op.execute("DROP TABLE IF EXISTS activity_logs CASCADE")
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
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["block_id"], ["activity_log_blocks.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("entry_hash"),
        )
        op.create_index("ix_activity_logs_actor_id", "activity_logs", ["actor_id"])
        op.create_index("ix_activity_logs_block_id", "activity_logs", ["block_id"])
        op.create_index(
            "ix_activity_logs_chain", "activity_logs", ["id", "previous_hash", "entry_hash"]
        )
        op.create_index("ix_activity_logs_entity_id", "activity_logs", ["entity_id"])
        op.create_index("ix_activity_logs_entity_type", "activity_logs", ["entity_type"])
        op.create_index("ix_activity_logs_event_type", "activity_logs", ["event_type"])
        op.execute(
            """
            CREATE TRIGGER activity_logs_no_update_delete
            BEFORE UPDATE OR DELETE ON activity_logs
            FOR EACH ROW EXECUTE FUNCTION forbid_activity_ledger_mutation()
            """
        )

        op.execute("DROP INDEX IF EXISTS ix_vendors_search_vector")
        op.execute("ALTER TABLE vendors DROP COLUMN IF EXISTS search_vector")
        op.execute("DROP INDEX IF EXISTS ix_rfqs_custom_attributes_gin")
        op.execute("DROP INDEX IF EXISTS ix_vendors_custom_attributes_gin")

    op.drop_column("rfqs", "custom_attributes")
    op.drop_column("vendors", "custom_attributes")
