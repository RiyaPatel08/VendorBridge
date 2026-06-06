"""Tests for the PostgreSQL-native optimization wiring.

These run against SQLite (the test backend), so they cover the dialect-agnostic
contract: the cross-dialect helpers degrade gracefully, the JSONB-backed
``custom_attributes`` round-trips, the 3-way-match CHECK is enforced by the
schema, and the full-text-search query builder still works via its ILIKE
fallback. The Postgres-only objects (RLS, partitions, materialized view, GIN/FTS
indexes) are exercised live against Postgres in the migration.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.optimizations import is_postgres, refresh_vendor_kpis, set_rls_context
from app.models.entities import Invoice
from app.vendors.service import build_vendor_query
from tests.conftest import get_test_db, reset_db


def test_helpers_degrade_gracefully_on_sqlite() -> None:
    reset_db()
    db = next(get_test_db())
    try:
        assert is_postgres(db) is False
        # Must not raise and must be a no-op on SQLite.
        set_rls_context(db, role="vendor", vendor_id=7)
        assert refresh_vendor_kpis(db) is False
    finally:
        db.close()


def test_vendor_query_builder_uses_ilike_fallback() -> None:
    # When Postgres features are off, the search must compile to an ILIKE query,
    # never reference the Postgres-only search_vector column.
    query = build_vendor_query(
        search="infra",
        status_filter=None,
        category_id=None,
        use_postgres_features=False,
    )
    compiled = str(query).lower()
    assert "lower" in compiled or "like" in compiled
    assert "search_vector" not in compiled


def test_custom_attributes_round_trip() -> None:
    reset_db()
    db = next(get_test_db())
    try:
        from app.models.entities import Vendor, VendorCategory

        db.add(VendorCategory(name="Furniture", code="FURN", is_active=True))
        db.flush()
        db.add(
            Vendor(
                name="Infra Supplies Pvt Ltd",
                category_id=1,
                gstin="24INFRA1234F1Z5",
                pan="INFRA1234F",
                state="Gujarat",
                city="Surat",
                contact_name="Meera Patel",
                contact_email="sales@infra.test",
                contact_phone="+91 98765 10001",
                status="active",
                custom_attributes={"iso_certified": True, "msme_registration": "UDYAM-1"},
            )
        )
        db.commit()
        vendor = db.query(Vendor).filter_by(gstin="24INFRA1234F1Z5").one()
        assert vendor.custom_attributes == {
            "iso_certified": True,
            "msme_registration": "UDYAM-1",
        }
    finally:
        db.close()


def test_invoice_three_way_match_check_constraint() -> None:
    reset_db()
    db = next(get_test_db())
    try:
        # The schema must refuse a payable invoice that has not passed 3-way match.
        db.add(
            Invoice(
                invoice_number="INV-TEST-0001",
                purchase_order_id=1,
                vendor_id=1,
                invoice_date=date.today(),
                due_date=date.today(),
                status="payable",
                match_status="pending",
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()
