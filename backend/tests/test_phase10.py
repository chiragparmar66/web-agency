import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.init_db import seed_initial_data
from app.models.enums import (
    BuildStatus,
    FileCategory,
    PaymentStatus,
    PaymentType,
    ProjectStatus,
    RevisionStatus,
    UserRole,
)
from app.models.pricing_package import PricingPackage
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.requirement import ProjectRequirement
from app.models.revision import Revision
from app.models.payment import Payment
from app.models.user import User
from app.models.website_build import WebsiteBuild
from app.services.ai_context import build_project_ai_context


async def setup_staff_and_client(
    client: AsyncClient,
    db_session: AsyncSession,
) -> tuple[dict, dict, str]:
    """Helper creating Admin user, Customer user, and Customer project with package."""
    await seed_initial_data(db_session)

    # 1. Create Admin
    admin = User(
        email="admin.phase10@studio.dev",
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
        json={"email": "admin.phase10@studio.dev", "password": "AdminSecure2026!"},
    )
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Customer
    cust_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "customer.phase10@clientcorp.in",
            "password": "ClientSecure2026!",
            "full_name": "Vikram Patel",
            "phone": "+919876500001",
        },
    )
    cust_token = cust_res.json()["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 3. Create Project with Business package
    pkg_stmt = select(PricingPackage).where(PricingPackage.slug == "business-website")
    pkg = (await db_session.execute(pkg_stmt)).scalar_one()

    proj_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={
            "title": "FinTech Analytics Suite",
            "business_name": "Patel Wealth Technologies",
            "package_id": pkg.id,
        },
    )
    project_id = proj_res.json()["data"]["id"]

    return admin_headers, cust_headers, project_id


@pytest.mark.asyncio
async def test_ai_context_service_aggregation(client: AsyncClient, db_session: AsyncSession):
    """Test backend AI context service aggregates requirements, files, package and revision."""
    admin_headers, cust_headers, project_id = await setup_staff_and_client(client, db_session)

    # 1. Submit requirements
    req_res = await client.put(
        f"/api/v1/projects/{project_id}/requirements",
        headers=cust_headers,
        json={
            "business_summary": "AI-powered wealth management and investment analysis SaaS.",
            "target_audience": "HNIs and modern retail investors.",
            "services_offered": "Portfolio rebalancing, tax optimization, algorithmic alerts.",
            "color_preferences": "Emerald Green, Obsidian, Brushed Gold",
            "reference_websites": ["https://stripe.com", "https://linear.app"],
            "social_links": {"linkedin": "https://linkedin.com/company/patelwealth"},
            "special_requests": "Include interactive performance charts and dark mode.",
        },
    )
    assert req_res.status_code == 200

    # 2. Add a mock project file (Logo)
    cust_stmt = select(User).where(User.email == "customer.phase10@clientcorp.in")
    cust_user = (await db_session.execute(cust_stmt)).scalar_one()

    logo_file = ProjectFile(
        project_id=project_id,
        file_category=FileCategory.LOGO,
        original_filename="patel_wealth_logo.svg",
        stored_filename="stored_logo_123.svg",
        file_path="/uploads/projects/patel_wealth_logo.svg",
        mime_type="image/svg+xml",
        file_size_bytes=24500,
        uploaded_by_user_id=cust_user.id,
    )
    db_session.add(logo_file)
    await db_session.commit()

    # 3. Call AI Context Service directly
    context = await build_project_ai_context(project_id, db_session)

    assert context["project_id"] == project_id
    assert context["title"] == "FinTech Analytics Suite"
    assert context["client_name"] == "Vikram Patel"
    assert context["client_email"] == "customer.phase10@clientcorp.in"
    assert context["package"]["name"] == "Business Website"
    assert context["requirements"]["business_summary"].startswith("AI-powered wealth")
    assert "Emerald Green" in context["requirements"]["color_preferences"]
    assert len(context["files"]) == 1
    assert context["files"][0]["original_filename"] == "patel_wealth_logo.svg"
    assert context["context_summary"]["has_logo"] is True
    assert "Home" in context["context_summary"]["suggested_pages"]
    assert context["ready_for_build"] is True


