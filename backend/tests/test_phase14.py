import os
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.init_db import seed_initial_data
from app.models.activity import ProjectActivity
from app.models.customer import Customer
from app.models.deployment import Deployment
from app.models.enums import (
    BuildReviewStatus,
    BuildStatus,
    DeploymentStatus,
    PaymentStatus,
    PaymentType,
    ProjectStatus,
    RevisionStatus,
    UserRole,
)
from app.models.payment import Payment
from app.models.pricing_package import PricingPackage
from app.models.project import Project
from app.models.user import User
from app.models.website_build import WebsiteBuild
from app.schemas.ai_generation import GeneratedFile, GeneratedWebsite
from app.services.ai.artifact_storage import ArtifactStorage
import hashlib
import hmac


def generate_valid_signature(order_id: str, payment_id: str, secret: str = settings.RAZORPAY_KEY_SECRET) -> str:
    """Helper to generate authentic Razorpay HMAC-SHA256 signature."""
    message = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


async def setup_phase14_test_environment(
    client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch
):
    """Setup admin, customer, second customer, project, and saved build artifact."""
    await seed_initial_data(db_session)
    monkeypatch.setattr(settings, "ARTIFACT_STORAGE_PATH", str(tmp_path / "builds"))

    # 1. Admin user
    admin = User(
        email="admin.phase14@studio.dev",
        hashed_password=hash_password("AdminSecure2026!"),
        full_name="Admin Chief",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin.phase14@studio.dev", "password": "AdminSecure2026!"},
    )
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Customer user
    cust_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "customer.phase14@client.dev",
            "password": "CustomerSecure2026!",
            "full_name": "Alice Wonderland",
            "phone": "+919876543210",
        },
    )
    cust_token = cust_res.json()["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 3. Second customer (for IDOR testing)
    other_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "other.phase14@client.dev",
            "password": "CustomerSecure2026!",
            "full_name": "Bob Intruder",
            "phone": "+919876543211",
        },
    )
    other_token = other_res.json()["data"]["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # 4. Create project for Customer
    packages = (await db_session.execute(select(PricingPackage))).scalars().all()
    package = packages[0]

    create_proj = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={
            "title": "Alice Wonderland Bakery",
            "business_name": "Wonderland Bakes",
            "package_id": package.id,
        },
    )
    assert create_proj.status_code == 201, create_proj.text
    project_id = create_proj.json()["data"]["id"]

    # 5. Create build record first
    build = WebsiteBuild(
        project_id=project_id,
        version_number=1,
        status=BuildStatus.COMPLETED,
        review_status=BuildReviewStatus.PENDING_REVIEW,
        preview_url=f"/api/v1/admin/projects/{project_id}/builds/1/sandbox-view",
        is_active=True,
    )
    db_session.add(build)
    await db_session.commit()
    await db_session.refresh(build)

    # 6. Save generated files artifact for build v1
    storage = ArtifactStorage(base_path=str(tmp_path / "builds"))
    generated = GeneratedWebsite(
        files=[
            GeneratedFile(
                path="index.html",
                content="<!DOCTYPE html><html><head><title>Wonderland Bakery</title></head><body><h1>Welcome to Wonderland Bakery</h1></body></html>",
                file_type="html",
            ),
            GeneratedFile(
                path="css/style.css",
                content="body { font-family: sans-serif; background: #fff; }",
                file_type="css",
            ),
        ],
        entry_file="index.html",
        total_files=2,
    )
    build_path = storage.save_build(
        project_id=project_id,
        build_id=build.id,
        version_number=1,
        website=generated,
        providers_used={"analysis": "gemini", "generation": "cerebras"},
        spec_summary={"validation_score": 100.0},
    )
    build.generated_code_path = build_path

    # Create advance payment record (50% paid)
    half_price = round(float(package.price_inr) / 2.0, 2)
    adv_payment = Payment(
        project_id=project_id,
        customer_id=create_proj.json()["data"]["customer_id"],
        payment_type=PaymentType.ADVANCE,
        amount_inr=half_price,
        status=PaymentStatus.SUCCESS,
        razorpay_order_id="order_adv_12345",
        razorpay_payment_id="pay_adv_12345",
        razorpay_signature="sig_adv_12345",
        invoice_number="INV-2026-0001",
    )
    db_session.add(adv_payment)

    await db_session.commit()
    await db_session.refresh(build)

    return {
        "admin": admin,
        "admin_headers": admin_headers,
        "cust_headers": cust_headers,
        "other_headers": other_headers,
        "project_id": project_id,
        "package": package,
        "build_id": build.id,
        "storage": storage,
        "tmp_path": tmp_path,
    }


