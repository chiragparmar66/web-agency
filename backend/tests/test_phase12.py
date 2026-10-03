import json
import os
import shutil
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.init_db import seed_initial_data
from app.models.enums import BuildStatus, PaymentStatus, PaymentType, ProjectStatus, UserRole
from app.models.pricing_package import PricingPackage
from app.models.project import Project
from app.models.payment import Payment
from app.models.user import User
from app.models.website_build import WebsiteBuild
from app.schemas.ai_generation import (
    CodeValidationFinding,
    GeneratedFile,
    GeneratedWebsite,
    WebsiteAnalysisResult,
    WebsitePagePlan,
    WebsitePlanResult,
)
from app.services.ai.artifact_storage import ArtifactStorage
from app.services.ai.base import (
    AIProvider,
    AIProviderError,
    AITask,
    extract_json_from_text,
)
from app.services.ai.build_worker import BuildWorker
from app.services.ai.registry import AIProviderRegistry
from app.services.ai.router import AITaskRouter
from app.services.ai.validator import CodeValidator, sanitize_relative_path


# ---------------------------------------------------------------------------
# Mock AI Provider for safe automated testing
# ---------------------------------------------------------------------------

class MockAIProvider(AIProvider):
    def __init__(self, name: str = "mock_provider", fail_times: int = 0):
        self._name = name
        self.fail_times = fail_times
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return True

    async def generate_text(self, prompt: str, system_prompt=None, model=None, temperature=0.7, max_tokens=4096) -> str:
        self.call_count += 1
        if self.call_count <= self.fail_times:
            raise AIProviderError(f"Simulated error in {self.name}")
        return json.dumps({"status": "ok", "message": "mock text output"})

    async def generate_structured(self, prompt: str, schema, system_prompt=None, model=None, temperature=0.2):
        self.call_count += 1
        if self.call_count <= self.fail_times:
            raise AIProviderError(f"Simulated structured error in {self.name}")

        if schema == WebsiteAnalysisResult:
            return WebsiteAnalysisResult(
                website_type="SaaS Landing Page",
                target_audience="Developers and Tech Startups",
                suggested_pages=["Home", "Features", "Pricing", "Contact"],
                recommended_sections=["Hero", "Key Features", "Testimonials", "Footer"],
                design_system={
                    "primary_color": "#0ea5e9",
                    "secondary_color": "#6366f1",
                    "background_theme": "dark",
                    "font_family": "Inter, sans-serif",
                },
                technical_constraints=["Responsive", "Semantic HTML5"],
                summary="High-converting modern tech SaaS landing website.",
            )
        elif schema == WebsitePlanResult:
            return WebsitePlanResult(
                project_name="CloudPulse Solutions",
                pages=[
                    WebsitePagePlan(
                        path="index.html",
                        title="CloudPulse — Next Gen Cloud Monitoring",
                        purpose="Landing page with value prop, product demo, and CTA.",
                        sections=["Hero", "Features Grid", "Stats", "Footer"],
                    ),
                    WebsitePagePlan(
                        path="about.html",
                        title="About Us — CloudPulse",
                        purpose="Company mission and team.",
                        sections=["Story", "Team", "Footer"],
                    ),
                ],
                navigation=[{"label": "Home", "url": "index.html"}, {"label": "About", "url": "about.html"}],
                shared_components=["Navbar", "Footer"],
                color_palette={"primary": "#0ea5e9", "background": "#0f172a"},
                typography={"body": "Inter", "heading": "Plus Jakarta Sans"},
            )
        elif schema == GeneratedWebsite:
            return GeneratedWebsite(
                entry_file="index.html",
                files=[
                    GeneratedFile(
                        path="index.html",
                        content="""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CloudPulse</title>
  <link rel="stylesheet" href="css/styles.css">
</head>
<body>
  <header><h1>Welcome to CloudPulse</h1></header>
  <main><p>Modern Infrastructure Monitoring for High-Growth Teams.</p></main>
  <script src="js/main.js"></script>
</body>
</html>""",
                        file_type="html",
                    ),
                    GeneratedFile(
                        path="about.html",
                        content="""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>About CloudPulse</title>
  <link rel="stylesheet" href="css/styles.css">
</head>
<body>
  <h1>About Us</h1>
  <p>Building the cloud observability standard.</p>
</body>
</html>""",
                        file_type="html",
                    ),
                    GeneratedFile(
                        path="css/styles.css",
                        content=":root { --primary: #0ea5e9; } body { font-family: sans-serif; background: #0f172a; color: #f8fafc; }",
                        file_type="css",
                    ),
                    GeneratedFile(
                        path="js/main.js",
                        content="console.log('CloudPulse loaded successfully.');",
                        file_type="js",
                    ),
                ],
                summary="Complete multi-page static site with modern dark theme and responsive layout.",
            )

        raise ValueError(f"Unknown schema {schema} in mock provider")


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_ai_configuration_defaults():
    """Verify Phase 12 configuration keys and router defaults."""
    assert hasattr(settings, "AI_GENERATION_ENABLED")
    assert hasattr(settings, "ARTIFACT_STORAGE_PATH")
    assert hasattr(settings, "GEMINI_API_KEY")
    assert hasattr(settings, "CEREBRAS_API_KEY")
    assert hasattr(settings, "GROQ_API_KEY")
    assert hasattr(settings, "OPENROUTER_API_KEY")
    assert settings.AI_ANALYSIS_PROVIDER == "gemini"
    assert settings.AI_PLANNING_PROVIDER == "gemini"
    assert settings.AI_GENERATION_PROVIDER == "cerebras"
    assert settings.AI_REVIEW_PROVIDER == "groq"
    assert settings.AI_FALLBACK_PROVIDER == "openrouter"


