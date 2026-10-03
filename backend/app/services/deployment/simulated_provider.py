import hashlib
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings
from app.services.deployment.base import DeploymentProvider, DeploymentResult


class SimulatedDeploymentProvider(DeploymentProvider):
    """
    Simulated deployment provider for local environments, development testing,
    and staging environments without external cloud platform credentials.
    """

    @property
    def name(self) -> str:
        return "simulated"

    def is_available(self) -> bool:
        return True

    async def deploy(
        self,
        project_id: str,
        project_number: str,
        build_id: str,
        version_number: int,
        artifact_path: Path,
    ) -> DeploymentResult:
        if not artifact_path.exists() or not artifact_path.is_dir():
            return DeploymentResult(
                success=False,
                error=f"Artifact directory not found at: {artifact_path}",
                smoke_test_status="FAILED",
                smoke_test_details={"reason": "Directory missing"},
            )

        entry_file = artifact_path / "index.html"
        if not entry_file.exists():
            return DeploymentResult(
                success=False,
                error="Required entry point index.html not found in artifacts",
                smoke_test_status="FAILED",
                smoke_test_details={"reason": "index.html missing"},
            )

        # Basic smoke test on artifact content
        try:
            content = entry_file.read_text(encoding="utf-8")
            if "<html" not in content.lower():
                return DeploymentResult(
                    success=False,
                    error="Entry file index.html does not contain valid HTML markup",
                    smoke_test_status="FAILED",
                    smoke_test_details={"reason": "Invalid HTML in index.html"},
                )
        except Exception as e:
            return DeploymentResult(
                success=False,
                error=f"Failed to read index.html: {str(e)}",
                smoke_test_status="FAILED",
                smoke_test_details={"reason": str(e)},
            )

        # Generate deterministic simulated deployment ID
        seed = f"{project_id}:{build_id}:{version_number}"
        sim_id = f"sim_{hashlib.sha256(seed.encode()).hexdigest()[:12]}"
        subdomain = project_number.lower().replace("-", "")
        base_domain = settings.DEPLOYMENT_BASE_DOMAIN or "nexusstudio.app"
        live_url = f"https://{subdomain}.{base_domain}"

        return DeploymentResult(
            success=True,
            live_url=live_url,
            provider_deployment_id=sim_id,
            metadata={
                "provider": "simulated",
                "subdomain": subdomain,
                "base_domain": base_domain,
                "version": version_number,
                "file_count": len(list(artifact_path.rglob("*"))),
            },
            smoke_test_status="PASSED",
            smoke_test_details={
                "status_code": 200,
                "entry_point": "index.html",
                "simulated_health_check": "OK",
            },
        )
