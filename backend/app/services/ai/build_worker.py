import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.activity import ProjectActivity
from app.models.enums import BuildStatus, ProjectStatus
from app.models.website_build import WebsiteBuild
from app.schemas.ai_generation import (
    GeneratedWebsite,
    WebsiteAnalysisResult,
    WebsitePlanResult,
)
from app.services.ai_context import build_project_ai_context
from app.services.ai.artifact_storage import ArtifactStorage
from app.services.ai.base import AITask, AIProviderError
from app.services.ai.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    GENERATION_SYSTEM_PROMPT,
    PLANNING_SYSTEM_PROMPT,
    REPAIR_SYSTEM_PROMPT,
    build_analysis_prompt,
    build_generation_prompt,
    build_planning_prompt,
    build_repair_prompt,
)
from app.services.ai.router import AITaskRouter
from app.services.ai.validator import CodeValidator

logger = logging.getLogger(__name__)


class BuildWorker:
    """
    Background build worker orchestrating the multi-provider website generation pipeline.
    """

    def __init__(
        self,
        router: Optional[AITaskRouter] = None,
        storage: Optional[ArtifactStorage] = None,
        validator: Optional[CodeValidator] = None,
    ):
        self.router = router or AITaskRouter()
        self.storage = storage or ArtifactStorage()
        self.validator = validator or CodeValidator()

    async def process_build(self, build_id: str, db: AsyncSession) -> WebsiteBuild:
        """
        Execute the complete multi-stage AI website build pipeline for a WebsiteBuild record.
        """
        # 1. Fetch and claim build
        stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id)
        result = await db.execute(stmt)
        build = result.scalar_one_or_none()

        if not build:
            raise ValueError(f"WebsiteBuild '{build_id}' not found.")

        # Ensure build can be processed
        if build.status not in (BuildStatus.QUEUED, BuildStatus.FAILED):
            logger.info("Build '%s' is in status '%s', skipping duplicate execution.", build_id, build.status.value)
            return build

        providers_used: Dict[str, str] = {}

        try:
            # 2. Stage 1: ANALYZING
            logger.info("Build %s: Entering ANALYZING stage", build_id)
            build.status = BuildStatus.ANALYZING
            await db.commit()
            await db.refresh(build)

            # Build rich AI context
            project_context = await build_project_ai_context(
                project_id=build.project_id,
                db=db,
                revision_id=build.revision_id,
            )

            # AI Analysis Task
            analysis_prompt = build_analysis_prompt(project_context)
            analysis_result, analysis_provider = await self.router.execute_task_structured(
                task=AITask.ANALYSIS,
                prompt=analysis_prompt,
                schema=WebsiteAnalysisResult,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
            )
            providers_used["analysis"] = analysis_provider
            build.spec_data = analysis_result.model_dump()

            # AI Planning Task
            planning_prompt = build_planning_prompt(project_context, build.spec_data)
            plan_result, plan_provider = await self.router.execute_task_structured(
                task=AITask.PLANNING,
                prompt=planning_prompt,
                schema=WebsitePlanResult,
                system_prompt=PLANNING_SYSTEM_PROMPT,
            )
            providers_used["planning"] = plan_provider
            build.architecture_data = plan_result.model_dump()
            build.design_system = plan_result.color_palette or analysis_result.design_system

            await db.commit()
            await db.refresh(build)

            # 3. Stage 2: GENERATING
            logger.info("Build %s: Entering GENERATING stage", build_id)
            build.status = BuildStatus.GENERATING
            await db.commit()
            await db.refresh(build)

            gen_prompt = build_generation_prompt(
                project_context=project_context,
                analysis_data=build.spec_data,
                plan_data=build.architecture_data,
            )

            website, gen_provider = await self.router.execute_task_structured(
                task=AITask.WEBSITE_GENERATION,
                prompt=gen_prompt,
                schema=GeneratedWebsite,
                system_prompt=GENERATION_SYSTEM_PROMPT,
            )
            providers_used["generation"] = gen_provider

            # 4. Stage 3: VALIDATING
            logger.info("Build %s: Validating generated files", build_id)
            val_result = self.validator.validate_website(website)

            # Attempt repair if validation failed
            if not val_result.is_valid and settings.AI_REPAIR_ENABLED:
                logger.warning("Build %s: Validation failed with %d errors. Attempting AI repair.", build_id, len(val_result.findings))
                repair_prompt = build_repair_prompt(
                    validation_findings=val_result.findings,
                    previous_files=website.files,
                )
                try:
                    repaired_website, repair_provider = await self.router.execute_task_structured(
                        task=AITask.REPAIR,
                        prompt=repair_prompt,
                        schema=GeneratedWebsite,
                        system_prompt=REPAIR_SYSTEM_PROMPT,
                    )
                    providers_used["repair"] = repair_provider
                    reval_result = self.validator.validate_website(repaired_website)
                    if reval_result.is_valid or reval_result.score > val_result.score:
                        website = repaired_website
                        val_result = reval_result
                except Exception as repair_err:
                    logger.warning("Repair task failed: %s", repair_err)

            # If still invalid after repair attempts
            if not val_result.is_valid:
                error_messages = "; ".join([f"{f.file_path}: {f.message}" for f in val_result.findings if f.severity == "ERROR"])
                build.status = BuildStatus.FAILED
                build.admin_notes = (build.admin_notes or "") + f"\nValidation Failed: {error_messages}"
                await db.commit()
                await db.refresh(build)
                return build

            # 5. Stage 4: STORAGE & COMPLETION
            logger.info("Build %s: Writing verified website artifacts to isolated storage", build_id)
            storage_path = self.storage.save_build(
                project_id=build.project_id,
                build_id=build.id,
                version_number=build.version_number,
                website=website,
                providers_used=providers_used,
                spec_summary={
                    "page_count": len(website.files),
                    "validation_score": val_result.score,
                    "website_type": build.spec_data.get("website_type") if build.spec_data else "Static Website",
                },
            )

            build.generated_code_path = storage_path
            build.status = BuildStatus.COMPLETED
            build.is_active = True

            # Also log ProjectActivity
            activity = ProjectActivity(
                project_id=build.project_id,
                action_type="BUILD_COMPLETED",
                note=f"AI Website Build v{build.version_number} completed. Providers: {providers_used}. Validation score: {val_result.score}%.",
                is_visible_to_client=True,
            )
            db.add(activity)

            await db.commit()
            await db.refresh(build)
            logger.info("Build %s successfully COMPLETED at %s", build_id, storage_path)
            return build

        except Exception as exc:
            logger.exception("Build %s encountered fatal error during processing: %s", build_id, exc)
            build.status = BuildStatus.FAILED
            build.admin_notes = (build.admin_notes or "") + f"\nBuild Error: {str(exc)}"
            await db.commit()
            await db.refresh(build)
            return build