def test_ai_provider_registry():
    """Verify provider registration, availability check, and retrieval."""
    registry = AIProviderRegistry()
    mock_prov = MockAIProvider(name="test_provider")
    registry.register(mock_prov)

    assert "test_provider" in registry.list_all()
    assert "test_provider" in registry.list_available()
    assert registry.get("test_provider") == mock_prov

    with pytest.raises(Exception):
        registry.get("non_existent_provider")


def test_json_extraction_utility():
    """Test JSON parsing across raw JSON, markdown fences, and text-embedded blocks."""
    # 1. Raw JSON
    raw = '{"key": "value", "count": 42}'
    assert extract_json_from_text(raw) == {"key": "value", "count": 42}

    # 2. Markdown fence
    fence = """Here is the architecture plan:
```json
{
  "project": "Nexus Studio",
  "status": "ready"
}
```
Hope this helps!"""
    assert extract_json_from_text(fence) == {"project": "Nexus Studio", "status": "ready"}

    # 3. Leading and trailing prose without fences
    prose = 'Analysis completed. {"pages": ["Home", "About"], "version": 1} End of response.'
    assert extract_json_from_text(prose) == {"pages": ["Home", "About"], "version": 1}

    # 4. Invalid JSON raises error
    with pytest.raises(AIProviderError):
        extract_json_from_text("Sorry, I cannot fulfill this request.")


def test_code_validator_rules():
    """Test CodeValidator path traversal, security, and integrity rules."""
    validator = CodeValidator()

    # 1. Valid website
    valid_site = GeneratedWebsite(
        entry_file="index.html",
        files=[
            GeneratedFile(
                path="index.html",
                content="<!DOCTYPE html><html><head><title>Test</title><link rel='stylesheet' href='style.css'></head><body><h1>Hi</h1></body></html>",
                file_type="html",
            ),
            GeneratedFile(
                path="style.css",
                content="body { color: red; }",
                file_type="css",
            ),
        ],
    )
    result = validator.validate_website(valid_site)
    assert result.is_valid is True
    assert result.score > 80.0

    # 2. Missing entry file
    no_entry = GeneratedWebsite(
        entry_file="index.html",
        files=[
            GeneratedFile(path="home.html", content="<html><body>Home</body></html>", file_type="html")
        ],
    )
    res_no_entry = validator.validate_website(no_entry)
    assert res_no_entry.is_valid is False
    assert any(f.rule == "MISSING_ENTRY_FILE" for f in res_no_entry.findings)

    # 3. Path traversal attack in file path
    traversal_site = GeneratedWebsite(
        entry_file="index.html",
        files=[
            GeneratedFile(path="index.html", content="<html><body>Normal</body></html>", file_type="html"),
            GeneratedFile(path="../secret.txt", content="secret content", file_type="txt"),
        ],
    )
    res_traversal = validator.validate_website(traversal_site)
    assert res_traversal.is_valid is False
    assert any(f.rule == "PATH_TRAVERSAL" for f in res_traversal.findings)

    # 4. Leaked Secret detection
    leaked_site = GeneratedWebsite(
        entry_file="index.html",
        files=[
            GeneratedFile(
                path="index.html",
                content="""<html><body><script>const apiKey = "sk-123456789012345678901234567890";</script></body></html>""",
                file_type="html",
            )
        ],
    )
    res_leak = validator.validate_website(leaked_site)
    assert res_leak.is_valid is False
    assert any(f.rule == "LEAKED_SECRET" for f in res_leak.findings)

    # 5. Dangerous execution detection
    dangerous_site = GeneratedWebsite(
        entry_file="index.html",
        files=[
            GeneratedFile(
                path="index.html",
                content="""<html><body><script>const { exec } = require('child_process');</script></body></html>""",
                file_type="html",
            )
        ],
    )
    res_dangerous = validator.validate_website(dangerous_site)
    assert res_dangerous.is_valid is False
    assert any(f.rule == "DANGEROUS_CODE" for f in res_dangerous.findings)


