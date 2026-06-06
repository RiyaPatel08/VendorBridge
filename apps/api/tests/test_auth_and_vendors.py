from app.core.security import hash_password
from app.models.entities import User, VendorCategory
from tests.conftest import get_client, get_test_db, reset_db


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_vendor_management_flow() -> None:
    reset_db()
    db = next(get_test_db())
    try:
        db.add(VendorCategory(name="Furniture", code="FURN", is_active=True))
        # Admin accounts are provisioned by the platform, not via self-register.
        db.add(
            User(
                email="admin@example.test",
                first_name="Asha",
                last_name="Admin",
                phone="+91 90000 00001",
                role="admin",
                hashed_password=hash_password("VendorBridge@123"),
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()

    client = get_client()
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Neel",
            "last_name": "Shah",
            "email": "officer@example.test",
            "phone": "+91 90000 00000",
            "role": "procurement_officer",
            "password": "VendorBridge@123",
        },
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "procurement_officer"

    create_response = client.post(
        "/api/v1/vendors",
        headers=auth_header(token),
        json={
            "name": "Infra Supplies Pvt Ltd",
            "legal_name": "Infra Supplies Private Limited",
            "category_id": 1,
            "gstin": "24INFRA1234F1Z5",
            "pan": "INFRA1234F",
            "state": "Gujarat",
            "city": "Surat",
            "contact_name": "Meera Patel",
            "contact_email": "sales@infra.test",
            "contact_phone": "+91 98765 10001",
            "status": "active",
            "completed_orders_count": 32,
            "rating": "4.50",
            "reliability_score": "91.00",
            "delivery_score": "88.00",
            "completion_rate": "96.00",
            "satisfaction_score": "90.00",
            "compliance_notes": "GST and PAN verified.",
        },
    )
    assert create_response.status_code == 201
    vendor = create_response.json()
    assert vendor["lifecycle_stage"] == "trusted"
    assert vendor["compliance_badge"] == "compliant"

    list_response = client.get("/api/v1/vendors?search=Infra", headers=auth_header(token))
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.test", "password": "VendorBridge@123"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    block_response = client.post(
        f"/api/v1/vendors/{vendor['id']}/block", headers=auth_header(admin_token)
    )
    assert block_response.status_code == 200
    assert block_response.json()["status"] == "blocked"
    assert block_response.json()["compliance_badge"] == "blocked"

    invalid_response = client.post(
        "/api/v1/vendors",
        headers=auth_header(token),
        json={
            "name": "Bad GST Vendor",
            "category_id": 1,
            "gstin": "BAD",
            "state": "Gujarat",
            "city": "Surat",
            "contact_name": "Bad Vendor",
            "contact_email": "bad@example.test",
            "contact_phone": "+91 98765 10001",
        },
    )
    assert invalid_response.status_code == 422
