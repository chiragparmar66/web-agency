import hashlib
import hmac
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.init_db import seed_initial_data
from app.models.enums import PaymentStatus, PaymentType, ProjectStatus
from app.models.pricing_package import PricingPackage
from app.models.project import Project


def generate_valid_signature(order_id: str, payment_id: str, secret: str = settings.RAZORPAY_KEY_SECRET) -> str:
    """Helper to generate authentic Razorpay HMAC-SHA256 signature."""
    message = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


async def register_customer_and_create_project(
    client: AsyncClient,
    email: str = "payment.client@studio.dev",
    package_id: str = None,
) -> tuple[str, str, dict]:
    """Helper to create customer and project. Returns (token, project_id, headers)."""
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass2026!",
            "full_name": "Rohan Sharma",
            "phone": "+919876543210",
        },
    )
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_payload = {
        "title": "E-Commerce Luxury Website",
        "business_name": "Sharma Gems & Jewels",
    }
    if package_id:
        proj_payload["package_id"] = package_id

    proj_res = await client.post("/api/v1/projects", headers=headers, json=proj_payload)
    project_id = proj_res.json()["data"]["id"]
    return token, project_id, headers


@pytest.mark.asyncio
async def test_create_payment_order_with_package_calculation(client: AsyncClient, db_session: AsyncSession):
    """Test creating payment order with server-side price calculation and invoice generation."""
    await seed_initial_data(db_session)

    # Get Business package (₹4,999)
    pkg_stmt = select(PricingPackage).where(PricingPackage.slug == "business-website")
    pkg = (await db_session.execute(pkg_stmt)).scalar_one()

    _, project_id, headers = await register_customer_and_create_project(
        client, "order.test@studio.dev", package_id=pkg.id
    )

    # Create ADVANCE order (50% of ₹4,999 = ₹2,499.50)
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=headers,
        json={"project_id": project_id, "payment_type": "ADVANCE"},
    )
    assert order_res.status_code == 201
    data = order_res.json()["data"]
    assert data["amount_inr"] == 2499.50
    assert data["amount_paise"] == 249950
    assert data["currency"] == "INR"
    assert data["invoice_number"].startswith("INV-2026-")
    assert data["customer_name"] == "Rohan Sharma"
    assert data["customer_phone"] == "+919876543210"
    assert data["order_id"].startswith("order_")


@pytest.mark.asyncio
async def test_verify_valid_signature_success(client: AsyncClient, db_session: AsyncSession):
    """Test authentic Razorpay signature verification and lifecycle progression."""
    _, project_id, headers = await register_customer_and_create_project(client, "verify.test@studio.dev")

    # 1. Create order
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=headers,
        json={"project_id": project_id, "payment_type": "ADVANCE"},
    )
    order_data = order_res.json()["data"]
    order_id = order_data["order_id"]

    # 2. Simulate successful checkout with valid HMAC signature
    fake_payment_id = "pay_test_abc123456"
    valid_sig = generate_valid_signature(order_id, fake_payment_id)

    verify_res = await client.post(
        "/api/v1/payments/verify",
        headers=headers,
        json={
            "project_id": project_id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": fake_payment_id,
            "razorpay_signature": valid_sig,
        },
    )
    assert verify_res.status_code == 200
    res_data = verify_res.json()["data"]
    assert res_data["status"] == "SUCCESS"
    assert res_data["razorpay_payment_id"] == fake_payment_id
    assert res_data["paid_at"] is not None

    # 3. Verify project lifecycle updated to REQUIREMENTS_PENDING and audit log created
    proj_chk = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    p_info = proj_chk.json()["data"]
    assert p_info["status"] == "REQUIREMENTS_PENDING"

    activities = p_info["activities"]
    pay_act = next((a for a in activities if a["action_type"] == "PAYMENT_COMPLETED"), None)
    assert pay_act is not None
    assert "ADVANCE" in pay_act["note"]


@pytest.mark.asyncio
async def test_invalid_signature_rejected(client: AsyncClient, db_session: AsyncSession):
    """Test that forged or tampered signatures are rejected and marked FAILED."""
    _, project_id, headers = await register_customer_and_create_project(client, "forgery.test@studio.dev")

    # Create order
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=headers,
        json={"project_id": project_id, "payment_type": "ADVANCE"},
    )
    order_id = order_res.json()["data"]["order_id"]

    # Attempt verification with forged signature
    tampered_sig = "fake_tampered_signature_hex_0000000000000000"
    verify_res = await client.post(
        "/api/v1/payments/verify",
        headers=headers,
        json={
            "project_id": project_id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_forged_999",
            "razorpay_signature": tampered_sig,
        },
    )
    assert verify_res.status_code == 400
    err_body = verify_res.json()
    err_msg = err_body.get("message") or err_body.get("detail", "")
    assert "Invalid payment signature" in err_msg


