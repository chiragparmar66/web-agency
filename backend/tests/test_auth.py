import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


@pytest.mark.asyncio
async def test_register_customer_success(client: AsyncClient, db_session: AsyncSession):
    """Test successful customer registration with automatic customer profile creation."""
    payload = {
        "email": "sarah.client@example.com",
        "password": "SecurePassword123!",
        "full_name": "Sarah Designer",
        "phone": "+919876543210",
        "company_name": "Sarah Creative Studio",
        "business_type": "Design Agency",
        "city": "Mumbai",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["email"] == "sarah.client@example.com"
    assert data["data"]["user"]["role"] == "CUSTOMER"

    # Verify user and customer profile persisted in database
    from sqlalchemy.orm import selectinload
    stmt = select(User).options(selectinload(User.customer_profile)).where(User.email == "sarah.client@example.com")
    res = await db_session.execute(stmt)
    user = res.scalar_one_or_none()
    assert user is not None
    assert user.role == UserRole.CUSTOMER
    assert user.hashed_password != payload["password"]
    assert user.customer_profile is not None
    assert user.customer_profile.company_name == "Sarah Creative Studio"


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient):
    """Test registration with already registered email fails."""
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123!",
        "full_name": "First User",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    err_data = res2.json()
    assert err_data["code"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test login with valid credentials returns tokens."""
    reg_payload = {
        "email": "login.test@example.com",
        "password": "LoginSecret456!",
        "full_name": "Login Tester",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "login.test@example.com",
        "password": "LoginSecret456!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "login.test@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with wrong password fails."""
    reg_payload = {
        "email": "wrong.pass@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Tester",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrong.pass@example.com",
        "password": "IncorrectPassword999!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_unauthorized_access_protected_endpoint(client: AsyncClient):
    """Test accessing protected /me without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_customer_cannot_access_admin_endpoint(client: AsyncClient):
    """Test RBAC boundary: CUSTOMER role attempting to access admin route receives 403 Forbidden."""
    reg_payload = {
        "email": "regular.client@example.com",
        "password": "RegularPassword123!",
        "full_name": "Regular Client",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/admin/overview", headers=headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["message"]


@pytest.mark.asyncio
async def test_admin_can_access_admin_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test server-side RBAC: ADMIN role successfully accesses admin endpoint."""
    admin_user = User(
        email="studio.director@nexusstudio.dev",
        hashed_password=hash_password("DirectorSuperPass2026!"),
        full_name="Studio Director",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.commit()

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "studio.director@nexusstudio.dev", "password": "DirectorSuperPass2026!"},
    )
    admin_token = login_res.json()["data"]["access_token"]

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/v1/admin/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["admin_email"] == "studio.director@nexusstudio.dev"


@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient):
    """Test refreshing tokens using valid refresh_token."""
    reg_payload = {
        "email": "refresh.test@example.com",
        "password": "RefreshPass123!",
        "full_name": "Refresh Tester",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    refresh_token = reg_res.json()["data"]["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_get_and_update_profile(client: AsyncClient):
    """Test retrieving and updating customer profile."""
    reg_payload = {
        "email": "profile.update@example.com",
        "password": "ProfilePass123!",
        "full_name": "Old Name",
        "phone": "+919999999999",
        "company_name": "Old Company",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch profile
    get_res = await client.get("/api/v1/auth/me", headers=headers)
    assert get_res.status_code == 200
    profile_data = get_res.json()["data"]
    assert profile_data["full_name"] == "Old Name"
    assert profile_data["customer_profile"]["company_name"] == "Old Company"

    # Update profile
    update_payload = {
        "user_update": {"full_name": "New Modern Name", "phone": "+918888888888"},
        "customer_update": {"company_name": "New Modern Company", "city": "Bengaluru"},
    }
    put_res = await client.put("/api/v1/auth/me", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    updated_data = put_res.json()["data"]
    assert updated_data["full_name"] == "New Modern Name"
    assert updated_data["phone"] == "+918888888888"
    assert updated_data["customer_profile"]["company_name"] == "New Modern Company"
    assert updated_data["customer_profile"]["city"] == "Bengaluru"
