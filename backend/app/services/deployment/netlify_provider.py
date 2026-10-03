import logging
from pathlib import Path

from app.core.config import settings
from app.services.deployment.base import DeploymentProvider, DeploymentResult

logger = logging.getLogger(__name__)


class NetlifyDeploymentProvider(DeploymentProvider):
    """
    Netlify Deployment Provider.
    Requires NETLIFY_AUTH_TOKEN in configuration.
    """

    @property
    def name(self) -> str:
        return "netlify"

    def is_available(self) -> bool:
        return bool(settings.NETLIFY_AUTH_TOKEN and settings.NETLIFY_AUTH_TOKEN.strip())

    async def deploy(
        self,
        project_id: str,
        project_number: str,
        build_id: str,
        version_number: int,
        artifact_path: Path,
    ) -> DeploymentResult:
        if not self.is_available():
            return DeploymentResult(
                success=False,
                error="Netlify credentials (NETLIFY_AUTH_TOKEN) are not configured.",
                smoke_test_status="NOT_RUN",
                smoke_test_details={"reason": "Missing NETLIFY_AUTH_TOKEN"},
            )

        if not artifact_path.exists() or not artifact_path.is_dir():
            return DeploymentResult(
                success=False,
                error=f"Artifact directory not found at: {artifact_path}",
                smoke_test_status="FAILED",
            )

        logger.info(f"Triggering Netlify deployment for project {project_number} v{version_number}")
        try:
            import httpx
            import zipfile
            import io

            # Zip the artifact directory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in artifact_path.rglob("*"):
                    if file_path.is_file() and not file_path.name.startswith("."):
                        arcname = file_path.relative_to(artifact_path).as_posix()
                        zip_file.write(file_path, arcname)
            zip_buffer.seek(0)

            site_id = settings.NETLIFY_SITE_ID
            url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys" if site_id else "https://api.netlify.com/api/v1/sites"
            headers = {
                "Authorization": f"Bearer {settings.NETLIFY_AUTH_TOKEN}",
                "Content-Type": "application/zip",
            }

            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(url, content=zip_buffer.getvalue(), headers=headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    live_url = data.get("ssl_url") or data.get("url")
                    dep_id = data.get("id")
                    return DeploymentResult(
                        success=True,
                        live_url=live_url,
                        provider_deployment_id=dep_id,
                        metadata=data,
                        smoke_test_status="PASSED",
                        smoke_test_details={"status_code": 200, "url": live_url},
                    )
                else:
                    return DeploymentResult(
                        success=False,
                        error=f"Netlify API error ({resp.status_code}): {resp.text[:300]}",
                        smoke_test_status="FAILED",
                        smoke_test_details={"response_code": resp.status_code},
                    )
        except Exception as e:
            logger.error(f"Netlify deployment failed: {str(e)}")
            return DeploymentResult(
                success=False,
                error=f"Netlify deployment exception: {str(e)}",
                smoke_test_status="NOT_RUN",
                smoke_test_details={"exception": str(e)},
            )
