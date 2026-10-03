import hashlib
import hmac
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.init_db import seed_initial_data
from app.models.enums import BuildStatus, PaymentStatus, PaymentType, ProjectStatus, UserRole
from app.models.pricing_package import PricingPackage
from app.models.project import Project
from app.models.payment import Payment
from app.models.user import User


def generate_valid_signature(order_id: str, payment_id: str, secret: str = settings.RAZORPAY_KEY_SECRET) -> str:
    """Helper to generate authentic Razorpay HMAC-SHA256 signature."""
    message = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


async def setup_client_and_admin(
    client: AsyncClient,
    db_session: AsyncSession,
) -> tuple[dict, dict, str, PricingPackage]:
    """Helper creating Admin user, Customer user, and returning auth headers and a seeded package."""
    await seed_initial_data(db_session)

    # 1. Create Admin
    admin = User(
        email="admin.phase11@studio.dev",
        hashed_password=hash_password("AdminSecure2026!"),
        full_name="Alex Mercer",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin.phase11@studio.dev", "password": "AdminSecure2026!"},
    )
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Customer
    cust_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "customer.phase11@clientcorp.in",
            "password": "ClientSecure2026!",
            "full_name": "Rohan Deshmukh",
            "phone": "+919876543210",
        },
    )
    cust_token = cust_res.json()["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    cust_id = cust_res.json()["data"]["user"]["id"]

    # 3. Retrieve Business package
    pkg_stmt = select(PricingPackage).where(PricingPackage.slug == "business-website")
    pkg = (await db_session.execute(pkg_stmt)).scalar_one()

    return admin_headers, cust_headers, cust_id, pkg


@pytest.mark.asyncio
async def test_active_package_retrieval(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving active pricing packages via both /packages and /pricing/packages."""
    await seed_initial_data(db_session)

    # Test GET /api/v1/packages
    res1 = await client.get("/api/v1/packages")
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert len(data1) >= 4
    assert all("id" in p and len(p["id"]) > 0 for p in data1)
    assert any(p["slug"] == "business-website" for p in data1)

    # Test GET /api/v1/pricing/packages
    res2 = await client.get("/api/v1/pricing/packages")
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert len(data2) == len(data1)


@pytest.mark.asyncio
async def test_project_creation_with_valid_and_invalid_package(client: AsyncClient, db_session: AsyncSession):
    """Test creating a project with a valid package_id, and rejection of invalid package UUIDs."""
    _, cust_headers, _, pkg = await setup_client_and_admin(client, db_session)

    # 1. Success with real package_id
    success_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={
            "title": "Boutique Legal Firm Website",
            "business_name": "Deshmukh Legal Chambers",
            "package_id": pkg.id,
        },
    )
    assert success_res.status_code == 201
    proj_data = success_res.json()["data"]
    assert proj_data["package_id"] == pkg.id
    assert proj_data["package"]["name"] == "Business Website"
    assert proj_data["status"] == "NEW"

    # 2. Rejection with invalid/non-existent package_id
    fake_pkg_id = "00000000-0000-0000-0000-000000000000"
    fail_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={
            "title": "Invalid Package Attempt",
            "business_name": "Fake Co",
            "package_id": fake_pkg_id,
        },
    )
    assert fail_res.status_code == 400
    err_msg = fail_res.json().get("message") or fail_res.json().get("detail", "")
    assert "Selected package not found" in err_msg


@pytest.mark.asyncio
async def test_requirements_submission_and_payment_order(client: AsyncClient, db_session: AsyncSession):
    """Test requirements submission and server-side calculation for advance payment order."""
    _, cust_headers, _, pkg = await setup_client_and_admin(client, db_session)

    # 1. Create project
    proj_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={
            "title": "Architecture Studio Portal",
            "business_name": "Studio Forma",
            "package_id": pkg.id,
        },
    )
    project_id = proj_res.json()["data"]["id"]

    # 2. Submit requirements
    req_res = await client.post(
        f"/api/v1/projects/{project_id}/requirements/submit",
        headers=cust_headers,
        json={
            "business_summary": "Modern architectural design and spatial planning studio.",
            "target_audience": "Real estate developers and luxury homeowners.",
            "services_offered": "Architectural blueprints, 3D visualization, interior masterplanning.",
            "color_preferences": "Concrete gray, charcoal, warm travertine.",
            "reference_websites": ["https://fosterandpartners.com"],
        },
    )
    assert req_res.status_code == 200
    assert req_res.json()["data"]["is_submitted"] is True

    # Project is REQUIREMENTS_PENDING before payment
    chk = await client.get(f"/api/v1/projects/{project_id}", headers=cust_headers)
    assert chk.json()["data"]["status"] == "REQUIREMENTS_PENDING"

    # 3. Create ADVANCE payment order (50% of ₹4,999 = ₹2,499.50)
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=cust_headers,
        json={"project_id": project_id, "payment_type": "ADVANCE"},
    )
    assert order_res.status_code == 201
    order_data = order_res.json()["data"]
    assert order_data["amount_inr"] == 2499.50
    assert order_data["amount_paise"] == 249950
    assert order_data["order_id"].startswith("order_")


@pytest.mark.asyncio
async def test_payment_verification_transitions_to_pending_approval(client: AsyncClient, db_session: AsyncSession):
    """Test that verifying advance payment transitions project with submitted requirements to PENDING_APPROVAL."""
    admin_headers, cust_headers, _, pkg = await setup_client_and_admin(client, db_session)

    # 1. Create project and submit requirements
    proj_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={"title": "Solar Energy Solutions", "business_name": "Surya Power", "package_id": pkg.id},
    )
    project_id = proj_res.json()["data"]["id"]

    await client.post(
        f"/api/v1/projects/{project_id}/requirements/submit",
        headers=cust_headers,
        json={"business_summary": "Solar EPC provider for commercial and residential roofs."},
    )

    # 2. Create order
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=cust_headers,
        json={"project_id": project_id, "payment_type": "ADVANCE"},
    )
    order_data = order_res.json()["data"]
    order_id = order_data["order_id"]

    # 3. Test invalid signature rejection: project remains REQUIREMENTS_PENDING
    tampered_sig = "invalid_signature_hex_1234567890abcdef"
    fail_verify = await client.post(
        "/api/v1/payments/verify",
        headers=cust_headers,
        json={
            "project_id": project_id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_fake_tampered",
            "razorpay_signature": tampered_sig,
        },
    )
    assert fail_verify.status_code == 400

    # Ensure status did NOT become PENDING_APPROVAL
    chk_fail = await client.get(f"/api/v1/projects/{project_id}", headers=cust_headers)
    assert chk_fail.json()["data"]["status"] == "REQUIREMENTS_PENDING"

    # 4. Successful verification with authentic HMAC signature
    valid_payment_id = "pay_valid_p11_001"
    valid_sig = generate_valid_signature(order_id, valid_payment_id)

    verify_res = await client.post(
        "/api/v1/payments/verify",
        headers=cust_headers,
        json={
            "project_id": project_id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": valid_payment_id,
            "razorpay_signature": valid_sig,
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "SUCCESS"

    # 5. Project MUST now be PENDING_APPROVAL
    chk_success = await client.get(f"/api/v1/projects/{project_id}", headers=cust_headers)
    assert chk_success.json()["data"]["status"] == "PENDING_APPROVAL"

    # 6. Idempotent duplicate verification returns success safely
    dup_res = await client.post(
        "/api/v1/payments/verify",
        headers=cust_headers,
        json={
            "project_id": project_id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": valid_payment_id,
            "razorpay_signature": valid_sig,
        },
    )
    assert dup_res.status_code == 200
    assert dup_res.json()["data"]["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_admin_approval_requires_payment_or_waiver(client: AsyncClient, db_session: AsyncSession):
    """Test admin build approval: blocked without payment, succeeded with payment or explicit waiver."""
    admin_headers, cust_headers, _, pkg = await setup_client_and_admin(client, db_session)

    # Create project 1 (unpaid)
    p1_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={"title": "Unpaid Project", "business_name": "Client A", "package_id": pkg.id},
    )
    p1_id = p1_res.json()["data"]["id"]

    # 1. Customer cannot call admin approval (RBAC check)
    cust_attempt = await client.post(
        f"/api/v1/admin/projects/{p1_id}/approve-build",
        headers=cust_headers,
        json={"waive_payment": True},
    )
    assert cust_attempt.status_code == 403

    # 2. Admin approval without payment fails (400)
    admin_fail = await client.post(
        f"/api/v1/admin/projects/{p1_id}/approve-build",
        headers=admin_headers,
        json={"admin_notes": "Attempt without payment"},
    )
    assert admin_fail.status_code == 400
    assert "Advance payment must be completed" in admin_fail.json()["message"]

    # 3. Admin approval with explicit waiver succeeds (waive_payment = True)
    admin_waived = await client.post(
        f"/api/v1/admin/projects/{p1_id}/approve-build",
        headers=admin_headers,
        json={"admin_notes": "Director approved waiver", "waive_payment": True},
    )
    assert admin_waived.status_code == 200
    waived_data = admin_waived.json()["data"]
    assert waived_data["project_status"] == "BUILDING"
    assert waived_data["build"]["status"] == "QUEUED"
    assert waived_data["build"]["version_number"] == 1

    # 4. Project 2 with verified payment succeeds without waiver
    p2_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={"title": "Paid Project", "business_name": "Client B", "package_id": pkg.id},
    )
    p2_id = p2_res.json()["data"]["id"]

    # Submit requirements
    await client.post(
        f"/api/v1/projects/{p2_id}/requirements/submit",
        headers=cust_headers,
        json={"business_summary": "Full payment verification test."},
    )

    # Create order & verify
    ord2 = (await client.post(
        "/api/v1/payments/create-order",
        headers=cust_headers,
        json={"project_id": p2_id, "payment_type": "ADVANCE"},
    )).json()["data"]

    pay_id2 = "pay_p11_verified_002"
    sig2 = generate_valid_signature(ord2["order_id"], pay_id2)
    await client.post(
        "/api/v1/payments/verify",
        headers=cust_headers,
        json={
            "project_id": p2_id,
            "razorpay_order_id": ord2["order_id"],
            "razorpay_payment_id": pay_id2,
            "razorpay_signature": sig2,
        },
    )

    # Admin approves paid project without needing waiver
    admin_paid_res = await client.post(
        f"/api/v1/admin/projects/{p2_id}/approve-build",
        headers=admin_headers,
        json={"admin_notes": "Requirements and advance payment verified."},
    )
    assert admin_paid_res.status_code == 200
    assert admin_paid_res.json()["data"]["project_status"] == "BUILDING"
    assert admin_paid_res.json()["data"]["build"]["version_number"] == 1


@pytest.mark.asyncio
async def test_sandbox_signature_endpoint_and_admin_project_payment_status(
    client: AsyncClient, db_session: AsyncSession
):
    """Test the dev sandbox signature endpoint and admin project list payment badges."""
    admin_headers, cust_headers, _, pkg = await setup_client_and_admin(client, db_session)

    # Create project
    proj_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={"title": "Sandbox Test Project", "business_name": "Sandbox Co", "package_id": pkg.id},
    )
    project_id = proj_res.json()["data"]["id"]

    # Submit requirements
    await client.post(
        f"/api/v1/projects/{project_id}/requirements/submit",
        headers=cust_headers,
        json={"business_summary": "Testing development sandbox signature flow."},
    )

    # Check Admin project listing shows advance_payment_status == PENDING
    admin_proj = (await client.get(f"/api/v1/admin/projects/{project_id}", headers=admin_headers)).json()["data"]
    assert admin_proj["advance_payment_status"] == "PENDING"
    assert admin_proj["total_paid_inr"] == 0.0

    # Create order
    ord_res = await client.post(
        "/api/v1/payments/create-order",
        headers=cust_headers,
        json={"project_id": project_id, "payment_type": "ADVANCE"},
    )
    order_id = ord_res.json()["data"]["order_id"]

    # Request sandbox signature
    sig_res = await client.post(
        "/api/v1/payments/sandbox-signature",
        headers=cust_headers,
        json={"project_id": project_id, "razorpay_order_id": order_id},
    )
    assert sig_res.status_code == 200
    sig_data = sig_res.json()["data"]
    assert sig_data["razorpay_order_id"] == order_id
    assert sig_data["razorpay_payment_id"].startswith("pay_test_")
    assert len(sig_data["razorpay_signature"]) == 64

    # Verify payment using the generated sandbox signature
    verify_res = await client.post(
        "/api/v1/payments/verify",
        headers=cust_headers,
        json={
            "project_id": project_id,
            "razorpay_order_id": sig_data["razorpay_order_id"],
            "razorpay_payment_id": sig_data["razorpay_payment_id"],
            "razorpay_signature": sig_data["razorpay_signature"],
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "SUCCESS"

    # Check Admin project detail now shows advance_payment_status == PAID
    admin_proj_after = (await client.get(f"/api/v1/admin/projects/{project_id}", headers=admin_headers)).json()["data"]
    assert admin_proj_after["advance_payment_status"] == "PAID"
    assert admin_proj_after["total_paid_inr"] == 2499.50
    assert admin_proj_after["status"] == "PENDING_APPROVAL"
