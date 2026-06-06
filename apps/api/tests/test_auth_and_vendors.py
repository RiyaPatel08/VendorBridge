from app.core.security import hash_password
from app.models.entities import User, VendorCategory
from tests.conftest import get_client, get_test_db, reset_db


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_vendor_self_registration_flow() -> None:
    reset_db()
    db = next(get_test_db())
    try:
        db.add(VendorCategory(name="Furniture", code="FURN", is_active=True))
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
    officer_response = client.post(
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
    assert officer_response.status_code == 201
    officer_token = officer_response.json()["access_token"]

    manual_create_response = client.post(
        "/api/v1/vendors",
        headers=auth_header(officer_token),
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
        },
    )
    assert manual_create_response.status_code == 403
    assert manual_create_response.json()["detail"] == (
        "Vendors must self-register before admin verification"
    )

    vendor_response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Meera",
            "last_name": "Patel",
            "email": "sales@infra.test",
            "phone": "+91 98765 10001",
            "role": "vendor",
            "password": "VendorBridge@123",
        },
    )
    assert vendor_response.status_code == 201
    vendor_token = vendor_response.json()["access_token"]

    profile_response = client.post(
        "/api/v1/vendors/self-register",
        headers=auth_header(vendor_token),
        json={
            "name": "Infra Supplies Pvt Ltd",
            "legal_name": "Infra Supplies Private Limited",
            "category_id": 1,
            "gstin": "24INFRA1234F1Z5",
            "pan": "INFRA1234F",
            "state": "Gujarat",
            "city": "Surat",
            "contact_phone": "+91 98765 10001",
            "compliance_notes": "GST and PAN documents uploaded.",
        },
    )
    assert profile_response.status_code == 201
    vendor = profile_response.json()
    assert vendor["status"] == "pending"
    assert vendor["lifecycle_stage"] == "potential"
    assert vendor["is_gstin_verified"] is False
    assert vendor["compliance_badge"] == "needs_review"

    list_response = client.get("/api/v1/vendors?search=Infra", headers=auth_header(officer_token))
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.test", "password": "VendorBridge@123"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    verify_response = client.post(
        f"/api/v1/vendors/{vendor['id']}/verify", headers=auth_header(admin_token)
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["status"] == "active"
    assert verify_response.json()["is_gstin_verified"] is True
    assert verify_response.json()["compliance_badge"] == "compliant"

    block_response = client.post(
        f"/api/v1/vendors/{vendor['id']}/block", headers=auth_header(admin_token)
    )
    assert block_response.status_code == 200
    assert block_response.json()["status"] == "blocked"
    assert block_response.json()["compliance_badge"] == "blocked"

    invalid_response = client.post(
        "/api/v1/vendors/self-register",
        headers=auth_header(vendor_token),
        json={
            "name": "Bad GST Vendor",
            "category_id": 1,
            "gstin": "BAD",
            "state": "Gujarat",
            "city": "Surat",
            "contact_phone": "+91 98765 10001",
        },
    )
    assert invalid_response.status_code in {409, 422}
