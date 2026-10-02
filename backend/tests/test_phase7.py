import io
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.init_db import seed_initial_data
from app.models.enums import FileCategory, ProjectStatus, RevisionStatus, UserRole
from app.models.project import Project
from app.models.pricing_package import PricingPackage
from app.models.user import User

VALID_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00"
    b"\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


async def create_user_and_token(
    client: AsyncClient,
    email: str = "client.rev@studio.dev",
    role: UserRole = UserRole.CUSTOMER,
    db_session: AsyncSession = None,
) -> tuple[str, str]:
    """Helper to create user and return (token, user_id)."""
    if role == UserRole.CUSTOMER:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "SecurePassword123!",
                "full_name": "Test Client",
                "phone": "+919876543210",
            },
        )
        data = reg_res.json()["data"]
        return data["access_token"], data["user"]["id"]
    else:
        # Staff user created directly in DB
        staff_user = User(
            email=email,
            hashed_password=hash_password("StaffSecure123!"),
            full_name="Staff Member",
            role=role,
            is_active=True,
        )
        db_session.add(staff_user)
        await db_session.commit()
        await db_session.refresh(staff_user)

        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "StaffSecure123!"},
        )
        token = login_res.json()["data"]["access_token"]
        return token, staff_user.id


@pytest.mark.asyncio
async def test_revision_creation_blocked_before_development(client: AsyncClient, db_session: AsyncSession):
    """Test that revision requests cannot be submitted when project is in NEW or REQUIREMENTS_PENDING status."""
    token, _ = await create_user_and_token(client, "newproject.rev@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "Pending Project", "business_name": "Studio Testing"},
    )
    project_id = proj_res.json()["data"]["id"]

    # In NEW status
    rev_res = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "Please change the primary accent colors and navbar layout."},
    )
    assert rev_res.status_code == 400
    assert "Cannot request revisions before initial project requirements are submitted" in rev_res.json()["message"]


@pytest.mark.asyncio
async def test_successful_revision_creation_and_sequential_numbering(client: AsyncClient, db_session: AsyncSession):
    """Test submitting multiple revisions and verifying sequential numbering, status transition, and audit activity."""
    token, _ = await create_user_and_token(client, "sequential.client@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "E-Commerce Revisions Test", "business_name": "Trendy Wear"},
    )
    project_id = proj_res.json()["data"]["id"]

    # Move project to DEVELOPMENT directly to simulate active development phase
    stmt = select(Project).where(Project.id == project_id)
    result = await db_session.execute(stmt)
    proj = result.scalar_one()
    proj.status = ProjectStatus.DEVELOPMENT
    await db_session.commit()

    # Submit first revision
    rev1_res = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "First revision: Update the hero section banner copy and CTA styling."},
    )
    assert rev1_res.status_code == 201
    rev1_data = rev1_res.json()["data"]
    assert rev1_data["revision_number"] == 1
    assert rev1_data["status"] == "PENDING"
    assert "First revision" in rev1_data["description"]

    # Verify project status moved to REVISION_REQUESTED and revisions_used updated
    proj_check = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    p_data = proj_check.json()["data"]
    assert p_data["status"] == "REVISION_REQUESTED"
    assert p_data["revisions_used"] == 1

    # Check that audit activity timeline recorded the event
    activities = p_data["activities"]
    revision_activity = next((a for a in activities if a["action_type"] == "REVISION_REQUESTED"), None)
    assert revision_activity is not None
    assert "Revision #1 requested" in revision_activity["note"]

    # Submit second revision
    rev2_res = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "Second revision: Adjust font sizing across mobile footer navigation."},
    )
    assert rev2_res.status_code == 201
    rev2_data = rev2_res.json()["data"]
    assert rev2_data["revision_number"] == 2
    assert rev2_data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_package_revision_quota_enforcement(client: AsyncClient, db_session: AsyncSession):
    """Test that customer cannot exceed their package's included revisions quota."""
    await seed_initial_data(db_session)

    # Get Starter package (has 1 revision included)
    stmt = select(PricingPackage).where(PricingPackage.slug == "starter-website")
    res = await db_session.execute(stmt)
    starter_pkg = res.scalar_one()
    assert starter_pkg.revisions_included == 1

    token, _ = await create_user_and_token(client, "quota.client@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "title": "Starter Quota Test",
            "business_name": "Budget Shop",
            "package_id": starter_pkg.id,
        },
    )
    project_id = proj_res.json()["data"]["id"]

    # Transition to CLIENT_REVIEW
    p_stmt = select(Project).where(Project.id == project_id)
    p_obj = (await db_session.execute(p_stmt)).scalar_one()
    p_obj.status = ProjectStatus.CLIENT_REVIEW
    await db_session.commit()

    # Revision 1 should succeed
    rev1 = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "First allowed revision for the starter tier project."},
    )
    assert rev1.status_code == 201
    assert rev1.json()["data"]["revision_number"] == 1

    # Revision 2 should be rejected because quota is 1
    rev2 = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "Second revision exceeding the included quota limit."},
    )
    assert rev2.status_code == 400
    assert "Revision limit reached" in rev2.json()["message"]


