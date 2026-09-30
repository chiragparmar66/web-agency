import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.init_db import seed_initial_data


@pytest.mark.asyncio
async def test_submit_inquiry(client: AsyncClient):
    """Test public contact/inquiry submission."""
    payload = {
        "name": "Rajesh Kumar",
        "email": "rajesh@delhienterprises.in",
        "phone": "+919811223344",
        "business_name": "Delhi Industrial Supplies",
        "business_type": "Manufacturing",
        "city": "New Delhi",
        "source": "CONTACT_FORM",
        "message": "We need a new professional multi-page company website with a product catalog.",
    }
    response = await client.post("/api/v1/inquiries", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Rajesh Kumar"
    assert data["data"]["status"] == "NEW"


@pytest.mark.asyncio
async def test_get_services(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving public studio services."""
    await seed_initial_data(db_session)

    response = await client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 6
    assert any(s["slug"] == "business-websites" for s in data["data"])


@pytest.mark.asyncio
async def test_get_portfolio_empty_state(client: AsyncClient):
    """Test portfolio returns clean empty list when no projects are published."""
    response = await client.get("/api/v1/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_create_and_list_customer_projects(client: AsyncClient):
    """Test customer creating a project and viewing their dashboard projects."""
    # Register customer
    reg_payload = {
        "email": "amit.patel@gujarattextiles.com",
        "password": "PatelSecure2026!",
        "full_name": "Amit Patel",
        "phone": "+919822334455",
        "company_name": "Gujarat Textiles",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_payload = {
        "title": "Gujarat Textiles Corporate Portal",
        "business_name": "Gujarat Textiles Pvt Ltd",
    }
    create_res = await client.post("/api/v1/projects", json=proj_payload, headers=headers)
    assert create_res.status_code == 201
    proj_data = create_res.json()["data"]
    assert proj_data["title"] == "Gujarat Textiles Corporate Portal"
    assert proj_data["status"] == "NEW"
    assert proj_data["project_number"].startswith("PRJ-2026-")

    project_id = proj_data["id"]

    # List projects
    list_res = await client.get("/api/v1/projects", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert len(list_data) == 1
    assert list_data[0]["id"] == project_id

    # Get single project detail
    detail_res = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["id"] == project_id
    assert len(detail_data["activities"]) >= 1
    assert detail_data["activities"][0]["action_type"] == "PROJECT_CREATED"


@pytest.mark.asyncio
async def test_project_ownership_isolation(client: AsyncClient):
    """Test strict security: Customer B CANNOT access Customer A's project."""
    # Customer A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "client.a@example.com",
            "password": "ClientAPassword1!",
            "full_name": "Client A",
        },
    )
    token_a = res_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Customer A creates project
    proj_a = await client.post(
        "/api/v1/projects",
        json={"title": "Client A Website", "business_name": "Brand A"},
        headers=headers_a,
    )
    project_a_id = proj_a.json()["data"]["id"]

    # Customer B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "client.b@example.com",
            "password": "ClientBPassword1!",
            "full_name": "Client B",
        },
    )
    token_b = res_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Customer B tries to view Customer A's project -> MUST BE FORBIDDEN (403)
    attack_res = await client.get(f"/api/v1/projects/{project_a_id}", headers=headers_b)
    assert attack_res.status_code == 403


@pytest.mark.asyncio
async def test_customer_dashboard_summary(client: AsyncClient):
    """Test dashboard summary endpoint returns real project count and status."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "priya.sharma@creative.in",
            "password": "PriyaPassword2026!",
            "full_name": "Priya Sharma",
        },
    )
    token = res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Empty state summary
    sum_empty = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert sum_empty.status_code == 200
    assert sum_empty.json()["data"]["total_projects"] == 0
    assert sum_empty.json()["data"]["active_project"] is None

    # After creating project
    await client.post(
        "/api/v1/projects",
        json={"title": "Priya Portfolio Site", "business_name": "Priya Studios"},
        headers=headers,
    )

    sum_active = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert sum_active.status_code == 200
    data = sum_active.json()["data"]
    assert data["total_projects"] == 1
    assert data["active_project"]["title"] == "Priya Portfolio Site"
    assert len(data["recent_activities"]) >= 1


@pytest.mark.asyncio
async def test_customer_change_password(client: AsyncClient):
    """Test password change endpoint."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "change.pwd@example.com",
            "password": "OldPassword123!",
            "full_name": "Pwd User",
        },
    )
    token = res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    change_res = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "OldPassword123!", "new_password": "BrandNewPassword2026!"},
        headers=headers,
    )
    assert change_res.status_code == 200

    # Old password fails
    fail_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "change.pwd@example.com", "password": "OldPassword123!"},
    )
    assert fail_res.status_code == 400

    # New password succeeds
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "change.pwd@example.com", "password": "BrandNewPassword2026!"},
    )
    assert login_res.status_code == 200
