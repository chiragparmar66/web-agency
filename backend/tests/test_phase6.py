import io
import os
import zipfile
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.models.enums import FileCategory
from app.services.storage import storage_service

# Valid test asset payloads
VALID_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
VALID_JPG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
VALID_GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
VALID_WEBP = b"RIFF\x1c\x00\x00\x00WEBPVP8 \x10\x00\x00\x00\x30\x01\x00\x9d\x01\x2a\x01\x00\x01\x00\x00\x00\x00\x00"
VALID_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000120 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"


def create_valid_docx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
        zf.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"></w:document>')
    return buf.getvalue()


async def register_user_and_create_project(
    client: AsyncClient,
    email: str = "asset.owner@studio.in",
    title: str = "Brand Asset Test Site",
) -> tuple[str, str]:
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Asset Client",
            "phone": "+919876543210",
        },
    )
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": title, "business_name": "Studio Assets Inc"},
    )
    project_id = proj_res.json()["data"]["id"]
    return token, project_id


@pytest.mark.asyncio
async def test_upload_valid_png_and_metadata(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "png.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "LOGO"},
        files={"file": ("company_logo.png", VALID_PNG, "image/png")},
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["project_id"] == project_id
    assert data["original_filename"] == "company_logo.png"
    assert data["file_category"] == "LOGO"
    assert data["mime_type"] == "image/png"
    assert data["file_size_bytes"] == len(VALID_PNG)


@pytest.mark.asyncio
async def test_upload_valid_jpg_webp_gif(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "images.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    for name, payload, mime in [
        ("banner.jpg", VALID_JPG, "image/jpeg"),
        ("hero.webp", VALID_WEBP, "image/webp"),
        ("icon.gif", VALID_GIF, "image/gif"),
    ]:
        res = await client.post(
            f"/api/v1/projects/{project_id}/files",
            headers=headers,
            data={"file_category": "IMAGE"},
            files={"file": (name, payload, mime)},
        )
        assert res.status_code == 201
        assert res.json()["data"]["mime_type"] == mime


@pytest.mark.asyncio
async def test_upload_valid_pdf_and_docx(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "docs.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    # PDF
    pdf_res = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "DOCUMENT"},
        files={"file": ("specification.pdf", VALID_PDF, "application/pdf")},
    )
    assert pdf_res.status_code == 201
    assert pdf_res.json()["data"]["mime_type"] == "application/pdf"

    # DOCX
    docx_bytes = create_valid_docx()
    docx_res = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "DOCUMENT"},
        files={"file": ("project_brief.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert docx_res.status_code == 201
    assert docx_res.json()["data"]["mime_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@pytest.mark.asyncio
async def test_list_files_and_download_security_headers(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "list.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload file
    upload_res = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "BRAND_ASSET"},
        files={"file": ("brand_guide.pdf", VALID_PDF, "application/pdf")},
    )
    file_id = upload_res.json()["data"]["id"]

    # List files
    list_res = await client.get(f"/api/v1/projects/{project_id}/files", headers=headers)
    assert list_res.status_code == 200
    files = list_res.json()["data"]
    assert len(files) == 1
    assert files[0]["id"] == file_id

    # Download file
    dl_res = await client.get(
        f"/api/v1/projects/{project_id}/files/{file_id}/download",
        headers=headers,
    )
    assert dl_res.status_code == 200
    assert dl_res.content == VALID_PDF
    assert dl_res.headers["X-Content-Type-Options"] == "nosniff"
    assert dl_res.headers["Cache-Control"] == "private, no-store"
    assert "attachment;" in dl_res.headers["Content-Disposition"]
    assert "brand_guide.pdf" in dl_res.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_delete_file_and_physical_cleanup(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "del.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload
    upload_res = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "IMAGE"},
        files={"file": ("temporary.png", VALID_PNG, "image/png")},
    )
    file_id = upload_res.json()["data"]["id"]

    # Verify download works
    dl_before = await client.get(f"/api/v1/projects/{project_id}/files/{file_id}/download", headers=headers)
    assert dl_before.status_code == 200

    # Delete
    del_res = await client.delete(f"/api/v1/projects/{project_id}/files/{file_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True

    # Verify file is gone from list & download
    list_res = await client.get(f"/api/v1/projects/{project_id}/files", headers=headers)
    assert len(list_res.json()["data"]) == 0

    dl_after = await client.get(f"/api/v1/projects/{project_id}/files/{file_id}/download", headers=headers)
    assert dl_after.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_and_cross_project_protection(client: AsyncClient):
    token_a, proj_a = await register_user_and_create_project(client, "user_a@test.in", "Project A")
    token_b, proj_b = await register_user_and_create_project(client, "user_b@test.in", "Project B")

    # Upload file to project A
    upload_res = await client.post(
        f"/api/v1/projects/{proj_a}/files",
        headers={"Authorization": f"Bearer {token_a}"},
        data={"file_category": "LOGO"},
        files={"file": ("logo_a.png", VALID_PNG, "image/png")},
    )
    file_a_id = upload_res.json()["data"]["id"]

    # 1. Unauthenticated attempts
    assert (await client.get(f"/api/v1/projects/{proj_a}/files")).status_code == 401
    assert (await client.get(f"/api/v1/projects/{proj_a}/files/{file_a_id}/download")).status_code == 401
    assert (await client.delete(f"/api/v1/projects/{proj_a}/files/{file_a_id}")).status_code == 401

    # 2. Cross-project attempts by User B
    b_headers = {"Authorization": f"Bearer {token_b}"}
    # User B cannot list Project A files
    assert (await client.get(f"/api/v1/projects/{proj_a}/files", headers=b_headers)).status_code == 403
    # User B cannot download Project A file
    assert (await client.get(f"/api/v1/projects/{proj_a}/files/{file_a_id}/download", headers=b_headers)).status_code == 403
    # User B cannot delete Project A file
    assert (await client.delete(f"/api/v1/projects/{proj_a}/files/{file_a_id}", headers=b_headers)).status_code == 403
    # User B cannot upload to Project A
    assert (
        await client.post(
            f"/api/v1/projects/{proj_a}/files",
            headers=b_headers,
            data={"file_category": "LOGO"},
            files={"file": ("bad.png", VALID_PNG, "image/png")},
        )
    ).status_code == 403


@pytest.mark.asyncio
async def test_category_restrictions(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "cat.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    # Cannot upload PDF as LOGO
    bad_logo = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "LOGO"},
        files={"file": ("doc.pdf", VALID_PDF, "application/pdf")},
    )
    assert bad_logo.status_code == 400
    msg = bad_logo.json().get("message") or bad_logo.json().get("detail", "")
    assert "requires an image file" in msg

    # Cannot upload PNG as DOCUMENT
    bad_doc = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "DOCUMENT"},
        files={"file": ("pic.png", VALID_PNG, "image/png")},
    )
    assert bad_doc.status_code == 400
    msg_doc = bad_doc.json().get("message") or bad_doc.json().get("detail", "")
    assert "requires a document file" in msg_doc


