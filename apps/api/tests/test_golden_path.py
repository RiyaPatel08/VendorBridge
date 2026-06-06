from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.common.enums import UserRole
from app.core.security import hash_password
from app.models.entities import User, Vendor, VendorCategory
from tests.conftest import get_client, get_test_db, reset_db


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_user(db, email: str, role: UserRole) -> User:
    user = User(
        email=email,
        first_name=email.split("@")[0],
        last_name="User",
        phone="+91 90000 00000",
        role=role.value,
        hashed_password=hash_password("VendorBridge@123"),
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def test_rfq_to_invoice_golden_path() -> None:
    reset_db()
    db = next(get_test_db())
    try:
        create_user(db, "admin@vendorbridge.test", UserRole.admin)
        create_user(db, "officer@vendorbridge.test", UserRole.procurement_officer)
        create_user(db, "rahul.mehta@vendorbridge.test", UserRole.manager)
        create_user(db, "priya.shah@vendorbridge.test", UserRole.manager)
        create_user(db, "vendor@infrasupplies.test", UserRole.vendor)
        create_user(db, "quotes@techcore.test", UserRole.vendor)
        category = VendorCategory(name="Furniture", code="FURN", is_active=True)
        db.add(category)
        db.flush()
        vendors = [
            Vendor(
                name="Infra Supplies Pvt Ltd",
                legal_name="Infra Supplies Private Limited",
                category_id=category.id,
                gstin="24INFRA1234F1Z5",
                pan="INFRA1234F",
                state="Gujarat",
                city="Surat",
                contact_name="Meera Patel",
                contact_email="vendor@infrasupplies.test",
                contact_phone="+91 98765 10001",
                status="active",
                lifecycle_stage="trusted",
                completed_orders_count=32,
                rating=Decimal("4.50"),
                reliability_score=Decimal("91.00"),
                delivery_score=Decimal("88.00"),
                completion_rate=Decimal("96.00"),
                satisfaction_score=Decimal("90.00"),
                is_gstin_verified=True,
                is_pan_verified=True,
            ),
            Vendor(
                name="TechCore Ltd",
                legal_name="TechCore Limited",
                category_id=category.id,
                gstin="24TECHC2727Q1Z1",
                pan="TECHC2727Q",
                state="Gujarat",
                city="Ahmedabad",
                contact_name="Harsh Mehta",
                contact_email="quotes@techcore.test",
                contact_phone="+91 98765 10002",
                status="active",
                lifecycle_stage="verified",
                completed_orders_count=11,
                rating=Decimal("3.80"),
                reliability_score=Decimal("78.00"),
                delivery_score=Decimal("84.00"),
                completion_rate=Decimal("86.00"),
                satisfaction_score=Decimal("76.00"),
                is_gstin_verified=True,
                is_pan_verified=True,
            ),
        ]
        db.add_all(vendors)
        db.commit()
    finally:
        db.close()

    client = get_client()
    officer_token = client.post(
        "/api/v1/auth/login",
        json={"email": "officer@vendorbridge.test", "password": "VendorBridge@123"},
    ).json()["access_token"]
    winning_vendor_token = client.post(
        "/api/v1/auth/login",
        json={"email": "vendor@infrasupplies.test", "password": "VendorBridge@123"},
    ).json()["access_token"]
    other_vendor_token = client.post(
        "/api/v1/auth/login",
        json={"email": "quotes@techcore.test", "password": "VendorBridge@123"},
    ).json()["access_token"]

    rfq_response = client.post(
        "/api/v1/rfqs",
        headers=auth_header(officer_token),
        json={
            "title": "Office Furniture Procurement Q2",
            "category_id": 1,
            "description": "Furniture",
            "deadline": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
            "vendor_ids": [1, 2],
            "items": [
                {
                    "item_name": "Ergonomic chair",
                    "hsn_sac": "9403",
                    "quantity": "25",
                    "unit": "NOS",
                },
                {"item_name": "Standing desk", "hsn_sac": "9403", "quantity": "10", "unit": "NOS"},
            ],
        },
    )
    assert rfq_response.status_code == 201
    rfq = rfq_response.json()
    assert (
        client.post(
            f"/api/v1/rfqs/{rfq['id']}/send", headers=auth_header(officer_token)
        ).status_code
        == 200
    )

    officer_quote = client.post(
        "/api/v1/quotations/drafts",
        headers=auth_header(officer_token),
        json={
            "rfq_id": rfq["id"],
            "vendor_id": 1,
            "delivery_days": 10,
            "payment_terms_days": 30,
            "items": [
                {
                    "rfq_item_id": rfq["items"][0]["id"],
                    "quantity": "25",
                    "unit_price": "4200",
                    "gst_percent": "18",
                    "available_quantity": "25",
                    "additional_quantity": "0",
                }
            ],
        },
    )
    assert officer_quote.status_code == 403

    quote_tokens = {1: winning_vendor_token, 2: other_vendor_token}
    for vendor_id, chair_price, desk_price in [(1, "4200", "5200"), (2, "4700", "6300")]:
        draft = client.post(
            "/api/v1/quotations/drafts",
            headers=auth_header(quote_tokens[vendor_id]),
            json={
                "rfq_id": rfq["id"],
                "vendor_id": vendor_id,
                "delivery_days": 10,
                "payment_terms_days": 30,
                "items": [
                    {
                        "rfq_item_id": rfq["items"][0]["id"],
                        "quantity": "25",
                        "unit_price": chair_price,
                        "gst_percent": "18",
                        "available_quantity": "25",
                        "additional_quantity": "0",
                    },
                    {
                        "rfq_item_id": rfq["items"][1]["id"],
                        "quantity": "10",
                        "unit_price": desk_price,
                        "gst_percent": "18",
                        "available_quantity": "10",
                        "additional_quantity": "0",
                    },
                ],
            },
        )
        assert draft.status_code == 201
        assert (
            client.post(
                f"/api/v1/quotations/{draft.json()['id']}/submit",
                headers=auth_header(quote_tokens[vendor_id]),
            ).status_code
            == 200
        )

    comparison = client.get(
        f"/api/v1/rfqs/{rfq['id']}/comparison", headers=auth_header(officer_token)
    )
    assert comparison.status_code == 200
    selected_quotation_id = comparison.json()["rows"][0]["quotation_id"]
    approval_id = client.post(
        f"/api/v1/rfqs/{rfq['id']}/select-quotation",
        headers=auth_header(officer_token),
        json={"quotation_id": selected_quotation_id},
    ).json()["approval_request_id"]

    manager_token = client.post(
        "/api/v1/auth/login",
        json={"email": "rahul.mehta@vendorbridge.test", "password": "VendorBridge@123"},
    ).json()["access_token"]
    finance_token = client.post(
        "/api/v1/auth/login",
        json={"email": "priya.shah@vendorbridge.test", "password": "VendorBridge@123"},
    ).json()["access_token"]
    assert (
        client.post(
            f"/api/v1/approvals/{approval_id}/approve",
            headers=auth_header(manager_token),
            json={"remarks": "L1 approved"},
        ).status_code
        == 200
    )
    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers=auth_header(finance_token),
        json={"remarks": "Finance approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    po = client.post(
        f"/api/v1/approvals/{approval_id}/purchase-order",
        headers=auth_header(officer_token),
    )
    assert po.status_code == 200
    po_id = po.json()["id"]
    assert (
        client.post(
            f"/api/v1/purchase-orders/{po_id}/accept",
            headers=auth_header(other_vendor_token),
            json={},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/purchase-orders/{po_id}/accept",
            headers=auth_header(winning_vendor_token),
            json={},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/purchase-orders/{po_id}/receive", headers=auth_header(officer_token)
        ).status_code
        == 200
    )
    invoice = client.post(
        f"/api/v1/purchase-orders/{po_id}/invoice", headers=auth_header(officer_token)
    )
    assert invoice.status_code == 200
    invoice_id = invoice.json()["id"]
    assert invoice.json()["match_status"] == "matched"
    assert (
        client.post(
            f"/api/v1/invoices/{invoice_id}/payable", headers=auth_header(finance_token)
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/invoices/{invoice_id}/email",
            headers=auth_header(officer_token),
            json={"to_email": "accounts@infrasupplies.com"},
        ).status_code
        == 200
    )
    admin_token = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@vendorbridge.test", "password": "VendorBridge@123"},
    ).json()["access_token"]
    verify = client.get("/api/v1/activity/verify", headers=auth_header(admin_token))
    assert verify.status_code == 200
    assert verify.json()["ok"] is True