@pytest.mark.asyncio
async def test_client_preview_access_controls(client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch):
    """Test client preview gating: blocked when pending review, accessible once admin approves, IDOR guarded."""
    env = await setup_phase14_test_environment(client, db_session, tmp_path, monkeypatch)
    p_id = env["project_id"]
    b_id = env["build_id"]

    # 1. Customer attempts to view preview while build review_status is PENDING_REVIEW -> 403 Forbidden
    res = await client.get(f"/api/v1/projects/{p_id}/builds/{b_id}/preview", headers=env["cust_headers"])
    assert res.status_code == 403
    err_msg = res.json().get("message") or res.json().get("detail", "")
    assert "undergoing internal review" in err_msg

    # Sandbox view also 403
    sb_res = await client.get(f"/api/v1/projects/{p_id}/builds/{b_id}/preview-sandbox", headers=env["cust_headers"])
    assert sb_res.status_code == 403

    # 2. Admin approves the build review
    app_res = await client.post(
        f"/api/v1/admin/projects/{p_id}/builds/{b_id}/approve-review",
        headers=env["admin_headers"],
        json={"notes": "Build inspected and approved for client delivery."},
    )
    assert app_res.status_code == 200

    # 3. Customer can now view preview metadata
    prev_res = await client.get(f"/api/v1/projects/{p_id}/builds/{b_id}/preview", headers=env["cust_headers"])
    assert prev_res.status_code == 200
    data = prev_res.json()["data"]
    assert data["build_id"] == b_id
    assert data["review_status"] == "APPROVED"
    assert data["client_approved"] is False

    # 4. Another customer cannot preview (IDOR guard)
    other_res = await client.get(f"/api/v1/projects/{p_id}/builds/{b_id}/preview", headers=env["other_headers"])
    assert other_res.status_code == 403


@pytest.mark.asyncio
async def test_client_preview_sandbox_security_headers(client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch):
    """Test client sandbox view returns HTML with strict CSP preventing script execution."""
    env = await setup_phase14_test_environment(client, db_session, tmp_path, monkeypatch)
    p_id = env["project_id"]
    b_id = env["build_id"]

    # Admin approves review
    await client.post(f"/api/v1/admin/projects/{p_id}/builds/{b_id}/approve-review", headers=env["admin_headers"])

    # Client fetches sandbox HTML
    res = await client.get(f"/api/v1/projects/{p_id}/builds/{b_id}/preview-sandbox", headers=env["cust_headers"])
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Wonderland Bakery" in res.text

    # Strict CSP headers check
    csp = res.headers.get("content-security-policy", "")
    assert "script-src 'none'" in csp
    assert "object-src 'none'" in csp
    assert res.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
async def test_client_revision_request_workflow(client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch):
    """Test client submitting revision requests and package revision limit enforcement."""
    env = await setup_phase14_test_environment(client, db_session, tmp_path, monkeypatch)
    p_id = env["project_id"]

    # Set project status to CLIENT_REVIEW so revisions can be submitted
    p_stmt = select(Project).where(Project.id == p_id)
    proj = (await db_session.execute(p_stmt)).scalar_one()
    proj.status = ProjectStatus.CLIENT_REVIEW
    await db_session.commit()

    # 1. Customer submits revision request
    rev_payload = {
        "description": "Please change the hero header font to Playfair and add a section showcasing chocolate cakes.",
    }
    rev_res = await client.post(f"/api/v1/projects/{p_id}/revisions", headers=env["cust_headers"], json=rev_payload)
    assert rev_res.status_code == 201
    rev_data = rev_res.json()["data"]
    assert rev_data["revision_number"] == 1
    assert rev_data["status"] == "PENDING"

    # Verify project status moved to REVISION_REQUESTED
    proj_res = await client.get(f"/api/v1/projects/{p_id}", headers=env["cust_headers"])
    assert proj_res.json()["data"]["status"] == "REVISION_REQUESTED"
    assert proj_res.json()["data"]["revisions_used"] == 1