@pytest.mark.asyncio
async def test_oversized_files_rejection(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "oversize.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    # Image > 5MB
    large_image = VALID_PNG + (b"\x00" * (5 * 1024 * 1024 + 10))
    res_img = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "IMAGE"},
        files={"file": ("giant.png", large_image, "image/png")},
    )
    assert res_img.status_code == 400
    msg_img = res_img.json().get("message") or res_img.json().get("detail", "")
    assert "exceeds 5 MB limit" in msg_img

    # Document > 10MB
    large_pdf = VALID_PDF + (b"\x00" * (10 * 1024 * 1024 + 10))
    res_pdf = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "DOCUMENT"},
        files={"file": ("giant.pdf", large_pdf, "application/pdf")},
    )
    assert res_pdf.status_code == 400
    msg_pdf = res_pdf.json().get("message") or res_pdf.json().get("detail", "")
    assert "exceeds 10 MB limit" in msg_pdf


@pytest.mark.asyncio
async def test_malicious_and_disallowed_files(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "mal.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. EXE disguised as PNG (MZ header)
    exe_as_png = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 100
    res1 = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "IMAGE"},
        files={"file": ("trojan.png", exe_as_png, "image/png")},
    )
    assert res1.status_code == 400
    msg1 = res1.json().get("message") or res1.json().get("detail", "")
    assert "Dangerous" in msg1 or "signature" in msg1

    # 2. HTML disguised as PNG
    html_as_png = b"<!DOCTYPE html><html><script>alert(1)</script></html>"
    res2 = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "IMAGE"},
        files={"file": ("xss.png", html_as_png, "image/png")},
    )
    assert res2.status_code == 400

    # 3. SVG file
    svg_payload = b'<svg xmlns="http://www.w3.org/2000/svg"><circle r="10"/></svg>'
    res3 = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "LOGO"},
        files={"file": ("vector.svg", svg_payload, "image/svg+xml")},
    )
    assert res3.status_code == 400
    msg3 = res3.json().get("message") or res3.json().get("detail", "")
    assert "prohibited" in msg3 or "Unsupported" in msg3

    # 4. Empty file
    res4 = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "IMAGE"},
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert res4.status_code == 400
    msg4 = res4.json().get("message") or res4.json().get("detail", "")
    assert "empty" in msg4

    # 5. Dangerous filenames (path traversal and null bytes sanitized)
    res5 = await client.post(
        f"/api/v1/projects/{project_id}/files",
        headers=headers,
        data={"file_category": "LOGO"},
        files={"file": ("../../etc/passwd.png", VALID_PNG, "image/png")},
    )
    assert res5.status_code == 201
    assert ".." not in res5.json()["data"]["original_filename"]
    assert "/" not in res5.json()["data"]["original_filename"]


@pytest.mark.asyncio
async def test_project_file_quota_50(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "quota.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    # Mock count to 50
    with patch("app.api.v1.endpoints.files.MAX_PROJECT_FILES", 3):
        for i in range(3):
            r = await client.post(
                f"/api/v1/projects/{project_id}/files",
                headers=headers,
                data={"file_category": "IMAGE"},
                files={"file": (f"test_{i}.png", VALID_PNG, "image/png")},
            )
            assert r.status_code == 201

        # 4th upload must be rejected due to quota
        r4 = await client.post(
            f"/api/v1/projects/{project_id}/files",
            headers=headers,
            data={"file_category": "IMAGE"},
            files={"file": ("overflow.png", VALID_PNG, "image/png")},
        )
        assert r4.status_code == 400
        msg4 = r4.json().get("message") or r4.json().get("detail", "")
        assert "quota reached" in msg4


@pytest.mark.asyncio
async def test_database_failure_cleans_up_physical_file(client: AsyncClient):
    token, project_id = await register_user_and_create_project(client, "dbfail.user@test.in")
    headers = {"Authorization": f"Bearer {token}"}

    deleted_paths = []
    original_delete = storage_service.delete_file

    def spy_delete(path):
        deleted_paths.append(path)
        return original_delete(path)

    with patch.object(storage_service, "delete_file", side_effect=spy_delete):
        with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=Exception("Database failure")):
            res = await client.post(
                f"/api/v1/projects/{project_id}/files",
                headers=headers,
                data={"file_category": "IMAGE"},
                files={"file": ("cleanup_test.png", VALID_PNG, "image/png")},
            )
            assert res.status_code == 500
            # Ensure physical storage cleanup was triggered
            assert len(deleted_paths) == 1
