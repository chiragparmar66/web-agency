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
from app.models.enums import BuildReviewStatus, BuildStatus, ProjectStatus, UserRole
from app.models.pricing_package import PricingPackage
from app.models.project import Project
from app.models.user import User
from app.models.website_build import WebsiteBuild
from app.schemas.ai_generation import GeneratedFile, GeneratedWebsite
from app.services.ai.artifact_storage import ArtifactStorage


async def setup_phase13_test_environment(
    client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch
):
    """Setup admin, customer, project, and saved build artifact."""
    await seed_initial_data(db_session)
    monkeypatch.setattr(settings, "ARTIFACT_STORAGE_PATH", str(tmp_path / "builds"))

    # 1. Admin user
    admin = User(
        email="admin.phase13@studio.dev",
        hashed_password=hash_password("AdminSecure2026!"),
        full_name="Sarah Connor",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin.phase13@studio.dev", "password": "AdminSecure2026!"},
    )
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Customer user
    cust_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "customer.phase13@client.dev",
            "password": "CustomerSecure2026!",
            "full_name": "John Connor",
            "phone": "+919876543210",
        },
    )
    cust_token = cust_res.json()["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    packages = (await db_session.execute(select(PricingPackage))).scalars().all()
    package = packages[0]

    # 3. Create project
    proj_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Cyberdyne Systems Portal",
            "business_name": "Cyberdyne Systems",
            "package_id": package.id,
        },
        headers=cust_headers,
    )
    project_id = proj_res.json()["data"]["id"]

    # 4. Create WebsiteBuild record
    build = WebsiteBuild(
        project_id=project_id,
        version_number=1,
        status=BuildStatus.COMPLETED,
        review_status=BuildReviewStatus.PENDING_REVIEW,
        is_active=True,
        spec_data={
            "website_type": "Corporate AI Portal",
            "target_audience": "Defense and Enterprise",
            "summary": "High security autonomous infrastructure portal.",
            "validation_score": 95.0,
            "findings": [
                {
                    "file_path": "about.html",
                    "severity": "WARNING",
                    "rule": "MISSING_LOCAL_ASSET",
                    "message": "Referenced asset 'team.jpg' not found in file list.",
                }
            ],
        },
        architecture_data={"pages": [{"path": "index.html", "title": "Home"}]},
        admin_notes="Phase 13 review target build.",
    )
    db_session.add(build)
    await db_session.commit()
    await db_session.refresh(build)

    # 5. Save physical build artifact in storage
    storage = ArtifactStorage(base_path=str(tmp_path / "builds"))
    website = GeneratedWebsite(
        entry_file="index.html",
        files=[
            GeneratedFile(
                path="index.html",
                content="<!DOCTYPE html><html><head><title>Cyberdyne</title></head><body><h1>Welcome to Cyberdyne</h1></body></html>",
                file_type="html",
            ),
            GeneratedFile(
                path="css/styles.css",
                content="body { background: #000; color: #fff; }",
                file_type="css",
            ),
            GeneratedFile(
                path="js/main.js",
                content="console.log('System online.');",
                file_type="js",
            ),
        ],
        summary="Completed Cyberdyne portal website.",
    )
    build_path = storage.save_build(
        project_id=project_id,
        build_id=build.id,
        version_number=1,
        website=website,
        providers_used={"analysis": "gemini", "generation": "cerebras"},
        spec_summary={"validation_score": 95.0},
    )

    # Also create a dummy binary file in the build directory for binary testing
    binary_path = os.path.join(build_path, "logo.png")
    with open(binary_path, "wb") as bf:
        bf.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    return admin_headers, cust_headers, project_id, build.id, storage