@pytest.mark.asyncio
async def test_revision_with_attachment_linking(client: AsyncClient, db_session: AsyncSession):
    """Test attaching uploaded project files to a revision request."""
    token, _ = await create_user_and_token(client, "attach.client@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "Attachment Linking Test", "business_name": "Visual Lab"},
    )
    project_id = proj_res.json()["data"]["id"]

    # Upload an asset first
    upload_res = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "IMAGE"},
        files={"file": ("markup_screenshot.png", VALID_PNG, "image/png")},
    )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["data"]["id"]

    # Move project to DEVELOPMENT
    p_stmt = select(Project).where(Project.id == project_id)
    p_obj = (await db_session.execute(p_stmt)).scalar_one()
    p_obj.status = ProjectStatus.DEVELOPMENT
    await db_session.commit()

    # Create revision with attachment
    rev_res = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={
            "description": "Please see attached mockup screenshot for spacing adjustments.",
            "attachment_file_ids": [file_id],
        },
    )
    assert rev_res.status_code == 201
    rev_data = rev_res.json()["data"]
    assert len(rev_data["attachments"]) == 1
    attached_file = rev_data["attachments"][0]
    assert attached_file["id"] == file_id
    assert attached_file["original_filename"] == "markup_screenshot.png"
    assert attached_file["file_category"] == "REVISION_ATTACHMENT"


@pytest.mark.asyncio
async def test_list_and_get_revisions(client: AsyncClient, db_session: AsyncSession):
    """Test listing all revisions and retrieving single revision details."""
    token, _ = await create_user_and_token(client, "list.client@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "List Revisions Test", "business_name": "Multi Rev Corp"},
    )
    project_id = proj_res.json()["data"]["id"]

    # Move project to DEVELOPMENT
    p_stmt = select(Project).where(Project.id == project_id)
    p_obj = (await db_session.execute(p_stmt)).scalar_one()
    p_obj.status = ProjectStatus.DEVELOPMENT
    await db_session.commit()

    # Create two revisions
    r1 = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "Rev 1: Modify footer contact details and address."},
    )
    rev1_id = r1.json()["data"]["id"]

    r2 = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "Rev 2: Re-align social media icons in the header bar."},
    )
    rev2_id = r2.json()["data"]["id"]

    # List revisions
    list_res = await client.get(f"/api/v1/projects/{project_id}/revisions", headers=headers)
    assert list_res.status_code == 200
    revs = list_res.json()["data"]
    assert len(revs) == 2
    assert revs[0]["id"] == rev1_id
    assert revs[0]["revision_number"] == 1
    assert revs[1]["id"] == rev2_id
    assert revs[1]["revision_number"] == 2

    # Get single revision
    get_res = await client.get(f"/api/v1/projects/{project_id}/revisions/{rev1_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == rev1_id
    assert get_res.json()["data"]["revision_number"] == 1


@pytest.mark.asyncio
async def test_staff_update_revision_lifecycle(client: AsyncClient, db_session: AsyncSession):
    """Test staff (Developer / Admin) updating revision status and admin response."""
    # 1. Customer creates project and revision
    cust_token, _ = await create_user_and_token(client, "client.lifecycle@test.in")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=cust_headers,
        json={"title": "Lifecycle Test", "business_name": "Dev Flow Inc"},
    )
    project_id = proj_res.json()["data"]["id"]

    p_stmt = select(Project).where(Project.id == project_id)
    p_obj = (await db_session.execute(p_stmt)).scalar_one()
    p_obj.status = ProjectStatus.DEVELOPMENT
    await db_session.commit()

    rev_res = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=cust_headers,
        json={"description": "Please adjust the mobile dropdown animation speed."},
    )
    rev_id = rev_res.json()["data"]["id"]

    # 2. Developer token
    dev_token, _ = await create_user_and_token(
        client, "lead.dev@studio.dev", role=UserRole.DEVELOPER, db_session=db_session
    )
    dev_headers = {"Authorization": f"Bearer {dev_token}"}

    # Step A: Update to IN_PROGRESS
    patch1 = await client.patch(
        f"/api/v1/projects/{project_id}/revisions/{rev_id}",
        headers=dev_headers,
        json={"status": "IN_PROGRESS", "admin_response": "Currently addressing the menu timing."},
    )
    assert patch1.status_code == 200
    assert patch1.json()["data"]["status"] == "IN_PROGRESS"
    assert patch1.json()["data"]["admin_response"] == "Currently addressing the menu timing."

    # Check project returned to DEVELOPMENT
    proj_chk1 = await client.get(f"/api/v1/projects/{project_id}", headers=dev_headers)
    assert proj_chk1.json()["data"]["status"] == "DEVELOPMENT"

    # Step B: Update to COMPLETED
    patch2 = await client.patch(
        f"/api/v1/projects/{project_id}/revisions/{rev_id}",
        headers=dev_headers,
        json={"status": "COMPLETED", "admin_response": "Animation smoothed out to 250ms with ease-out curve."},
    )
    assert patch2.status_code == 200
    assert patch2.json()["data"]["status"] == "COMPLETED"
    assert patch2.json()["data"]["resolved_at"] is not None

    # Check project status moved to CLIENT_REVIEW
    proj_chk2 = await client.get(f"/api/v1/projects/{project_id}", headers=cust_headers)
    assert proj_chk2.json()["data"]["status"] == "CLIENT_REVIEW"