def test_artifact_storage_and_manifest(tmp_path):
    """Test artifact persistence, path isolation, and manifest verification."""
    storage = ArtifactStorage(base_path=str(tmp_path / "builds"))
    website = GeneratedWebsite(
        entry_file="index.html",
        files=[
            GeneratedFile(
                path="index.html",
                content="<!DOCTYPE html><html><body><h1>Saved Build</h1></body></html>",
                file_type="html",
            ),
            GeneratedFile(
                path="css/main.css",
                content="body { margin: 0; }",
                file_type="css",
            ),
        ],
    )

    project_id = "test-proj-uuid-1234"
    build_id = "test-build-uuid-5678"
    version_num = 1

    build_dir = storage.save_build(
        project_id=project_id,
        build_id=build_id,
        version_number=version_num,
        website=website,
        providers_used={"analysis": "gemini", "generation": "cerebras"},
        spec_summary={"page_count": 2},
    )

    assert os.path.exists(build_dir)
    assert os.path.exists(os.path.join(build_dir, "index.html"))
    assert os.path.exists(os.path.join(build_dir, "css", "main.css"))
    assert os.path.exists(os.path.join(build_dir, "manifest.json"))

    # Verify manifest
    manifest = storage.read_manifest(project_id, version_num)
    assert manifest is not None
    assert manifest.project_id == project_id
    assert manifest.build_id == build_id
    assert manifest.version_number == version_num
    assert manifest.entry_file == "index.html"
    assert len(manifest.files) == 2
    assert manifest.providers_used["generation"] == "cerebras"

    # Verify list and read
    files = storage.list_files(project_id, version_num)
    assert "index.html" in files
    assert "css/main.css" in files

    content = storage.read_file(project_id, version_num, "index.html")
    assert "Saved Build" in content


@pytest.mark.asyncio
async def test_task_router_fallback_mechanism():
    """Verify task router tries primary provider then seamlessly falls back."""
    registry = AIProviderRegistry()
    # Primary provider fails on first call
    primary_mock = MockAIProvider(name="cerebras", fail_times=5)
    fallback_mock = MockAIProvider(name="openrouter", fail_times=0)

    registry.register(primary_mock)
    registry.register(fallback_mock)

    router = AITaskRouter(registry=registry)

    # Route website generation task: primary (cerebras) fails -> fallback (openrouter) succeeds
    website, provider_used = await router.execute_task_structured(
        task=AITask.WEBSITE_GENERATION,
        prompt="Generate landing page",
        schema=GeneratedWebsite,
        max_retries=1,
    )

    assert provider_used == "openrouter"
    assert website.entry_file == "index.html"
    assert len(website.files) > 0


from app.models.customer import Customer


@pytest.mark.asyncio
async def test_build_worker_end_to_end(client: AsyncClient, db_session: AsyncSession, tmp_path):
    """
    Test complete build worker lifecycle:
    Admin approval queues build -> Worker processes -> ANALYZING -> GENERATING -> COMPLETED.
    """
    await seed_initial_data(db_session)

    # 1. Create Admin
    admin = User(
        email="admin.phase12@studio.dev",
        hashed_password=hash_password("AdminSecure2026!"),
        full_name="Elena Vance",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    # 2. Create customer and project
    cust_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "client.phase12@techcorp.io",
            "password": "ClientSecure2026!",
            "full_name": "Maya Lin",
            "phone": "+919123456780",
        },
    )
    cust_token = cust_res.json()["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    packages = (await db_session.execute(select(PricingPackage))).scalars().all()
    target_package = packages[0]

    # Create project via customer endpoint
    proj_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Quantum AI Cloud Portal",
            "package_id": target_package.id,
            "business_name": "Quantum AI Systems",
        },
        headers=cust_headers,
    )
    project_id = proj_res.json()["data"]["id"]

    # Admin queues build with waived payment
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin.phase12@studio.dev", "password": "AdminSecure2026!"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

    approval_res = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        json={
            "admin_notes": "Phase 12 automated pipeline verification build.",
            "waive_payment": True,
        },
        headers=admin_headers,
    )
    assert approval_res.status_code == 200
    build_id = approval_res.json()["data"]["build"]["id"]

    # 3. Setup mock worker with isolated temporary storage
    mock_provider = MockAIProvider(name="gemini")
    mock_registry = AIProviderRegistry()
    mock_registry.register(mock_provider)
    for name in ["cerebras", "groq", "openrouter"]:
        mock_registry.register(MockAIProvider(name=name))

    custom_storage = ArtifactStorage(base_path=str(tmp_path / "builds"))
    worker = BuildWorker(
        router=AITaskRouter(registry=mock_registry),
        storage=custom_storage,
        validator=CodeValidator(),
    )

    # 4. Process build
    completed_build = await worker.process_build(build_id=build_id, db=db_session)

    assert completed_build.status == BuildStatus.COMPLETED
    assert completed_build.is_active is True
    assert completed_build.spec_data is not None
    assert completed_build.spec_data["website_type"] == "SaaS Landing Page"
    assert completed_build.architecture_data is not None
    assert completed_build.generated_code_path is not None
    assert os.path.exists(completed_build.generated_code_path)

    # Verify manifest exists in storage
    manifest = custom_storage.read_manifest(project_id, completed_build.version_number)
    assert manifest is not None
    assert manifest.version_number == 1
    assert "index.html" in [f["path"] for f in manifest.files]