@pytest.mark.asyncio
async def test_admin_build_review_endpoint(client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch):
    """Test GET /projects/{project_id}/builds/{build_id}/review endpoint."""
    admin_headers, cust_headers, project_id, build_id, _ = await setup_phase13_test_environment(
        client, db_session, tmp_path, monkeypatch
    )

    # 1. Admin can access review
    res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/review",
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["build_id"] == build_id
    assert data["version_number"] == 1
    assert data["status"] == "COMPLETED"
    assert data["review_status"] == "PENDING_REVIEW"
    assert data["validation_score"] == 95.0
    assert data["entry_file"] == "index.html"
    assert data["providers_used"]["generation"] == "cerebras"
    assert len(data["validation_findings"]) == 1
    assert data["validation_findings"][0]["severity"] == "WARNING"

    # 2. Customer rejected (403 Forbidden)
    cust_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/review",
        headers=cust_headers,
    )
    assert cust_res.status_code == 403

    # 3. Unauthenticated rejected (401 Unauthorized)
    anon_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/review"
    )
    assert anon_res.status_code == 401

    # 4. Wrong project/build combination returns 404
    wrong_res = await client.get(
        f"/api/v1/admin/projects/wrong-uuid-1234/builds/{build_id}/review",
        headers=admin_headers,
    )
    assert wrong_res.status_code == 404


@pytest.mark.asyncio
async def test_admin_file_inspection_and_traversal_protection(
    client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch
):
    """Test safe file listing, content retrieval, binary protection, and path traversal block."""
    admin_headers, cust_headers, project_id, build_id, _ = await setup_phase13_test_environment(
        client, db_session, tmp_path, monkeypatch
    )

    # 1. List files with detailed metadata
    list_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/files?detailed=true",
        headers=admin_headers,
    )
    assert list_res.status_code == 200
    files_meta = list_res.json()["data"]
    file_paths = [f["path"] for f in files_meta]
    assert "index.html" in file_paths
    assert "css/styles.css" in file_paths
    assert "logo.png" in file_paths

    logo_meta = next(f for f in files_meta if f["path"] == "logo.png")
    assert logo_meta["is_text"] is False

    # 2. Inspect safe text file content
    content_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/files/index.html",
        headers=admin_headers,
    )
    assert content_res.status_code == 200
    file_data = content_res.json()["data"]
    assert file_data["is_text"] is True
    assert "<h1>Welcome to Cyberdyne</h1>" in file_data["content"]
    assert file_data["is_truncated"] is False

    # 3. Inspect binary file (should return metadata, content=None)
    bin_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/files/logo.png",
        headers=admin_headers,
    )
    assert bin_res.status_code == 200
    bin_data = bin_res.json()["data"]
    assert bin_data["is_text"] is False
    assert bin_data["content"] is None
    assert bin_data["size_bytes"] > 0

    # 4. Path traversal attempts rejected
    traversal_paths = [
        "../secret.txt",
        "..%2Fsecret.txt",
        "nested/../../secret.txt",
        "C:\\Windows\\System32\\cmd.exe",
        "/etc/passwd",
    ]
    for bad_path in traversal_paths:
        t_res = await client.get(
            f"/api/v1/admin/projects/{project_id}/builds/{build_id}/files/{bad_path}",
            headers=admin_headers,
        )
        assert t_res.status_code in (400, 404), f"Path {bad_path} did not reject safely"

    # 5. Customer cannot read files
    cust_file_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/files/index.html",
        headers=cust_headers,
    )
    assert cust_file_res.status_code == 403