@pytest.mark.asyncio
async def test_customer_cannot_patch_revision(client: AsyncClient, db_session: AsyncSession):
    """Test RBAC: Customers cannot update revision status or admin response."""
    token, _ = await create_user_and_token(client, "unauth.cust@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "RBAC Test", "business_name": "Security Check"},
    )
    project_id = proj_res.json()["data"]["id"]

    p_stmt = select(Project).where(Project.id == project_id)
    p_obj = (await db_session.execute(p_stmt)).scalar_one()
    p_obj.status = ProjectStatus.DEVELOPMENT
    await db_session.commit()

    rev_res = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "Valid revision description for testing authorization."},
    )
    rev_id = rev_res.json()["data"]["id"]

    # Customer attempts to patch their own revision to COMPLETED
    patch_res = await client.patch(
        f"/api/v1/projects/{project_id}/revisions/{rev_id}",
        headers=headers,
        json={"status": "COMPLETED"},
    )
    assert patch_res.status_code == 403


@pytest.mark.asyncio
async def test_idor_protection_for_revisions(client: AsyncClient, db_session: AsyncSession):
    """Test IDOR protection: User B cannot view or request revisions on User A's project."""
    # User A
    token_a, _ = await create_user_and_token(client, "user.a@test.in")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    proj_a = await client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"title": "Client A Site", "business_name": "Enterprise A"},
    )
    proj_a_id = proj_a.json()["data"]["id"]

    # User B
    token_b, _ = await create_user_and_token(client, "user.b@test.in")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B attempts to list revisions of Project A
    res_list = await client.get(f"/api/v1/projects/{proj_a_id}/revisions", headers=headers_b)
    assert res_list.status_code == 403

    # User B attempts to create revision on Project A
    res_create = await client.post(
        f"/api/v1/projects/{proj_a_id}/revisions",
        headers=headers_b,
        json={"description": "Unauthorized attempt to request revision."},
    )
    assert res_create.status_code == 403


@pytest.mark.asyncio
async def test_revision_validation_description_length(client: AsyncClient, db_session: AsyncSession):
    """Test validation fails if description is less than 10 characters."""
    token, _ = await create_user_and_token(client, "val.client@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "Validation Test", "business_name": "Quality Check"},
    )
    project_id = proj_res.json()["data"]["id"]

    p_stmt = select(Project).where(Project.id == project_id)
    p_obj = (await db_session.execute(p_stmt)).scalar_one()
    p_obj.status = ProjectStatus.DEVELOPMENT
    await db_session.commit()

    # Description too short
    short_res = await client.post(
        f"/api/v1/projects/{project_id}/revisions",
        headers=headers,
        json={"description": "Too short"},
    )
    assert short_res.status_code == 422
