import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.init_db import seed_initial_data


@pytest.mark.asyncio
async def test_get_pricing_packages(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving public pricing packages."""
    await seed_initial_data(db_session)

    response = await client.get("/api/v1/pricing/packages")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 4
    slugs = [p["slug"] for p in data["data"]]
    assert "starter-website" in slugs
    assert "business-website" in slugs
    assert "professional-website" in slugs
    assert "custom-solution" in slugs


@pytest.mark.asyncio
async def test_project_requirements_flow(client: AsyncClient):
    """Test full requirements flow: get blank, save draft, submit, verify locked."""
    # 1. Register customer
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sunita.verma@delhiclinic.com",
            "password": "VermaPassword2026!",
            "full_name": "Dr. Sunita Verma",
            "phone": "+919876543210",
        },
    )
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create project
    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "title": "Verma Dental Clinic Website",
            "business_name": "Verma Dental Care",
        },
    )
    project_id = proj_res.json()["data"]["id"]

    # 3. Get initial blank requirements
    req_res = await client.get(
        f"/api/v1/projects/{project_id}/requirements",
        headers=headers,
    )
    assert req_res.status_code == 200
    req_data = req_res.json()["data"]
    assert req_data["is_submitted"] is False
    assert req_data["business_summary"] is None

    # 4. Save draft
    draft_res = await client.put(
        f"/api/v1/projects/{project_id}/requirements",
        headers=headers,
        json={
            "business_summary": "Comprehensive dental clinic offering preventive and cosmetic dentistry.",
            "target_audience": "Families, professionals, and seniors in South Delhi.",
            "services_offered": "Dental implants, teeth whitening, root canal, orthodontics.",
            "color_preferences": "Teal and clean medical white.",
            "reference_websites": ["https://clove-dental.example.com"],
            "contact_email": "appointments@vermadental.com",
            "contact_phone": "+919876543210",
        },
    )
    assert draft_res.status_code == 200
    assert draft_res.json()["data"]["is_submitted"] is False
    assert "dental" in draft_res.json()["data"]["business_summary"].lower()

    # 5. Submit requirements (final)
    submit_res = await client.post(
        f"/api/v1/projects/{project_id}/requirements/submit",
        headers=headers,
        json={
            "business_summary": "Comprehensive dental clinic offering preventive and cosmetic dentistry in Delhi.",
            "special_requests": "Include online appointment booking widget.",
        },
    )
    assert submit_res.status_code == 200
    sub_data = submit_res.json()["data"]
    assert sub_data["is_submitted"] is True
    assert sub_data["submitted_at"] is not None

    # 6. Verify project status was moved to REQUIREMENTS_PENDING
    proj_check = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=headers,
    )
    assert proj_check.json()["data"]["status"] == "REQUIREMENTS_PENDING"

    # 7. Attempting to edit after submit returns 409 Conflict
    conflict_res = await client.put(
        f"/api/v1/projects/{project_id}/requirements",
        headers=headers,
        json={"business_summary": "Trying to modify after submission."},
    )
    assert conflict_res.status_code == 409

    # 8. Attempting to submit again returns 409 Conflict
    conflict_sub_res = await client.post(
        f"/api/v1/projects/{project_id}/requirements/submit",
        headers=headers,
        json={"business_summary": "Trying to submit again."},
    )
    assert conflict_sub_res.status_code == 409


@pytest.mark.asyncio
async def test_requirements_idor_protection(client: AsyncClient):
    """Test that customer B cannot access or update customer A's requirements."""
    # Customer A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cust.a@test.com",
            "password": "Password123!",
            "full_name": "Customer A",
            "phone": "+919999900001",
        },
    )
    token_a = res_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"title": "Project A", "business_name": "Company A"},
    )
    project_id = proj_res.json()["data"]["id"]

    # Customer B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cust.b@test.com",
            "password": "Password123!",
            "full_name": "Customer B",
            "phone": "+919999900002",
        },
    )
    token_b = res_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Customer B tries to GET Customer A's requirements -> 403 Forbidden
    get_res = await client.get(
        f"/api/v1/projects/{project_id}/requirements",
        headers=headers_b,
    )
    assert get_res.status_code == 403

    # Customer B tries to PUT Customer A's requirements -> 403 Forbidden
    put_res = await client.put(
        f"/api/v1/projects/{project_id}/requirements",
        headers=headers_b,
        json={"business_summary": "Malicious edit attempt"},
    )
    assert put_res.status_code == 403


@pytest.mark.asyncio
async def test_project_messages_and_idor(client: AsyncClient):
    """Test sending and reading messages with customer boundary enforcement."""
    # Customer A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rahul.sharma@techcorp.in",
            "password": "RahulPassword2026!",
            "full_name": "Rahul Sharma",
            "phone": "+919111222333",
        },
    )
    token_a = res_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"title": "Sharma Tech Portal", "business_name": "Sharma Tech"},
    )
    project_id = proj_res.json()["data"]["id"]

    # Send message as Customer A
    send_res = await client.post(
        f"/api/v1/projects/{project_id}/messages",
        headers=headers_a,
        json={"message": "Hello, we have uploaded our logo and brand assets."},
    )
    assert send_res.status_code == 201
    assert send_res.json()["data"]["message"] == "Hello, we have uploaded our logo and brand assets."
    assert send_res.json()["data"]["is_internal_note"] is False

    # List messages as Customer A
    list_res = await client.get(
        f"/api/v1/projects/{project_id}/messages",
        headers=headers_a,
    )
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 1

    # Customer B attempts to view or post on Customer A's project -> 403 Forbidden
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder@evil.com",
            "password": "Password123!",
            "full_name": "Intruder User",
            "phone": "+919888777666",
        },
    )
    token_b = res_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    get_res = await client.get(
        f"/api/v1/projects/{project_id}/messages",
        headers=headers_b,
    )
    assert get_res.status_code == 403

    post_res = await client.post(
        f"/api/v1/projects/{project_id}/messages",
        headers=headers_b,
        json={"message": "Unauthorized message attempt"},
    )
    assert post_res.status_code == 403