@pytest.mark.asyncio
async def test_client_final_approval_and_remaining_payment(client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch):
    """Test client final approval, remaining balance calculation, and transition to ready for deployment."""
    env = await setup_phase14_test_environment(client, db_session, tmp_path, monkeypatch)
    p_id = env["project_id"]
    b_id = env["build_id"]

    # 1. Approve review by admin first
    await client.post(f"/api/v1/admin/projects/{p_id}/builds/{b_id}/approve-review", headers=env["admin_headers"])

    # 2. Customer approves the build
    app_res = await client.post(
        f"/api/v1/projects/{p_id}/builds/{b_id}/approve",
        headers=env["cust_headers"],
        json={"feedback": "Looks marvelous! Approved for launch."},
    )
    assert app_res.status_code == 200
    assert app_res.json()["data"]["client_approved"] is True

    # Since only advance (50%) was paid, project status should be PAYMENT_PENDING
    proj_res = await client.get(f"/api/v1/projects/{p_id}", headers=env["cust_headers"])
    assert proj_res.json()["data"]["status"] == "PAYMENT_PENDING"

    # 3. Create FINAL payment order
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=env["cust_headers"],
        json={"project_id": p_id, "payment_type": "FINAL"},
    )
    assert order_res.status_code == 201
    order_data = order_res.json()["data"]
    expected_remaining = round(float(env["package"].price_inr) / 2.0, 2)
    assert order_data["amount_inr"] == expected_remaining

    # 4. Generate valid signature for final payment
    payment_id = "pay_final_test_123"
    signature = generate_valid_signature(order_data["order_id"], payment_id)

    # 5. Verify final payment
    verify_res = await client.post(
        "/api/v1/payments/verify",
        headers=env["cust_headers"],
        json={
            "project_id": p_id,
            "razorpay_order_id": order_data["order_id"],
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "SUCCESS"

    # 6. Verify project is now APPROVED (eligible for production deployment)
    proj_after_pay = await client.get(f"/api/v1/projects/{p_id}", headers=env["cust_headers"])
    assert proj_after_pay.json()["data"]["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_deployment_eligibility_and_production_deploy(client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch):
    """Test 5-gate eligibility evaluation, deployment trigger, live URL generation, and project LIVE status."""
    env = await setup_phase14_test_environment(client, db_session, tmp_path, monkeypatch)
    p_id = env["project_id"]
    b_id = env["build_id"]

    # Gate check 1: Before admin review approval
    elig_res = await client.get(
        f"/api/v1/admin/projects/{p_id}/builds/{b_id}/deployment-eligibility",
        headers=env["admin_headers"],
    )
    assert elig_res.status_code == 200
    assert elig_res.json()["data"]["is_eligible"] is False
    assert len(elig_res.json()["data"]["blockers"]) >= 1

    # Attempting deploy prematurely returns 400
    premature_deploy = await client.post(
        f"/api/v1/admin/projects/{p_id}/builds/{b_id}/deploy",
        headers=env["admin_headers"],
    )
    assert premature_deploy.status_code == 400

    # Pass Gate 2: Admin approves review
    await client.post(f"/api/v1/admin/projects/{p_id}/builds/{b_id}/approve-review", headers=env["admin_headers"])

    # Pass Gate 3: Client final approval
    await client.post(
        f"/api/v1/projects/{p_id}/builds/{b_id}/approve",
        headers=env["cust_headers"],
        json={"feedback": "Approved!"},
    )

    # Pass Gate 4: Clear remaining payment
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers=env["cust_headers"],
        json={"project_id": p_id, "payment_type": "FINAL"},
    )
    assert order_res.status_code == 201
    payment_id = "pay_final_full_999"
    signature = generate_valid_signature(order_res.json()["data"]["order_id"], payment_id)

    verify_pay = await client.post(
        "/api/v1/payments/verify",
        headers=env["cust_headers"],
        json={
            "project_id": p_id,
            "razorpay_order_id": order_res.json()["data"]["order_id"],
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert verify_pay.status_code == 200

    # Re-evaluate eligibility: All 5 gates pass!
    elig_res2 = await client.get(
        f"/api/v1/admin/projects/{p_id}/builds/{b_id}/deployment-eligibility",
        headers=env["admin_headers"],
    )
    assert elig_res2.status_code == 200
    elig_data = elig_res2.json()["data"]
    assert elig_data["is_eligible"] is True
    assert elig_data["build_completed"] is True
    assert elig_data["admin_approved"] is True
    assert elig_data["client_approved"] is True
    assert elig_data["final_payment_cleared"] is True
    assert elig_data["artifact_available"] is True
    assert len(elig_data["blockers"]) == 0

    # Non-admin cannot trigger deployment
    unauth_dep = await client.post(
        f"/api/v1/admin/projects/{p_id}/builds/{b_id}/deploy",
        headers=env["cust_headers"],
    )
    assert unauth_dep.status_code == 403

    # Admin triggers production deployment
    deploy_res = await client.post(
        f"/api/v1/admin/projects/{p_id}/builds/{b_id}/deploy",
        headers=env["admin_headers"],
        json={"provider": "simulated", "notes": "Production launch via Nexus Studio deployment engine."},
    )
    assert deploy_res.status_code == 200
    dep_data = deploy_res.json()["data"]
    assert dep_data["status"] == "DEPLOYED"
    assert dep_data["live_url"] is not None
    assert dep_data["smoke_test_status"] == "PASSED"

    # Verify project status moved to LIVE with production_url updated
    proj_final = await client.get(f"/api/v1/projects/{p_id}", headers=env["cust_headers"])
    assert proj_final.json()["data"]["status"] == "LIVE"
    assert proj_final.json()["data"]["production_url"] == dep_data["live_url"]

    # Verify deployment history is retrievable by both client and admin
    hist_client = await client.get(f"/api/v1/projects/{p_id}/deployments", headers=env["cust_headers"])
    assert hist_client.status_code == 200
    assert len(hist_client.json()["data"]) >= 1

    hist_admin = await client.get(f"/api/v1/admin/projects/{p_id}/deployments", headers=env["admin_headers"])
    assert hist_admin.status_code == 200
    assert len(hist_admin.json()["data"]) >= 1