@pytest.mark.asyncio
async def test_admin_process_and_manifest_endpoints(
    client: AsyncClient, db_session: AsyncSession, tmp_path, monkeypatch
):
    """Test admin process trigger and artifact inspection endpoints."""
    await seed_initial_data(db_session)

    monkeypatch.setattr(settings, "ARTIFACT_STORAGE_PATH", str(tmp_path / "admin_builds"))

    # 1. Admin user
    admin = User(
        email="superadmin.phase12@studio.dev",
        hashed_password=hash_password("AdminSecure2026!"),
        full_name="Marcus Aurelius",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin.phase12@studio.dev", "password": "AdminSecure2026!"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

    # 2. Register customer
    cust_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "customer.admininspect@studio.dev",
            "password": "CustomerSecure2026!",
            "full_name": "Lucius Verus",
            "phone": "+919876543299",
        },
    )
    cust_token = cust_res.json()["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    packages = (await db_session.execute(select(PricingPackage))).scalars().all()

    # Create project via API so customer association is properly handled
    proj_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Admin Inspection Project",
            "business_name": "Admin Inspection LLC",
            "package_id": packages[0].id,
        },
        headers=cust_headers,
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["data"]["id"]

    # Approve build to create queued WebsiteBuild
    app_res = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        json={"waive_payment": True, "admin_notes": "Inspection test build."},
        headers=admin_headers,
    )
    assert app_res.status_code == 200
    build_id = app_res.json()["data"]["build"]["id"]

    # Save a mock artifact so file inspection works
    storage = ArtifactStorage(base_path=str(tmp_path / "admin_builds"))
    website = GeneratedWebsite(
        entry_file="index.html",
        files=[
            GeneratedFile(path="index.html", content="<html><body>API Test</body></html>", file_type="html"),
            GeneratedFile(path="style.css", content="body { color: blue; }", file_type="css"),
        ],
    )
    storage.save_build(
        project_id=project_id,
        build_id=build_id,
        version_number=1,
        website=website,
        providers_used={"test": "mock"},
    )

    # Verify manifest endpoint
    man_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/manifest",
        headers=admin_headers,
    )
    assert man_res.status_code == 200
    assert man_res.json()["data"]["entry_file"] == "index.html"

    # Verify files endpoint
    files_res = await client.get(
        f"/api/v1/admin/projects/{project_id}/builds/{build_id}/files",
        headers=admin_headers,
    )
    assert files_res.status_code == 200
    files_data = files_res.json()["data"]
    assert "index.html" in files_data
    assert "style.css" in files_data