@pytest.mark.asyncio
async def test_replay_attack_prevention(client: AsyncClient, db_session: AsyncSession):
    """Test that a payment_id cannot be reused/replayed to approve another project."""
    _, proj1_id, headers1 = await register_customer_and_create_project(client, "replay1@studio.dev")
    _, proj2_id, headers2 = await register_customer_and_create_project(client, "replay2@studio.dev")

    # Order 1
    o1 = (await client.post("/api/v1/payments/create-order", headers=headers1, json={"project_id": proj1_id})).json()["data"]
    reused_payment_id = "pay_replayed_12345"
    sig1 = generate_valid_signature(o1["order_id"], reused_payment_id)

    # Verify Order 1
    v1 = await client.post(
        "/api/v1/payments/verify",
        headers=headers1,
        json={
            "project_id": proj1_id,
            "razorpay_order_id": o1["order_id"],
            "razorpay_payment_id": reused_payment_id,
            "razorpay_signature": sig1,
        },
    )
    assert v1.status_code == 200

    # Order 2
    o2 = (await client.post("/api/v1/payments/create-order", headers=headers2, json={"project_id": proj2_id})).json()["data"]
    sig2 = generate_valid_signature(o2["order_id"], reused_payment_id)

    # Attempt to replay the same payment_id on Order 2
    v2 = await client.post(
        "/api/v1/payments/verify",
        headers=headers2,
        json={
            "project_id": proj2_id,
            "razorpay_order_id": o2["order_id"],
            "razorpay_payment_id": reused_payment_id,
            "razorpay_signature": sig2,
        },
    )
    assert v2.status_code == 400
    err_body = v2.json()
    err_msg = err_body.get("message") or err_body.get("detail", "")
    assert "replay attack prevented" in err_msg


@pytest.mark.asyncio
async def test_final_payment_transitions_to_deploying(client: AsyncClient, db_session: AsyncSession):
    """Test that verifying FINAL milestone transitions project to DEPLOYING status."""
    _, project_id, headers = await register_customer_and_create_project(client, "final.test@studio.dev")

    # Set project to CLIENT_REVIEW
    p_stmt = select(Project).where(Project.id == project_id)
    proj = (await db_session.execute(p_stmt)).scalar_one()
    proj.status = ProjectStatus.CLIENT_REVIEW
    await db_session.commit()

    # Create FINAL payment order
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=headers,
        json={"project_id": project_id, "payment_type": "FINAL"},
    )
    order_id = order_res.json()["data"]["order_id"]

    # Verify payment
    pay_id = "pay_final_stage_789"
    sig = generate_valid_signature(order_id, pay_id)
    v_res = await client.post(
        "/api/v1/payments/verify",
        headers=headers,
        json={
            "project_id": project_id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": pay_id,
            "razorpay_signature": sig,
        },
    )
    assert v_res.status_code == 200

    # Project status should now be DEPLOYING
    proj_chk = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert proj_chk.json()["data"]["status"] == "DEPLOYING"


@pytest.mark.asyncio
async def test_list_payments_and_invoice_details(client: AsyncClient, db_session: AsyncSession):
    """Test listing payments for a project and retrieving complete invoice receipt."""
    _, project_id, headers = await register_customer_and_create_project(client, "invoice.test@studio.dev")

    # Create order & verify
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=headers,
        json={"project_id": project_id, "payment_type": "ADVANCE"},
    )
    order_data = order_res.json()["data"]
    pay_id = "pay_inv_verified_444"
    sig = generate_valid_signature(order_data["order_id"], pay_id)

    verify_res = await client.post(
        "/api/v1/payments/verify",
        headers=headers,
        json={
            "project_id": project_id,
            "razorpay_order_id": order_data["order_id"],
            "razorpay_payment_id": pay_id,
            "razorpay_signature": sig,
        },
    )
    internal_payment_id = verify_res.json()["data"]["id"]

    # List payments
    list_res = await client.get(f"/api/v1/payments/projects/{project_id}", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # Get invoice details
    inv_res = await client.get(f"/api/v1/payments/{internal_payment_id}/invoice", headers=headers)
    assert inv_res.status_code == 200
    inv = inv_res.json()["data"]
    assert inv["payment_id"] == internal_payment_id
    assert inv["invoice_number"].startswith("INV-2026-")
    assert inv["customer_name"] == "Rohan Sharma"
    assert inv["status"] == "SUCCESS"
    assert inv["paid_at"] is not None


@pytest.mark.asyncio
async def test_payment_idor_protection(client: AsyncClient, db_session: AsyncSession):
    """Test that Customer B cannot create orders or view invoices for Customer A's project."""
    _, proj_a_id, _ = await register_customer_and_create_project(client, "client.a@studio.dev")
    _, _, headers_b = await register_customer_and_create_project(client, "client.b@studio.dev")

    # Customer B attempts to create payment order on Project A
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=headers_b,
        json={"project_id": proj_a_id, "payment_type": "ADVANCE"},
    )
    assert order_res.status_code == 403

    # Customer B attempts to list payments of Project A
    list_res = await client.get(f"/api/v1/payments/projects/{proj_a_id}", headers=headers_b)
    assert list_res.status_code == 403
