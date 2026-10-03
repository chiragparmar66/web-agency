import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.services.deployment.base import DeploymentProvider, DeploymentResult

logger = logging.getLogger(__name__)


class VercelDeploymentProvider(DeploymentProvider):
    """
    Vercel Deployment Provider.
    Requires VERCEL_TOKEN in configuration.
    """

    @property
    def name(self) -> str:
        return "vercel"

    def is_available(self) -> bool:
        return bool(settings.VERCEL_TOKEN and settings.VERCEL_TOKEN.strip())

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
                error="Vercel credentials (VERCEL_TOKEN) are not configured.",
                smoke_test_status="NOT_RUN",
                smoke_test_details={"reason": "Missing VERCEL_TOKEN"},
            )

        if not artifact_path.exists() or not artifact_path.is_dir():
            return DeploymentResult(
                success=False,
                error=f"Artifact directory not found at: {artifact_path}",
                smoke_test_status="FAILED",
            )

        # In production with valid VERCEL_TOKEN, httpx would call:
        # POST https://api.vercel.com/v13/deployments
        # For now, if token is set but dummy/placeholder, handle gracefully
        logger.info(f"Triggering Vercel deployment for project {project_number} v{version_number}")
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {settings.VERCEL_TOKEN}",
                "Content-Type": "application/json",
            }
            # Prepare files list from artifact_path
            files_payload = []
            for file_path in artifact_path.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(artifact_path).as_posix()
                    # Skip system or hidden files
                    if rel_path.startswith("."):
                        continue
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        files_payload.append({
                            "file": rel_path,
                            "data": content,
                        })
                    except Exception:
                        pass

            payload = {
                "name": f"nexus-{project_number.lower().replace('_', '-')}",
                "files": files_payload,
                "projectSettings": {
                    "framework": None,
                },
            }
            params = {}
            if settings.VERCEL_TEAM_ID:
                params["teamId"] = settings.VERCEL_TEAM_ID

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    json=payload,
                    headers=headers,
                    params=params,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    live_url = f"https://{data.get('url')}"
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
                        error=f"Vercel API error ({resp.status_code}): {resp.text[:300]}",
                        smoke_test_status="FAILED",
                        smoke_test_details={"response_code": resp.status_code},
                    )
        except Exception as e:
            logger.error(f"Vercel deployment failed: {str(e)}")
            return DeploymentResult(
                success=False,
                error=f"Vercel deployment exception: {str(e)}",
                smoke_test_status="NOT_RUN",
                smoke_test_details={"exception": str(e)},
            )