@pytest.mark.asyncio
async def test_build_worker_failure_flow(client: AsyncClient, db_session: AsyncSession, tmp_path):
    """Test build worker handles provider failure by marking build as FAILED."""
    await seed_initial_data(db_session)

    # 1. Register customer & create project
    cust_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "failtest.phase12@studio.dev",
            "password": "FailPass2026!",
            "full_name": "Test User",
            "phone": "+919876543111",
        },
    )
    cust_token = cust_res.json()["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    packages = (await db_session.execute(select(PricingPackage))).scalars().all()

    proj_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Failing Build Project",
            "business_name": "Fail Test Corp",
            "package_id": packages[0].id,
        },
        headers=cust_headers,
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["data"]["id"]

    # Create admin
    admin = User(
        email="admin.failtest@studio.dev",
        hashed_password=hash_password("AdminSecure2026!"),
        full_name="Admin Failure Test",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin.failtest@studio.dev", "password": "AdminSecure2026!"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

    app_res = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        json={"waive_payment": True},
        headers=admin_headers,
    )
    build_id = app_res.json()["data"]["build"]["id"]

    # Provider that fails completely on all calls
    failing_provider = MockAIProvider(name="failing_mock", fail_times=999)
    failing_registry = AIProviderRegistry()
    for name in ["gemini", "cerebras", "groq", "openrouter"]:
        failing_registry.register(MockAIProvider(name=name, fail_times=999))

    worker = BuildWorker(
        router=AITaskRouter(registry=failing_registry),
        storage=ArtifactStorage(base_path=str(tmp_path / "builds")),
    )

    failed_build = await worker.process_build(build_id=build_id, db=db_session)
    assert failed_build.status == BuildStatus.FAILED
    assert "Build Error" in (failed_build.admin_notes or "")


class RepairMockAIProvider(MockAIProvider):
    """Mock provider that returns invalid site first, but fixed site on repair."""
    def __init__(self):
        super().__init__(name="repair_mock")

    async def generate_structured(self, prompt: str, schema, system_prompt=None, model=None, temperature=0.2):
        if schema == WebsiteAnalysisResult:
            return WebsiteAnalysisResult(
                website_type="Portfolio",
                target_audience="Designers",
                suggested_pages=["Home"],
                recommended_sections=["Hero"],
                summary="Designer portfolio.",
            )
        elif schema == WebsitePlanResult:
            return WebsitePlanResult(
                project_name="Portfolio Site",
                pages=[WebsitePagePlan(path="index.html", title="Portfolio", purpose="Showcase")],
            )
        elif schema == GeneratedWebsite:
            # Check if this is a repair prompt
            if "VALIDATION ERRORS" in prompt or "Regenerate all files so that all errors are resolved" in prompt:
                # Corrected site
                return GeneratedWebsite(
                    entry_file="index.html",
                    files=[
                        GeneratedFile(path="index.html", content="<!DOCTYPE html><html><body><h1>Repaired Site</h1></body></html>", file_type="html")
                    ],
                    summary="Repaired valid website",
                )
            else:
                # Initially missing entry file (invalid)
                return GeneratedWebsite(
                    entry_file="index.html",
                    files=[
                        GeneratedFile(path="wrong_entry.html", content="<html><body>No index file</body></html>", file_type="html")
                    ],
                    summary="Invalid site missing index.html",
                )
        return await super().generate_structured(prompt, schema, system_prompt, model, temperature)


@pytest.mark.asyncio
async def test_build_worker_repair_flow(client: AsyncClient, db_session: AsyncSession, tmp_path):
    """Test that build worker catches validation errors and triggers AI repair to fix them."""
    await seed_initial_data(db_session)

    # 1. Register customer & create project
    cust_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "repairtest.phase12@studio.dev",
            "password": "RepairPass2026!",
            "full_name": "Repair User",
            "phone": "+919876543999",
        },
    )
    cust_token = cust_res.json()["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    packages = (await db_session.execute(select(PricingPackage))).scalars().all()

    proj_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Repair Test Project",
            "business_name": "Repair Studio",
            "package_id": packages[0].id,
        },
        headers=cust_headers,
    )
    project_id = proj_res.json()["data"]["id"]

    # 2. Admin approval
    admin = User(
        email="admin.repairtest@studio.dev",
        hashed_password=hash_password("AdminSecure2026!"),
        full_name="Admin Repair Test",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin.repairtest@studio.dev", "password": "AdminSecure2026!"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

    app_res = await client.post(
        f"/api/v1/admin/projects/{project_id}/approve-build",
        json={"waive_payment": True},
        headers=admin_headers,
    )
    build_id = app_res.json()["data"]["build"]["id"]

    # Setup worker with RepairMockAIProvider
    repair_provider = RepairMockAIProvider()
    repair_registry = AIProviderRegistry()
    for name in ["gemini", "cerebras", "groq", "openrouter"]:
        repair_registry.register(repair_provider)

    worker = BuildWorker(
        router=AITaskRouter(registry=repair_registry),
        storage=ArtifactStorage(base_path=str(tmp_path / "builds")),
        validator=CodeValidator(),
    )

    repaired_build = await worker.process_build(build_id=build_id, db=db_session)
    assert repaired_build.status == BuildStatus.COMPLETED
    assert repaired_build.generated_code_path is not None

