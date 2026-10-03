import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.enums import InquirySource, InquiryStatus, UserRole
from app.models.inquiry import Inquiry
from app.models.user import User
from app.services.admin_bootstrap import bootstrap_admin_account
from app.services.email_service import EmailService


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_admin_overview(client: AsyncClient):
    """Test 1: Unauthenticated request to protected admin endpoint returns 401 Unauthorized."""
    response = await client.get("/api/v1/admin/overview")
    assert response.status_code == 401
    data = response.json()
    msg = data.get("message") or data.get("detail") or ""
    assert "token" in msg.lower() or "authentication" in msg.lower()


@pytest.mark.asyncio
async def test_customer_cannot_access_admin_overview(client: AsyncClient, db_session: AsyncSession):
    """Test 2: Authenticated normal customer cannot access protected admin endpoints (403 Forbidden)."""
    # Create customer user
    customer = User(
        email="customer.jane@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Jane Customer",
        phone="7877794272",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    token = create_access_token(subject=str(customer.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/overview", headers=headers)
    assert response.status_code == 403
    data = response.json()
    msg = data.get("message") or data.get("detail") or ""
    assert "access denied" in msg.lower()

    # Also test inquiries listing endpoint is forbidden for customer
    inquiries_resp = await client.get("/api/v1/admin/inquiries", headers=headers)
    assert inquiries_resp.status_code == 403


@pytest.mark.asyncio
async def test_authenticated_admin_can_access_admin_endpoints(client: AsyncClient, db_session: AsyncSession):
    """Test 3: Authenticated ADMIN user can access protected admin endpoints."""
    admin_user, _ = await bootstrap_admin_account(
        db=db_session,
        email="chiragparmar5768@gmail.com",
        password="SuperAdminSecret123!",
    )
    assert admin_user is not None
    assert admin_user.role == UserRole.ADMIN

    token = create_access_token(subject=str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["admin_email"] == "chiragparmar5768@gmail.com"

    # Admin can list inquiries
    inq_res = await client.get("/api/v1/admin/inquiries", headers=headers)
    assert inq_res.status_code == 200
    assert inq_res.json()["success"] is True


@pytest.mark.asyncio
async def test_user_cannot_self_promote_via_registration_payload(client: AsyncClient, db_session: AsyncSession):
    """Test 4: User cannot self-promote to ADMIN by sending role parameter during public registration."""
    payload = {
        "email": "hacker@example.com",
        "password": "Password123!",
        "full_name": "Privilege Escalation Tester",
        "phone": "+917877794272",
        "role": "ADMIN",  # Attempted override
        "company_name": "Security Labs",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    user_data = response.json()["data"]["user"]
    assert user_data["role"] == "CUSTOMER"

    # Confirm authoritative role in database
    stmt = select(User).where(User.email == "hacker@example.com")
    res = await db_session.execute(stmt)
    db_user = res.scalar_one()
    assert db_user.role == UserRole.CUSTOMER


@pytest.mark.asyncio
async def test_user_cannot_gain_admin_access_by_forging_client_token(client: AsyncClient, db_session: AsyncSession):
    """Test 5: Token claims or client state cannot bypass DB-authoritative role check."""
    customer = User(
        email="forgery.tester@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Forgery Tester",
        phone="7877794272",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    # Even if an attacker crafts an access token with subject pointing to customer ID
    token = create_access_token(subject=str(customer.id))
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/admin/overview", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_bootstrap_is_idempotent(db_session: AsyncSession):
    """Test 6: Repeated execution of admin bootstrap does not create duplicate admin users."""
    target_email = "chiragparmar5768@gmail.com"
    pwd = "AdminBootstrapPassword456!"

    # Run 1: Creates account
    admin1, created1 = await bootstrap_admin_account(db_session, email=target_email, password=pwd)
    assert created1 is True
    assert admin1 is not None
    assert admin1.email == target_email
    assert admin1.role == UserRole.ADMIN

    # Run 2: Verifies existing account, does NOT duplicate
    admin2, created2 = await bootstrap_admin_account(db_session, email=target_email, password=pwd)
    assert created2 is False
    assert admin2.id == admin1.id

    # Run 3: Confirm only 1 admin account exists in DB for this email
    stmt = select(User).where(User.email == target_email)
    users = (await db_session.execute(stmt)).scalars().all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_existing_authentication_remains_intact(client: AsyncClient, db_session: AsyncSession):
    """Test 7: Standard customer registration, login, and profile fetching work without regression."""
    email = "client.standard@example.com"
    pwd = "StandardClientPass123!"

    reg_res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": "Standard Client",
        "phone": "7877794272",
    })
    assert reg_res.status_code == 201

    login_res = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": pwd,
    })
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]

    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == email


@pytest.mark.asyncio
async def test_contact_inquiry_flow_and_admin_management(client: AsyncClient, db_session: AsyncSession):
    """Test public contact inquiry submission, database storage, email dispatch hook, and admin CRM management."""
    # Bootstrap admin
    admin_user, _ = await bootstrap_admin_account(
        db=db_session,
        email="chiragparmar5768@gmail.com",
        password="AdminPassword789!",
    )
    admin_token = create_access_token(subject=str(admin_user.id))
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    inquiry_payload = {
        "name": "Rajesh Sharma",
        "email": "rajesh@manufacturing.in",
        "phone": "7877794272",
        "subject": "Corporate Website with Custom Catalog",
        "business_name": "Sharma Precision Tools",
        "business_type": "Manufacturing",
        "city": "Ahmedabad",
        "source": "CONTACT_FORM",
        "selected_package": "business-websites",
        "message": "We need a multi-page responsive corporate website showcasing precision industrial machinery.",
    }

    with patch.object(EmailService, "_send_inquiry_sync", return_value=True) as mock_send:
        response = await client.post("/api/v1/inquiries", json=inquiry_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        inquiry_id = data["data"]["id"]
        assert data["data"]["subject"] == inquiry_payload["subject"]

    # Verify persisted in database
    stmt = select(Inquiry).where(Inquiry.id == inquiry_id)
    inq = (await db_session.execute(stmt)).scalar_one()
    assert inq.name == "Rajesh Sharma"
    assert inq.subject == "Corporate Website with Custom Catalog"
    assert inq.status == InquiryStatus.NEW

    # Admin lists inquiries and sees the new lead
    admin_list = await client.get("/api/v1/admin/inquiries", headers=admin_headers)
    assert admin_list.status_code == 200
    leads = admin_list.json()["data"]
    assert any(lead["id"] == inquiry_id for lead in leads)

    # Admin updates inquiry status and marks as read
    update_res = await client.patch(
        f"/api/v1/admin/inquiries/{inquiry_id}",
        json={"status": "CONTACTED", "is_read": True},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    updated_lead = update_res.json()["data"]
    assert updated_lead["status"] == "CONTACTED"
    assert updated_lead["read_at"] is not None


@pytest.mark.asyncio
async def test_inquiry_rate_limit_protection(client: AsyncClient, db_session: AsyncSession):
    """Test abuse protection: rapid burst of inquiries from same IP is rate-limited (429)."""
    from app.api.v1.endpoints.inquiries import _ip_rate_tracker
    _ip_rate_tracker.clear()  # Ensure clean state

    payload = {
        "name": "Spam Tester",
        "email": "spam@tester.in",
        "phone": "7877794272",
        "message": "Testing automated abuse prevention mechanism.",
    }
    headers = {"X-Forwarded-For": "203.0.113.195"}

    # First 5 should succeed (status 201)
    for _ in range(5):
        res = await client.post("/api/v1/inquiries", json=payload, headers=headers)
        assert res.status_code == 201

    # 6th should be rejected with 429
    res6 = await client.post("/api/v1/inquiries", json=payload, headers=headers)
    assert res6.status_code == 429
    assert "Too many" in (res6.json().get("message") or "")

