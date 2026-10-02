import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.init_db import seed_initial_data
from app.models.enums import InquirySource, InquiryStatus, ProjectStatus, UserRole
from app.models.inquiry import Inquiry
from app.models.project import Project
from app.models.user import User


async def create_staff_user(
    email: str,
    role: UserRole,
    full_name: str,
    db_session: AsyncSession,
    client: AsyncClient,
) -> tuple[str, str]:
    """Helper to create an active staff member and return (token, user_id)."""
    staff = User(
        email=email,
        hashed_password=hash_password("StaffPass2026!"),
        full_name=full_name,
        role=role,
        is_active=True,
    )
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StaffPass2026!"},
    )
    token = login_res.json()["data"]["access_token"]
    return token, staff.id


async def create_customer_and_project(
    client: AsyncClient,
    email: str = "customer.phase8@test.in",
    title: str = "Corporate Identity Portal",
) -> tuple[str, str, str]:
    """Helper to register customer and create a project. Returns (token, user_id, project_id)."""
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "CustomerSecure2026!",
            "full_name": "Client User",
            "phone": "+919876543210",
        },
    )
    data = reg_res.json()["data"]
    token = data["access_token"]
    user_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": title, "business_name": "Acme Innovations"},
    )
    project_id = proj_res.json()["data"]["id"]
    return token, user_id, project_id


@pytest.mark.asyncio
async def test_admin_system_overview(client: AsyncClient, db_session: AsyncSession):
    """Test admin overview counts and role-based restrictions."""
    admin_token, _ = await create_staff_user(
        "admin.overview@studio.dev", UserRole.ADMIN, "Lead Admin", db_session, client
    )
    cust_token, _, _ = await create_customer_and_project(client, "cust.overview@test.in")

    # Admin access
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_res = await client.get("/api/v1/admin/overview", headers=admin_headers)
    assert admin_res.status_code == 200
    data = admin_res.json()["data"]
    assert data["admin_email"] == "admin.overview@studio.dev"
    assert data["total_users"] >= 2
    assert data["total_projects"] >= 1
    assert data["system_status"] == "operational"

    # Customer access denied
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    cust_res = await client.get("/api/v1/admin/overview", headers=cust_headers)
    assert cust_res.status_code == 403


@pytest.mark.asyncio
async def test_list_admin_projects_and_filtering(client: AsyncClient, db_session: AsyncSession):
    """Test staff listing all client projects and applying query filters."""
    dev_token, dev_id = await create_staff_user(
        "senior.dev@studio.dev", UserRole.DEVELOPER, "Senior Dev", db_session, client
    )
    dev_headers = {"Authorization": f"Bearer {dev_token}"}

    # Create two customer projects
    _, _, proj1_id = await create_customer_and_project(client, "client.one@test.in", "Project One")
    _, _, proj2_id = await create_customer_and_project(client, "client.two@test.in", "Project Two")

    # Move proj1 to IN_PROGRESS and assign to developer
    stmt = select(Project).where(Project.id == proj1_id)
    p1 = (await db_session.execute(stmt)).scalar_one()
    p1.status = ProjectStatus.IN_PROGRESS
    p1.assigned_developer_id = dev_id
    await db_session.commit()

    # Staff lists all projects
    all_res = await client.get("/api/v1/admin/projects", headers=dev_headers)
    assert all_res.status_code == 200
    all_projs = all_res.json()["data"]
    assert len(all_projs) >= 2
    ids = [p["id"] for p in all_projs]
    assert proj1_id in ids
    assert proj2_id in ids

    # Filter by status = IN_PROGRESS
    filtered_res = await client.get(
        "/api/v1/admin/projects?status=IN_PROGRESS", headers=dev_headers
    )
    assert filtered_res.status_code == 200
    filtered_data = filtered_res.json()["data"]
    assert all(p["status"] == "IN_PROGRESS" for p in filtered_data)
    assert any(p["id"] == proj1_id for p in filtered_data)

    # Filter by assigned developer
    dev_filter_res = await client.get(
        f"/api/v1/admin/projects?assigned_developer_id={dev_id}", headers=dev_headers
    )
    assert dev_filter_res.status_code == 200
    dev_filter_data = dev_filter_res.json()["data"]
    assert len(dev_filter_data) >= 1
    assert dev_filter_data[0]["assigned_developer_id"] == dev_id


