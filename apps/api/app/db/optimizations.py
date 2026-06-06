"""PostgreSQL-native optimization helpers.

VendorBridge treats PostgreSQL as an active computing layer rather than a dumb
data store. This module is the single, modular home for the application-side
wiring of the Postgres-only features defined in migration ``0002`` (row-level
security, materialized views, full-text search, JSONB containment). Every
helper degrades gracefully on SQLite so the test-suite and quick local dev
setup keep working without a Postgres server.

Design rule: feature detection is done once via :func:`is_postgres`; callers
never branch on raw dialect strings.
"""

from __future__ import annotations

from sqlalchemy import JSON, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

# A JSON column that becomes native ``jsonb`` on PostgreSQL (binary, indexable,
# supports the ``@>`` containment operator and GIN indexes) while staying plain
# ``JSON`` on SQLite so the same models work in tests.
JSONColumn = JSON().with_variant(JSONB(), "postgresql")

# Session-local GUC names used by the row-level security policies. They are set
# per request from the authenticated principal and isolate vendor data at the
# database layer even if an API handler forgets to add a ``WHERE`` clause.
RLS_ROLE_SETTING = "vendorbridge.role"
RLS_VENDOR_SETTING = "vendorbridge.vendor_id"

VENDOR_KPI_VIEW = "vendor_kpi_dashboard"


def is_postgres(db: Session) -> bool:
    """Return ``True`` when the active session is backed by PostgreSQL."""

    return db.bind is not None and db.bind.dialect.name == "postgresql"


def set_rls_context(db: Session, *, role: str, vendor_id: int | None) -> None:
    """Bind the current principal to the session for row-level security.

    Uses ``SET LOCAL`` so the values are scoped to the current transaction and
    can never leak across pooled connections. On SQLite this is a no-op because
    RLS does not exist there; the application-layer authorization checks remain
    the active safeguard in that environment.
    """

    if not is_postgres(db):
        return
    # set_config(setting, value, is_local=true) is parameterizable, which avoids
    # any SQL-injection surface that string-interpolated ``SET LOCAL`` would have.
    db.execute(
        text("SELECT set_config(:k, :v, true)"),
        {"k": RLS_ROLE_SETTING, "v": role},
    )
    db.execute(
        text("SELECT set_config(:k, :v, true)"),
        {"k": RLS_VENDOR_SETTING, "v": "" if vendor_id is None else str(vendor_id)},
    )


def refresh_vendor_kpis(db: Session, *, concurrently: bool = False) -> bool:
    """Refresh the dashboard materialized view. No-op (returns ``False``) on SQLite.

    ``CONCURRENTLY`` lets the dashboard keep serving the previous snapshot while
    the new one is computed, but it requires a unique index and cannot run
    inside a surrounding transaction block, so it is opt-in.
    """

    if not is_postgres(db):
        return False
    keyword = "CONCURRENTLY " if concurrently else ""
    db.execute(text(f"REFRESH MATERIALIZED VIEW {keyword}{VENDOR_KPI_VIEW}"))
    return True