@pytest.mark.asyncio
async def test_admin_approve_build_requires_staff_role(client: AsyncClient, db_session: AsyncSession):
    """Test RBAC: Customer is rejected (403) from approving and queuing AI builds."""
    _, cust_headers, project_id = await setup_staff_and_client(client, db_session)

    res = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        headers=cust_headers,
        json={"admin_notes": "Attempt by customer"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_approve_build_advance_payment_check_and_override(client: AsyncClient, db_session: AsyncSession):
    """Test that advance payment is required unless explicitly overridden by admin."""
    admin_headers, _, project_id = await setup_staff_and_client(client, db_session)

    # 1. Attempt to approve build without advance payment -> 400 Bad Request
    res_fail = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        headers=admin_headers,
        json={"admin_notes": "Approve without payment"},
    )
    assert res_fail.status_code == 400
    err_body = res_fail.json()
    err_msg = err_body.get("message") or err_body.get("detail", "")
    assert "Advance payment must be completed" in err_msg

    # 2. Attempt with force_override_payment -> 200 OK
    res_override = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        headers=admin_headers,
        json={"admin_notes": "Approved via administrative waiver", "force_override_payment": True},
    )
    assert res_override.status_code == 200
    data = res_override.json()["data"]
    assert data["success"] is True
    assert data["project_status"] == "BUILDING"
    assert data["build"]["version_number"] == 1
    assert data["build"]["status"] == "QUEUED"
    assert data["build"]["is_active"] is True
    assert data["build"]["admin_notes"] == "Approved via administrative waiver"


@pytest.mark.asyncio
async def test_admin_approve_build_with_verified_payment(client: AsyncClient, db_session: AsyncSession):
    """Test approving build when advance payment is properly completed."""
    admin_headers, cust_headers, project_id = await setup_staff_and_client(client, db_session)

    # Fetch customer record to attach payment
    p_stmt = select(Project).where(Project.id == project_id)
    proj = (await db_session.execute(p_stmt)).scalar_one()

    # Record verified advance payment
    pay = Payment(
        project_id=project_id,
        customer_id=proj.customer_id,
        payment_type=PaymentType.ADVANCE,
        amount_inr=2499.50,
        status=PaymentStatus.SUCCESS,
        razorpay_order_id="order_test_phase10_adv",
        razorpay_payment_id="pay_test_phase10_adv",
        invoice_number="INV-2026-P10-001",
    )
    db_session.add(pay)
    await db_session.commit()

    # Admin approves build
    res = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        headers=admin_headers,
        json={"admin_notes": "Requirements and advance payment verified. Ready for AI synthesis."},
    )
    assert res.status_code == 200
    build_data = res.json()["data"]["build"]
    assert build_data["version_number"] == 1
    assert build_data["status"] == "QUEUED"

    # Verify project status in database and audit log
    proj_chk = await client.get(f"/api/v1/projects/{project_id}", headers=cust_headers)
    p_info = proj_chk.json()["data"]
    assert p_info["status"] == "BUILDING"
    activities = p_info["activities"]
    assert any(a["action_type"] == "BUILD_APPROVED" for a in activities)


@pytest.mark.asyncio
async def test_version_increment_and_build_listing(client: AsyncClient, db_session: AsyncSession):
    """Test that multiple builds increment version number and list correctly."""
    admin_headers, _, project_id = await setup_staff_and_client(client, db_session)

    # First build
    res1 = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        headers=admin_headers,
        json={"admin_notes": "Build Version 1", "force_override_payment": True},
    )
    assert res1.status_code == 200
    assert res1.json()["data"]["build"]["version_number"] == 1

    # Second build (e.g., following revision or iteration)
    res2 = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        headers=admin_headers,
        json={"admin_notes": "Build Version 2 iteration", "force_override_payment": True},
    )
    assert res2.status_code == 200
    assert res2.json()["data"]["build"]["version_number"] == 2
    assert res2.json()["data"]["build"]["is_active"] is True

    # List builds via admin endpoint
    list_res = await client.get(f"/api/v1/admin/projects/{project_id}/builds", headers=admin_headers)
    assert list_res.status_code == 200
    builds = list_res.json()["data"]
    assert len(builds) == 2
    # Verify ordered descending by version_number
    assert builds[0]["version_number"] == 2
    assert builds[0]["is_active"] is True
    assert builds[1]["version_number"] == 1
    assert builds[1]["is_active"] is False


@pytest.mark.asyncio
async def test_get_project_ai_context_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test admin endpoint GET /api/v1/admin/projects/{project_id}/ai-context."""
    admin_headers, _, project_id = await setup_staff_and_client(client, db_session)

    res = await client.get(f"/api/v1/admin/projects/{project_id}/ai-context", headers=admin_headers)
    assert res.status_code == 200
    context = res.json()["data"]
    assert context["project_id"] == project_id
    assert context["client_name"] == "Vikram Patel"
    assert context["package"]["name"] == "Business Website"
    assert "context_summary" in context