@pytest.mark.asyncio
async def test_admin_approve_and_reject_review_actions(
    client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch
):
    """Test admin approve, reject, and audit logging flow."""
    admin_headers, cust_headers, project_id, build_id, _ = await setup_phase13_test_environment(
        client, db_session, tmp_path, monkeypatch
    )

    # 1. Reject build requires reason
    bad_reject = await client.post(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/reject-review",
        json={"reason": "no"},  # Less than 3 chars
        headers=admin_headers,
    )
    assert bad_reject.status_code == 422

    # Reject successfully with valid reason
    reject_res = await client.post(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/reject-review",
        json={"reason": "Hero section text contrast too low; needs lighter headline color."},
        headers=admin_headers,
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["review_status"] == "REJECTED"
    assert "contrast too low" in reject_res.json()["data"]["review_notes"]

    # Verify audit activity logged
    act_stmt = select(ProjectActivity).where(
        ProjectActivity.project_id == project_id,
        ProjectActivity.action_type == "BUILD_REJECTED_BY_ADMIN",
    )
    act_res = (await db_session.execute(act_stmt)).scalar_one_or_none()
    assert act_res is not None
    assert "Sarah Connor" in act_res.note
    assert "contrast too low" in act_res.note

    # 2. Approve build
    approve_res = await client.post(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/approve-review",
        json={"notes": "All feedback incorporated and layout approved."},
        headers=admin_headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["review_status"] == "APPROVED"

    # Verify approval activity logged
    appr_stmt = select(ProjectActivity).where(
        ProjectActivity.project_id == project_id,
        ProjectActivity.action_type == "BUILD_APPROVED_BY_ADMIN",
    )
    appr_act = (await db_session.execute(appr_stmt)).scalar_one_or_none()
    assert appr_act is not None
    assert "Sarah Connor" in appr_act.note


@pytest.mark.asyncio
async def test_cannot_approve_incomplete_build(
    client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch
):
    """Test that a QUEUED or ANALYZING build cannot be approved."""
    admin_headers, _, project_id, _, _ = await setup_phase13_test_environment(
        client, db_session, tmp_path, monkeypatch
    )

    # Create incomplete build in QUEUED state
    incomplete_build = WebsiteBuild(
        project_id=project_id,
        version_number=2,
        status=BuildStatus.QUEUED,
        review_status=BuildReviewStatus.PENDING_REVIEW,
        is_active=False,
    )
    db_session.add(incomplete_build)
    await db_session.commit()
    await db_session.refresh(incomplete_build)

    res = await client.post(
        f"/api/v1/admin/projects/{project_id}/builds/{incomplete_build.id}/approve-review",
        json={"notes": "premature approval"},
        headers=admin_headers,
    )
    assert res.status_code == 400
    assert "must be COMPLETED" in res.json()["message"]


@pytest.mark.asyncio
async def test_admin_rebuild_request_flow(
    client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch
):
    """Test admin rebuild request creates new version and deactivates prior builds."""
    admin_headers, _, project_id, build_id, _ = await setup_phase13_test_environment(
        client, db_session, tmp_path, monkeypatch
    )

    # Request rebuild
    rebuild_res = await client.post(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/rebuild",
        json={"admin_notes": "Rebuild with high-contrast theme and updated hero."},
        headers=admin_headers,
    )
    assert rebuild_res.status_code == 200
    new_build_data = rebuild_res.json()["data"]
    assert new_build_data["version_number"] == 2
    assert new_build_data["status"] == "QUEUED"
    assert new_build_data["review_status"] == "PENDING_REVIEW"
    assert new_build_data["is_active"] is True

    # Verify previous build was deactivated
    old_build_stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id)
    old_build = (await db_session.execute(old_build_stmt)).scalar_one()
    assert old_build.is_active is False

    # Verify audit activity
    reb_act_stmt = select(ProjectActivity).where(
        ProjectActivity.project_id == project_id,
        ProjectActivity.action_type == "BUILD_REBUILD_REQUESTED",
    )
    reb_act = (await db_session.execute(reb_act_stmt)).scalar_one_or_none()
    assert reb_act is not None
    assert "Build v2" in reb_act.note


@pytest.mark.asyncio
async def test_safe_sandbox_view_security_headers(
    client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch
):
    """Test sandbox view returns strict CSP with script-src 'none' preventing code execution."""
    admin_headers, cust_headers, project_id, build_id, _ = await setup_phase13_test_environment(
        client, db_session, tmp_path, monkeypatch
    )

    # Admin access sandbox view
    res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/sandbox-view?path=index.html",
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert "Content-Security-Policy" in res.headers
    csp = res.headers["Content-Security-Policy"]
    assert "script-src 'none'" in csp
    assert "frame-ancestors 'self'" in csp
    assert "X-Frame-Options" in res.headers
    assert res.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "Welcome to Cyberdyne" in res.text

    # Customer access rejected
    cust_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/sandbox-view?path=index.html",
        headers=cust_headers,
    )
    assert cust_res.status_code == 403