@pytest.mark.asyncio
async def test_admin_update_project_lifecycle_and_audit(client: AsyncClient, db_session: AsyncSession):
    """Test updating project status from studio console and logging audit activity."""
    admin_token, _ = await create_staff_user(
        "director@studio.dev", UserRole.ADMIN, "Studio Director", db_session, client
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    cust_token, _, proj_id = await create_customer_and_project(
        client, "lifecycle.client@test.in", "Lifecycle Site"
    )

    # Update status to DEVELOPMENT
    patch_res = await client.patch(
        f"/api/v1/admin/projects/{proj_id}",
        headers=admin_headers,
        json={"status": "DEVELOPMENT"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "DEVELOPMENT"

    # Customer verifies updated status and activity log
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    proj_chk = await client.get(f"/api/v1/projects/{proj_id}", headers=cust_headers)
    p_data = proj_chk.json()["data"]
    assert p_data["status"] == "DEVELOPMENT"
    status_act = next((a for a in p_data["activities"] if a["action_type"] == "STATUS_CHANGED"), None)
    assert status_act is not None
    assert "DEVELOPMENT" in status_act["new_status"]


@pytest.mark.asyncio
async def test_admin_assign_developer_and_validation(client: AsyncClient, db_session: AsyncSession):
    """Test assigning a developer to a project and preventing invalid assignments."""
    admin_token, _ = await create_staff_user(
        "admin.assign@studio.dev", UserRole.ADMIN, "Admin Assign", db_session, client
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    _, dev_id = await create_staff_user(
        "coder.lead@studio.dev", UserRole.DEVELOPER, "Coder Lead", db_session, client
    )
    _, cust_id, proj_id = await create_customer_and_project(client, "assign.cust@test.in")

    # Assign valid developer
    assign_res = await client.patch(
        f"/api/v1/admin/projects/{proj_id}",
        headers=admin_headers,
        json={"assigned_developer_id": dev_id},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["data"]["assigned_developer_id"] == dev_id
    assert assign_res.json()["data"]["assigned_developer"]["full_name"] == "Coder Lead"

    # Attempt to assign a customer role user as developer (should fail 400)
    invalid_assign = await client.patch(
        f"/api/v1/admin/projects/{proj_id}",
        headers=admin_headers,
        json={"assigned_developer_id": cust_id},
    )
    assert invalid_assign.status_code == 400
    err_body = invalid_assign.json()
    err_text = err_body.get("message") or err_body.get("detail", "")
    assert "must be an active Developer or Admin" in err_text


@pytest.mark.asyncio
async def test_admin_update_staging_and_production_urls(client: AsyncClient, db_session: AsyncSession):
    """Test configuring preview URL, production URL, and custom domain."""
    dev_token, _ = await create_staff_user(
        "dev.urls@studio.dev", UserRole.DEVELOPER, "URL Dev", db_session, client
    )
    dev_headers = {"Authorization": f"Bearer {dev_token}"}

    _, _, proj_id = await create_customer_and_project(client, "urls.cust@test.in")

    update_res = await client.patch(
        f"/api/v1/admin/projects/{proj_id}",
        headers=dev_headers,
        json={
            "preview_url": "https://staging.acme-innovations.preview.nexusstudio.dev",
            "production_url": "https://acme-innovations.com",
            "custom_domain": "acme-innovations.com",
        },
    )
    assert update_res.status_code == 200
    data = update_res.json()["data"]
    assert data["preview_url"] == "https://staging.acme-innovations.preview.nexusstudio.dev"
    assert data["production_url"] == "https://acme-innovations.com"
    assert data["custom_domain"] == "acme-innovations.com"


@pytest.mark.asyncio
async def test_admin_inquiries_crm_management(client: AsyncClient, db_session: AsyncSession):
    """Test listing leads/inquiries and updating inquiry status."""
    admin_token, _ = await create_staff_user(
        "admin.crm@studio.dev", UserRole.ADMIN, "CRM Manager", db_session, client
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create public inquiry
    inq_res = await client.post(
        "/api/v1/inquiries",
        json={
            "name": "Pooja Hegde",
            "email": "pooja.hegde@luxurycraft.in",
            "phone": "+919833445566",
            "business_name": "Luxury Craft Interiors",
            "message": "Interested in a bespoke showcase website with interactive portfolio.",
        },
    )
    assert inq_res.status_code == 201
    inquiry_id = inq_res.json()["data"]["id"]

    # Staff lists inquiries
    list_res = await client.get("/api/v1/admin/inquiries", headers=admin_headers)
    assert list_res.status_code == 200
    inquiries = list_res.json()["data"]
    assert any(i["id"] == inquiry_id for i in inquiries)

    # Staff updates inquiry status to QUALIFIED
    patch_inq = await client.patch(
        f"/api/v1/admin/inquiries/{inquiry_id}",
        headers=admin_headers,
        json={"status": "QUALIFIED"},
    )
    assert patch_inq.status_code == 200
    assert patch_inq.json()["data"]["status"] == "QUALIFIED"


@pytest.mark.asyncio
async def test_list_team_members(client: AsyncClient, db_session: AsyncSession):
    """Test listing staff team members excluding customers."""
    dev_token, _ = await create_staff_user(
        "team.dev@studio.dev", UserRole.DEVELOPER, "Team Dev", db_session, client
    )
    dev_headers = {"Authorization": f"Bearer {dev_token}"}

    # Register customer
    await create_customer_and_project(client, "regular.cust@test.in")

    team_res = await client.get("/api/v1/admin/team", headers=dev_headers)
    assert team_res.status_code == 200
    team = team_res.json()["data"]
    assert len(team) >= 1
    assert all(m["role"] in ["ADMIN", "DEVELOPER"] for m in team)
    assert not any(m["role"] == "CUSTOMER" for m in team)


@pytest.mark.asyncio
async def test_internal_developer_notes_security(client: AsyncClient, db_session: AsyncSession):
    """Test that internal notes posted by staff are hidden from customers but visible to staff."""
    dev_token, _ = await create_staff_user(
        "lead.coder@studio.dev", UserRole.DEVELOPER, "Lead Coder", db_session, client
    )
    dev_headers = {"Authorization": f"Bearer {dev_token}"}

    cust_token, _, proj_id = await create_customer_and_project(client, "msg.cust@test.in")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 1. Developer posts internal note
    dev_msg_res = await client.post(
        f"/api/v1/projects/{proj_id}/messages",
        headers=dev_headers,
        json={
            "message": "INTERNAL NOTE: Need to verify responsive layout breakpoint on mobile header.",
            "is_internal_note": True,
        },
    )
    assert dev_msg_res.status_code == 201
    assert dev_msg_res.json()["data"]["is_internal_note"] is True
    assert dev_msg_res.json()["data"]["sender_role"] == "DEVELOPER"

    # 2. Developer posts public client-facing message
    dev_public_res = await client.post(
        f"/api/v1/projects/{proj_id}/messages",
        headers=dev_headers,
        json={
            "message": "Hello! We have started building your homepage layout.",
            "is_internal_note": False,
        },
    )
    assert dev_public_res.status_code == 201
    assert dev_public_res.json()["data"]["is_internal_note"] is False

    # 3. Staff lists messages -> sees BOTH public message and internal note
    staff_list = await client.get(f"/api/v1/projects/{proj_id}/messages", headers=dev_headers)
    assert staff_list.status_code == 200
    staff_msgs = staff_list.json()["data"]
    assert len(staff_msgs) == 2
    assert any(m["is_internal_note"] is True for m in staff_msgs)

    # 4. Customer lists messages -> sees ONLY public message, internal note is strictly hidden!
    cust_list = await client.get(f"/api/v1/projects/{proj_id}/messages", headers=cust_headers)
    assert cust_list.status_code == 200
    cust_msgs = cust_list.json()["data"]
    assert len(cust_msgs) == 1
    assert cust_msgs[0]["is_internal_note"] is False
    assert "INTERNAL NOTE" not in cust_msgs[0]["message"]

    # 5. Customer attempts to post internal note -> backend forces is_internal_note=False
    cust_post = await client.post(
        f"/api/v1/projects/{proj_id}/messages",
        headers=cust_headers,
        json={
            "message": "Customer attempt to create internal note",
            "is_internal_note": True,
        },
    )
    assert cust_post.status_code == 201
    assert cust_post.json()["data"]["is_internal_note"] is False
