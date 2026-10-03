from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.activity import ProjectActivity
from app.models.deployment import Deployment
from app.models.enums import BuildReviewStatus, BuildStatus, DeploymentStatus, PaymentStatus, ProjectStatus
from app.models.project import Project
from app.models.website_build import WebsiteBuild
from app.schemas.deployment import DeploymentEligibilityResponse
from app.services.ai.artifact_storage import ArtifactStorage
from app.services.deployment.base import DeploymentProvider
from app.services.deployment.netlify_provider import NetlifyDeploymentProvider
from app.services.deployment.simulated_provider import SimulatedDeploymentProvider
from app.services.deployment.vercel_provider import VercelDeploymentProvider

logger = logging.getLogger(__name__)


class DeploymentService:
    def __init__(self):
        self.providers: Dict[str, DeploymentProvider] = {
            "simulated": SimulatedDeploymentProvider(),
            "vercel": VercelDeploymentProvider(),
            "netlify": NetlifyDeploymentProvider(),
        }
        self.artifact_storage = ArtifactStorage(settings.ARTIFACT_STORAGE_PATH)

    def get_provider(self, provider_name: Optional[str] = None) -> DeploymentProvider:
        name = (provider_name or settings.DEPLOYMENT_PROVIDER or "simulated").lower()
        if name not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported deployment provider: '{name}'. Available: {list(self.providers.keys())}",
            )
        return self.providers[name]

    async def check_eligibility(
        self,
        db: AsyncSession,
        project: Project,
        build: WebsiteBuild,
    ) -> DeploymentEligibilityResponse:
        blockers: List[str] = []

        # Gate 1: Build Status
        build_completed = (build.status == BuildStatus.COMPLETED)
        if not build_completed:
            blockers.append(f"Build is in state '{build.status}', but must be '{BuildStatus.COMPLETED}'")

        # Gate 2: Admin Review Approval
        admin_approved = (build.review_status == BuildReviewStatus.APPROVED)
        if not admin_approved:
            blockers.append(
                f"Build admin review status is '{build.review_status}', but must be '{BuildReviewStatus.APPROVED}'"
            )

        # Gate 3: Client Final Approval
        client_approved = bool(build.client_approved)
        if not client_approved:
            blockers.append("Client has not given final approval on this website build")

        # Gate 4: Remaining Payment Clearance
        # Load package and payments if not loaded
        package_price = float(project.package.price_inr) if project.package else 0.0
        total_paid = sum(
            float(p.amount_inr) for p in (project.payments or []) if p.status == PaymentStatus.SUCCESS
        )
        remaining = max(0.0, package_price - total_paid)
        final_payment_cleared = (remaining <= 0.001)
        if not final_payment_cleared:
            blockers.append(
                f"Remaining payment balance of ₹{remaining:.2f} is pending (Total price: ₹{package_price:.2f}, Paid: ₹{total_paid:.2f})"
            )

        # Gate 5: Artifact Existence & Safety
        artifact_available = False
        try:
            artifact_dir = self.artifact_storage.get_build_dir(project.id, build.version_number)
            if not artifact_dir.exists() or not artifact_dir.is_dir():
                blockers.append(f"Generated artifact directory does not exist at {artifact_dir}")
            else:
                entry_file = artifact_dir / "index.html"
                if not entry_file.exists():
                    blockers.append(f"Entry point 'index.html' is missing in build artifacts")
                else:
                    # Security traversal check: must be strictly inside storage root
                    storage_root = Path(settings.ARTIFACT_STORAGE_PATH).resolve()
                    resolved_dir = artifact_dir.resolve()
                    if not str(resolved_dir).startswith(str(storage_root)):
                        blockers.append("Security violation: artifact path escapes storage root")
                    else:
                        artifact_available = True
        except Exception as e:
            blockers.append(f"Error checking build artifacts: {str(e)}")

        is_eligible = (
            build_completed
            and admin_approved
            and client_approved
            and final_payment_cleared
            and artifact_available
        )

        return DeploymentEligibilityResponse(
            is_eligible=is_eligible,
            build_completed=build_completed,
            admin_approved=admin_approved,
            client_approved=client_approved,
            final_payment_cleared=final_payment_cleared,
            artifact_available=artifact_available,
            package_price_inr=package_price,
            total_paid_inr=total_paid,
            remaining_balance_inr=remaining,
            blockers=blockers,
        )

    async def deploy_build(
        self,
        db: AsyncSession,
        project: Project,
        build: WebsiteBuild,
        user_id: str,
        provider_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Deployment:
        # Check all 5 security gates
        eligibility = await self.check_eligibility(db, project, build)
        if not eligibility.is_eligible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Website build does not meet all 5 requirements for production deployment",
                    "blockers": eligibility.blockers,
                    "eligibility": eligibility.model_dump(),
                },
            )

        provider = self.get_provider(provider_name)

        # Create Deployment record in QUEUED / DEPLOYING state
        deployment = Deployment(
            project_id=project.id,
            build_id=build.id,
            version_number=build.version_number,
            status=DeploymentStatus.DEPLOYING,
            provider=provider.name,
            deployed_by_user_id=user_id,
            smoke_test_status="NOT_RUN",
        )
        db.add(deployment)

        # Transition project status to DEPLOYING
        previous_project_status = project.status
        project.status = ProjectStatus.DEPLOYING

        await db.commit()
        await db.refresh(deployment)

        # Execute deployment via provider
        artifact_dir = self.artifact_storage.get_build_dir(project.id, build.version_number)
        result = await provider.deploy(
            project_id=project.id,
            project_number=project.project_number,
            build_id=build.id,
            version_number=build.version_number,
            artifact_path=artifact_dir,
        )

        if result.success:
            deployment.status = DeploymentStatus.DEPLOYED
            deployment.live_url = result.live_url
            deployment.provider_deployment_id = result.provider_deployment_id
            deployment.deployed_at = datetime.now(timezone.utc)
            deployment.smoke_test_status = result.smoke_test_status
            deployment.smoke_test_details = result.smoke_test_details
            deployment.deployment_metadata = result.metadata

            # Update project production URL and status to LIVE
            project.production_url = result.live_url
            project.status = ProjectStatus.LIVE

            # Log project activity
            activity = ProjectActivity(
                project_id=project.id,
                performed_by_user_id=user_id,
                action_type="DEPLOYED_LIVE",
                old_status=previous_project_status.value if hasattr(previous_project_status, 'value') else str(previous_project_status),
                new_status=ProjectStatus.LIVE.value,
                note=f"Website build v{build.version_number} successfully deployed to {result.live_url} via {provider.name}.",
                is_visible_to_client=True,
            )
            db.add(activity)
            logger.info(f"Project {project.project_number} deployed to {result.live_url}")
        else:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = result.error
            deployment.smoke_test_status = result.smoke_test_status
            deployment.smoke_test_details = result.smoke_test_details

            # Revert project status to previous (or APPROVED)
            revert_status = previous_project_status if previous_project_status != ProjectStatus.DEPLOYING else ProjectStatus.APPROVED
            project.status = revert_status

            activity = ProjectActivity(
                project_id=project.id,
                performed_by_user_id=user_id,
                action_type="DEPLOYMENT_FAILED",
                old_status=ProjectStatus.DEPLOYING.value,
                new_status=revert_status.value if hasattr(revert_status, 'value') else str(revert_status),
                note=f"Deployment of build v{build.version_number} failed via {provider.name}: {result.error}",
                is_visible_to_client=False,
            )
            db.add(activity)
            logger.error(f"Deployment failed for project {project.project_number}: {result.error}")

        await db.commit()
        await db.refresh(deployment)
        return deployment
