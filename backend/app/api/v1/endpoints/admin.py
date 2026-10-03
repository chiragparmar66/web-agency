"""
Internal Developer & Admin Studio Console Endpoints.
Provides pipeline oversight, project lifecycle updates, developer assignments,
preview/production URL configuration, and lead/inquiry CRM management.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_roles
from app.core.config import settings
from app.db.session import async_session_factory
from app.services.ai.artifact_storage import ArtifactStorage
from app.services.ai.build_worker import BuildWorker
from app.models.activity import ProjectActivity
from app.models.customer import Customer
from app.models.deployment import Deployment
from app.models.enums import (
    BuildReviewStatus,
    BuildStatus,
    DeploymentStatus,
    InquiryStatus,
    PaymentStatus,
    PaymentType,
    ProjectStatus,
    UserRole,
)
from app.models.inquiry import Inquiry
from app.models.payment import Payment
from app.models.project import Project
from app.models.pricing_package import PricingPackage
from app.models.revision import Revision
from app.models.user import User
from app.models.website_build import WebsiteBuild
from app.schemas.admin import (
    AdminCustomerSummary,
    AdminInquiryUpdate,
    AdminOverviewResponse,
    AdminProjectResponse,
    AdminProjectUpdate,
    StaffUserResponse,
)
from app.schemas.common import APIResponse
from app.schemas.deployment import (
    DeploymentEligibilityResponse,
    DeploymentResponse,
    DeploymentTriggerRequest,
)
from app.schemas.inquiry import InquiryResponse
from app.schemas.website_build import (
    BuildApprovalRequest,
    BuildApprovalResponse,
    BuildFileContentResponse,
    BuildFileItem,
    BuildRebuildRequest,
    BuildReviewApproveRequest,
    BuildReviewDetailResponse,
    BuildReviewRejectRequest,
    ProjectAIContextResponse,
    WebsiteBuildResponse,
)
from app.services.ai_context import build_project_ai_context
from app.services.deployment import DeploymentService

router = APIRouter()


@router.get(
    "/overview",
    response_model=APIResponse[dict],
    summary="Admin System Overview",
)
async def admin_overview(
    admin_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only overview endpoint protected by server-side RBAC."""
    user_count_stmt = select(func.count(User.id))
    user_count = (await db.execute(user_count_stmt)).scalar() or 0

    project_count_stmt = select(func.count(Project.id))
    project_count = (await db.execute(project_count_stmt)).scalar() or 0

    active_count_stmt = select(func.count(Project.id)).where(
        Project.status.notin_([ProjectStatus.COMPLETED, ProjectStatus.LIVE])
    )
    active_count = (await db.execute(active_count_stmt)).scalar() or 0

    inquiry_count_stmt = select(func.count(Inquiry.id))
    inquiry_count = (await db.execute(inquiry_count_stmt)).scalar() or 0

    return APIResponse(
        success=True,
        message="Admin overview accessed.",
        data={
            "admin_email": admin_user.email,
            "total_users": user_count,
            "total_projects": project_count,
            "active_projects": active_count,
            "total_inquiries": inquiry_count,
            "system_status": "operational",
        },
    )


@router.get(
    "/projects",
    response_model=APIResponse[List[AdminProjectResponse]],
    summary="List all projects for studio console",
)
async def list_admin_projects(
    status_filter: Optional[ProjectStatus] = Query(None, alias="status"),
    assigned_developer_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """
    List all customer projects across the studio platform.
    Allows staff to monitor pipelines, filter by status, or filter by assigned developer.
    """
    stmt = (
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.assigned_developer),
            selectinload(Project.package),
            selectinload(Project.payments),
        )
        .order_by(Project.created_at.desc())
    )

    if status_filter:
        stmt = stmt.where(Project.status == status_filter)
    if assigned_developer_id:
        stmt = stmt.where(Project.assigned_developer_id == assigned_developer_id)

    result = await db.execute(stmt)
    projects = result.scalars().all()

    formatted_projects = []
    for p in projects:
        customer_summary = None
        if p.customer:
            customer_summary = AdminCustomerSummary(
                id=p.customer.id,
                full_name=p.customer.full_name,
                email=p.customer.email,
                phone=p.customer.phone,
                company_name=p.customer.company_name,
            )

        dev_summary = None
        if p.assigned_developer:
            dev_summary = StaffUserResponse(
                id=p.assigned_developer.id,
                full_name=p.assigned_developer.full_name,
                email=p.assigned_developer.email,
                phone=p.assigned_developer.phone,
                role=p.assigned_developer.role,
                is_active=p.assigned_developer.is_active,
            )

        has_advance = any(
            pay.status == PaymentStatus.SUCCESS and pay.payment_type in [PaymentType.ADVANCE, PaymentType.FULL]
            for pay in (p.payments or [])
        )
        total_paid = sum(
            float(pay.amount_inr) for pay in (p.payments or [])
            if pay.status == PaymentStatus.SUCCESS
        )

        formatted_projects.append(
            AdminProjectResponse(
                id=p.id,
                project_number=p.project_number,
                customer_id=p.customer_id,
                package_id=p.package_id,
                title=p.title,
                business_name=p.business_name,
                status=p.status,
                revisions_used=p.revisions_used,
                preview_url=p.preview_url,
                production_url=p.production_url,
                custom_domain=p.custom_domain,
                assigned_developer_id=p.assigned_developer_id,
                created_at=p.created_at,
                updated_at=p.updated_at,
                customer=customer_summary,
                assigned_developer=dev_summary,
                package_name=p.package.name if p.package else None,
                advance_payment_status="PAID" if has_advance else "PENDING",
                total_paid_inr=total_paid,
            )
        )

    return APIResponse(
        success=True,
        message="Studio projects retrieved.",
        data=formatted_projects,
    )


@router.get(
    "/projects/{project_id}",
    response_model=APIResponse[AdminProjectResponse],
    summary="Get single project detail for studio console",
)
async def get_admin_project(
    project_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full project detail with customer, assigned developer, and package."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.assigned_developer),
            selectinload(Project.package),
            selectinload(Project.payments),
        )
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    customer_summary = None
    if project.customer:
        customer_summary = AdminCustomerSummary(
            id=project.customer.id,
            full_name=project.customer.full_name,
            email=project.customer.email,
            phone=project.customer.phone,
            company_name=project.customer.company_name,
        )

    dev_summary = None
    if project.assigned_developer:
        dev_summary = StaffUserResponse(
            id=project.assigned_developer.id,
            full_name=project.assigned_developer.full_name,
            email=project.assigned_developer.email,
            phone=project.assigned_developer.phone,
            role=project.assigned_developer.role,
            is_active=project.assigned_developer.is_active,
        )

    has_advance = any(
        pay.status == PaymentStatus.SUCCESS and pay.payment_type in [PaymentType.ADVANCE, PaymentType.FULL]
        for pay in (project.payments or [])
    )
    total_paid = sum(
        float(pay.amount_inr) for pay in (project.payments or [])
        if pay.status == PaymentStatus.SUCCESS
    )

    return APIResponse(
        success=True,
        message="Project details retrieved.",
        data=AdminProjectResponse(
            id=project.id,
            project_number=project.project_number,
            customer_id=project.customer_id,
            package_id=project.package_id,
            title=project.title,
            business_name=project.business_name,
            status=project.status,
            revisions_used=project.revisions_used,
            preview_url=project.preview_url,
            production_url=project.production_url,
            custom_domain=project.custom_domain,
            assigned_developer_id=project.assigned_developer_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            customer=customer_summary,
            assigned_developer=dev_summary,
            package_name=project.package.name if project.package else None,
            advance_payment_status="PAID" if has_advance else "PENDING",
            total_paid_inr=total_paid,
        ),
    )


@router.patch(
    "/projects/{project_id}",
    response_model=APIResponse[AdminProjectResponse],
    summary="Update project status, developer assignment, and URLs",
)
async def update_admin_project(
    project_id: str,
    payload: AdminProjectUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """
    Staff update for project status, developer assignment, and staging/production URLs.
    Logs audit activity events for every change.
    """
    stmt = (
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.assigned_developer),
            selectinload(Project.package),
        )
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # 1. Update status
    if payload.status is not None and payload.status != project.status:
        old_status = project.status.value
        project.status = payload.status
        activity = ProjectActivity(
            project_id=project_id,
            performed_by_user_id=current_user.id,
            action_type="STATUS_CHANGED",
            old_status=old_status,
            new_status=payload.status.value,
            note=f"Project status changed from {old_status} to {payload.status.value} by {current_user.full_name}",
            is_visible_to_client=True,
        )
        db.add(activity)

    # 2. Update developer assignment
    if payload.assigned_developer_id is not None:
        if payload.assigned_developer_id == "":
            project.assigned_developer_id = None
            project.assigned_developer = None
            activity = ProjectActivity(
                project_id=project_id,
                performed_by_user_id=current_user.id,
                action_type="DEVELOPER_UNASSIGNED",
                note="Assigned developer removed",
                is_visible_to_client=False,
            )
            db.add(activity)
        else:
            dev_stmt = select(User).where(User.id == payload.assigned_developer_id)
            dev_res = await db.execute(dev_stmt)
            target_dev = dev_res.scalar_one_or_none()
            if not target_dev or target_dev.role not in [UserRole.ADMIN, UserRole.DEVELOPER]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned user must be an active Developer or Admin.",
                )
            project.assigned_developer_id = target_dev.id
            project.assigned_developer = target_dev
            activity = ProjectActivity(
                project_id=project_id,
                performed_by_user_id=current_user.id,
                action_type="DEVELOPER_ASSIGNED",
                note=f"Developer {target_dev.full_name} assigned to project",
                is_visible_to_client=False,
            )
            db.add(activity)

    # 3. Update preview URL
    if payload.preview_url is not None:
        project.preview_url = payload.preview_url.strip() if payload.preview_url else None
        if project.preview_url:
            activity = ProjectActivity(
                project_id=project_id,
                performed_by_user_id=current_user.id,
                action_type="PREVIEW_URL_UPDATED",
                note=f"Staging preview URL updated: {project.preview_url}",
                is_visible_to_client=True,
            )
            db.add(activity)

    # 4. Update production URL
    if payload.production_url is not None:
        project.production_url = payload.production_url.strip() if payload.production_url else None
        if project.production_url:
            activity = ProjectActivity(
                project_id=project_id,
                performed_by_user_id=current_user.id,
                action_type="PRODUCTION_URL_UPDATED",
                note=f"Production URL updated: {project.production_url}",
                is_visible_to_client=True,
            )
            db.add(activity)

    # 5. Update custom domain
    if payload.custom_domain is not None:
        project.custom_domain = payload.custom_domain.strip().lower() if payload.custom_domain else None

    await db.commit()

    # Re-fetch with fresh relationships
    reload_stmt = (
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.assigned_developer),
            selectinload(Project.package),
            selectinload(Project.payments),
        )
        .where(Project.id == project_id)
    )
    reload_res = await db.execute(reload_stmt)
    updated_project = reload_res.scalar_one()

    customer_summary = None
    if updated_project.customer:
        customer_summary = AdminCustomerSummary(
            id=updated_project.customer.id,
            full_name=updated_project.customer.full_name,
            email=updated_project.customer.email,
            phone=updated_project.customer.phone,
            company_name=updated_project.customer.company_name,
        )

    dev_summary = None
    if updated_project.assigned_developer:
        dev_summary = StaffUserResponse(
            id=updated_project.assigned_developer.id,
            full_name=updated_project.assigned_developer.full_name,
            email=updated_project.assigned_developer.email,
            phone=updated_project.assigned_developer.phone,
            role=updated_project.assigned_developer.role,
            is_active=updated_project.assigned_developer.is_active,
        )

    has_advance = any(
        pay.status == PaymentStatus.SUCCESS and pay.payment_type in [PaymentType.ADVANCE, PaymentType.FULL]
        for pay in (updated_project.payments or [])
    )
    total_paid = sum(
        float(pay.amount_inr) for pay in (updated_project.payments or [])
        if pay.status == PaymentStatus.SUCCESS
    )

    return APIResponse(
        success=True,
        message="Project updated successfully.",
        data=AdminProjectResponse(
            id=updated_project.id,
            project_number=updated_project.project_number,
            customer_id=updated_project.customer_id,
            package_id=updated_project.package_id,
            title=updated_project.title,
            business_name=updated_project.business_name,
            status=updated_project.status,
            revisions_used=updated_project.revisions_used,
            preview_url=updated_project.preview_url,
            production_url=updated_project.production_url,
            custom_domain=updated_project.custom_domain,
            assigned_developer_id=updated_project.assigned_developer_id,
            created_at=updated_project.created_at,
            updated_at=updated_project.updated_at,
            customer=customer_summary,
            assigned_developer=dev_summary,
            package_name=updated_project.package.name if updated_project.package else None,
            advance_payment_status="PAID" if has_advance else "PENDING",
            total_paid_inr=total_paid,
        ),
    )


@router.get(
    "/inquiries",
    response_model=APIResponse[List[InquiryResponse]],
    summary="List all inquiries for studio lead CRM",
)
async def list_admin_inquiries(
    status_filter: Optional[InquiryStatus] = Query(None, alias="status"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all leads/inquiries received through website forms and WhatsApp."""
    stmt = select(Inquiry).order_by(Inquiry.created_at.desc())
    if status_filter:
        stmt = stmt.where(Inquiry.status == status_filter)

    result = await db.execute(stmt)
    inquiries = result.scalars().all()

    return APIResponse(
        success=True,
        message="Inquiries retrieved.",
        data=[InquiryResponse.model_validate(i) for i in inquiries],
    )


@router.patch(
    "/inquiries/{inquiry_id}",
    response_model=APIResponse[InquiryResponse],
    summary="Update inquiry CRM status",
)
async def update_admin_inquiry(
    inquiry_id: str,
    payload: AdminInquiryUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """Update lead status (NEW -> CONTACTED -> QUALIFIED -> CONVERTED -> CLOSED)."""
    stmt = select(Inquiry).where(Inquiry.id == inquiry_id)
    result = await db.execute(stmt)
    inquiry = result.scalar_one_or_none()

    if not inquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")

    if payload.status is not None:
        inquiry.status = payload.status
    if payload.is_read is not None:
        inquiry.read_at = datetime.now(timezone.utc) if payload.is_read else None

    await db.commit()
    await db.refresh(inquiry)

    return APIResponse(
        success=True,
        message=f"Inquiry status updated to {inquiry.status.value}.",
        data=InquiryResponse.model_validate(inquiry),
    )


@router.get(
    "/team",
    response_model=APIResponse[List[StaffUserResponse]],
    summary="List studio staff team members",
)
async def list_team_members(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """List studio developers and admins available for assignment."""
    stmt = (
        select(User)
        .where(User.role.in_([UserRole.ADMIN, UserRole.DEVELOPER]), User.is_active == True)  # noqa: E712
        .order_by(User.full_name.asc())
    )
    result = await db.execute(stmt)
    team = result.scalars().all()

    return APIResponse(
        success=True,
        message="Team members retrieved.",
        data=[StaffUserResponse.model_validate(u) for u in team],
    )


# ---------------------------------------------------------------------------
# Phase 10: AI Website Builder Foundation & Approval Endpoints
# ---------------------------------------------------------------------------


async def _execute_build_worker_task(build_id: str) -> None:
    """Safely process an AI website build in an isolated session."""
    async with async_session_factory() as session:
        try:
            worker = BuildWorker()
            await worker.process_build(build_id, session)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Background build processing failed for %s", build_id)


@router.post(
    "/projects/{project_id}/approve-build",
    response_model=APIResponse[BuildApprovalResponse],
    summary="Approve client request and start AI Website Build run",
)
async def approve_and_start_build(
    project_id: str,
    background_tasks: BackgroundTasks,
    payload: Optional[BuildApprovalRequest] = None,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin verification step:
    1. Validates project existence.
    2. Validates advance payment status (or waiver).
    3. Moves project status to BUILDING.
    4. Queues a versioned WebsiteBuild run.
    5. Dispatches background build worker if enabled.
    6. Logs project audit activity.
    """
    req = payload or BuildApprovalRequest()

    stmt = (
        select(Project)
        .options(
            selectinload(Project.package),
            selectinload(Project.payments),
            selectinload(Project.builds),
        )
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    # Verify advance payment unless bypassed
    is_waived = req.force_override_payment or bool(req.waive_payment)
    if not is_waived:
        has_completed_advance = any(
            p.status == PaymentStatus.SUCCESS and p.payment_type in [PaymentType.ADVANCE, PaymentType.FULL]
            for p in (project.payments or [])
        )
        # If project has a package with price > 0 and no advance payment is recorded
        if project.package and float(project.package.price_inr) > 0 and not has_completed_advance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Advance payment must be completed before approving and starting the AI build. Use waive_payment to bypass if authorized.",
            )

    # Determine next build version number
    version_count_stmt = select(func.count(WebsiteBuild.id)).where(WebsiteBuild.project_id == project_id)
    existing_count = (await db.execute(version_count_stmt)).scalar() or 0
    next_version = existing_count + 1

    # Deactivate existing active builds
    if project.builds:
        for b in project.builds:
            b.is_active = False

    # Create new queued build record
    new_build = WebsiteBuild(
        project_id=project.id,
        revision_id=req.revision_id,
        version_number=next_version,
        status=BuildStatus.QUEUED,
        admin_notes=req.admin_notes,
        is_active=True,
        approved_by_user_id=current_user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(new_build)

    # Update project status
    old_status = project.status.value
    project.status = ProjectStatus.BUILDING

    # Log audit activity
    activity = ProjectActivity(
        project_id=project.id,
        performed_by_user_id=current_user.id,
        action_type="BUILD_APPROVED",
        old_status=old_status,
        new_status=project.status.value,
        note=f"AI Website Build v{next_version} approved & queued by {current_user.full_name}."
        + (f" Note: {req.admin_notes}" if req.admin_notes else ""),
        is_visible_to_client=True,
    )
    db.add(activity)

    await db.commit()
    await db.refresh(new_build)
    await db.refresh(project)

    # Trigger background worker if AI generation is enabled
    if settings.AI_GENERATION_ENABLED:
        background_tasks.add_task(_execute_build_worker_task, new_build.id)

    return APIResponse(
        success=True,
        message=f"Project approved. AI Website Build v{next_version} queued successfully.",
        data=BuildApprovalResponse(
            success=True,
            message=f"Build v{next_version} queued.",
            build=WebsiteBuildResponse.model_validate(new_build),
            project_status=project.status,
        ),
    )


@router.post(
    "/projects/{project_id}/builds/{build_id}/process",
    response_model=APIResponse[WebsiteBuildResponse],
    summary="Trigger processing of an AI website build",
)
async def process_build_run(
    project_id: str,
    build_id: str,
    background_tasks: BackgroundTasks,
    sync: bool = Query(False, description="Run synchronously if True, else background task"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI website builder pipeline execution for a specific build."""
    stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    result = await db.execute(stmt)
    build = result.scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    if sync:
        worker = BuildWorker()
        build = await worker.process_build(build_id, db)
    else:
        background_tasks.add_task(_execute_build_worker_task, build.id)

    return APIResponse(
        success=True,
        message="Build processing initiated in background." if not sync else f"Build completed with status: {build.status.value}",
        data=WebsiteBuildResponse.model_validate(build),
    )


@router.get(
    "/projects/{project_id}/builds/{build_id}/manifest",
    response_model=APIResponse[dict],
    summary="Get manifest for a generated build artifact",
)
async def get_build_manifest(
    project_id: str,
    build_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    result = await db.execute(stmt)
    build = result.scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    storage = ArtifactStorage()
    manifest = storage.read_manifest(project_id, build.version_number)
    if not manifest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build manifest not found.")

    return APIResponse(
        success=True,
        message="Build manifest retrieved.",
        data=manifest.model_dump(),
    )


@router.get(
    "/projects/{project_id}/builds/{build_id}/files",
    summary="List files for a generated build artifact",
)
async def list_build_files(
    project_id: str,
    build_id: str,
    detailed: bool = Query(False, description="Return rich metadata if True, else list of paths"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    result = await db.execute(stmt)
    build = result.scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    storage = ArtifactStorage()
    if detailed:
        file_items = storage.list_files_metadata(project_id, build.version_number)
        return APIResponse(
            success=True,
            message="Detailed build files metadata retrieved.",
            data=[BuildFileItem(**item) for item in file_items],
        )

    files = storage.list_files(project_id, build.version_number)
    return APIResponse(
        success=True,
        message="Build files list retrieved.",
        data=files,
    )


@router.get(
    "/projects/{project_id}/builds/{build_id}/files/{file_path:path}",
    response_model=APIResponse[BuildFileContentResponse],
    summary="Safely read content of a generated file in build artifact",
)
async def get_build_file_content(
    project_id: str,
    build_id: str,
    file_path: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    result = await db.execute(stmt)
    build = result.scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    storage = ArtifactStorage()
    try:
        content, is_text, is_truncated, total_size = storage.read_file_safe(
            project_id=project_id,
            version_number=build.version_number,
            relative_path=file_path,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    if content is None and total_size == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{file_path}' not found in build.")

    ext = file_path.split(".")[-1].lower() if "." in file_path else "txt"

    return APIResponse(
        success=True,
        message="File content retrieved." if is_text else "Binary file metadata retrieved (text display unsupported).",
        data=BuildFileContentResponse(
            path=file_path,
            file_type=ext,
            size_bytes=total_size,
            content=content,
            is_text=is_text,
            is_truncated=is_truncated,
        ),
    )


@router.get(
    "/projects/{project_id}/builds/{build_id}/review",
    response_model=APIResponse[BuildReviewDetailResponse],
    summary="Get complete build review and audit information for admin inspection",
)
async def get_build_review(
    project_id: str,
    build_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(WebsiteBuild)
        .options(
            selectinload(WebsiteBuild.project),
            selectinload(WebsiteBuild.approved_by),
            selectinload(WebsiteBuild.reviewed_by),
        )
        .where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    )
    result = await db.execute(stmt)
    build = result.scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    storage = ArtifactStorage()
    manifest = storage.read_manifest(project_id, build.version_number)
    file_items = storage.list_files_metadata(project_id, build.version_number)
    total_size = sum(f["size_bytes"] for f in file_items)

    providers_used = manifest.providers_used if manifest else {}
    spec_summary = manifest.spec_summary if manifest else (build.spec_data or {})
    validation_score = float(spec_summary.get("validation_score", 100.0))
    entry_file = manifest.entry_file if manifest else "index.html"

    # Extract or compile validation findings
    findings = []
    if build.status == BuildStatus.FAILED and build.admin_notes:
        findings.append({
            "file_path": entry_file,
            "severity": "ERROR",
            "rule": "BUILD_FAILURE",
            "message": build.admin_notes,
        })
    elif spec_summary.get("findings"):
        findings = spec_summary.get("findings")
    elif build.spec_data and build.spec_data.get("findings"):
        findings = build.spec_data.get("findings")

    review_data = BuildReviewDetailResponse(
        project_id=project_id,
        project_title=build.project.title if build.project else "Project",
        build_id=build.id,
        version_number=build.version_number,
        status=build.status,
        review_status=build.review_status,
        review_notes=build.review_notes,
        is_active=build.is_active,
        created_at=build.created_at,
        approved_at=build.approved_at,
        reviewed_at=build.reviewed_at,
        reviewed_by_name=build.reviewed_by.full_name if build.reviewed_by else None,
        providers_used=providers_used,
        entry_file=entry_file,
        files_count=len(file_items),
        total_size_bytes=total_size,
        validation_score=validation_score,
        validation_findings=findings,
        spec_summary=build.spec_data or {},
        architecture_summary=build.architecture_data or {},
        generated_code_path=build.generated_code_path,
        admin_notes=build.admin_notes,
    )

    return APIResponse(
        success=True,
        message="Build review details retrieved.",
        data=review_data,
    )


@router.post(
    "/projects/{project_id}/builds/{build_id}/approve-review",
    response_model=APIResponse[WebsiteBuildResponse],
    summary="Admin marks generated build as approved after code inspection",
)
async def approve_build_review(
    project_id: str,
    build_id: str,
    payload: Optional[BuildReviewApproveRequest] = None,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    result = await db.execute(stmt)
    build = result.scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    if build.status != BuildStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve build in '{build.status.value}' state. Build must be COMPLETED.",
        )

    build.review_status = BuildReviewStatus.APPROVED
    if payload and payload.notes:
        build.review_notes = payload.notes
    build.reviewed_by_user_id = current_user.id
    build.reviewed_at = datetime.now(timezone.utc)

    activity = ProjectActivity(
        project_id=project_id,
        performed_by_user_id=current_user.id,
        action_type="BUILD_APPROVED_BY_ADMIN",
        note=f"AI Website Build v{build.version_number} approved by {current_user.full_name}."
        + (f" Notes: {payload.notes}" if payload and payload.notes else ""),
        is_visible_to_client=False,
    )
    db.add(activity)

    await db.commit()
    await db.refresh(build)

    return APIResponse(
        success=True,
        message=f"Build v{build.version_number} approved successfully.",
        data=WebsiteBuildResponse.model_validate(build),
    )


@router.post(
    "/projects/{project_id}/builds/{build_id}/reject-review",
    response_model=APIResponse[WebsiteBuildResponse],
    summary="Admin rejects a generated build with required reason",
)
async def reject_build_review(
    project_id: str,
    build_id: str,
    payload: BuildReviewRejectRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    result = await db.execute(stmt)
    build = result.scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    build.review_status = BuildReviewStatus.REJECTED
    build.review_notes = payload.reason
    build.reviewed_by_user_id = current_user.id
    build.reviewed_at = datetime.now(timezone.utc)

    activity = ProjectActivity(
        project_id=project_id,
        performed_by_user_id=current_user.id,
        action_type="BUILD_REJECTED_BY_ADMIN",
        note=f"AI Website Build v{build.version_number} rejected by {current_user.full_name}. Reason: {payload.reason}",
        is_visible_to_client=False,
    )
    db.add(activity)

    await db.commit()
    await db.refresh(build)

    return APIResponse(
        success=True,
        message=f"Build v{build.version_number} rejected.",
        data=WebsiteBuildResponse.model_validate(build),
    )


@router.post(
    "/projects/{project_id}/builds/{build_id}/rebuild",
    response_model=APIResponse[WebsiteBuildResponse],
    summary="Trigger a new build version preserving existing builds",
)
async def request_build_rebuild(
    project_id: str,
    build_id: str,
    background_tasks: BackgroundTasks,
    payload: Optional[BuildRebuildRequest] = None,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    result = await db.execute(stmt)
    existing_build = result.scalar_one_or_none()
    if not existing_build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    # Calculate next version
    version_count_stmt = select(func.count(WebsiteBuild.id)).where(WebsiteBuild.project_id == project_id)
    existing_count = (await db.execute(version_count_stmt)).scalar() or 0
    next_version = existing_count + 1

    # Deactivate existing active builds
    all_builds_stmt = select(WebsiteBuild).where(WebsiteBuild.project_id == project_id)
    all_builds = (await db.execute(all_builds_stmt)).scalars().all()
    for b in all_builds:
        b.is_active = False

    admin_directive = (payload.admin_notes if payload and payload.admin_notes else None) or existing_build.admin_notes

    new_build = WebsiteBuild(
        project_id=project_id,
        revision_id=existing_build.revision_id,
        version_number=next_version,
        status=BuildStatus.QUEUED,
        review_status=BuildReviewStatus.PENDING_REVIEW,
        admin_notes=admin_directive,
        is_active=True,
        approved_by_user_id=current_user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(new_build)

    activity = ProjectActivity(
        project_id=project_id,
        performed_by_user_id=current_user.id,
        action_type="BUILD_REBUILD_REQUESTED",
        note=f"Rebuild requested by {current_user.full_name}: queued Build v{next_version}."
        + (f" Directive: {admin_directive}" if admin_directive else ""),
        is_visible_to_client=False,
    )
    db.add(activity)

    await db.commit()
    await db.refresh(new_build)

    if settings.AI_GENERATION_ENABLED:
        background_tasks.add_task(_execute_build_worker_task, new_build.id)

    return APIResponse(
        success=True,
        message=f"Rebuild queued as Build v{next_version}.",
        data=WebsiteBuildResponse.model_validate(new_build),
    )


@router.get(
    "/projects/{project_id}/builds/{build_id}/sandbox-view",
    summary="Safely render generated HTML in an isolated response with script execution disabled",
)
async def view_build_sandbox(
    project_id: str,
    build_id: str,
    path: str = Query("index.html", description="Relative file path to view"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebsiteBuild).where(WebsiteBuild.id == build_id, WebsiteBuild.project_id == project_id)
    result = await db.execute(stmt)
    build = result.scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Build '{build_id}' not found.")

    storage = ArtifactStorage()
    try:
        content, is_text, _, _ = storage.read_file_safe(project_id, build.version_number, path)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{path}' not found.")

    media_type = "text/html"
    if path.endswith(".css"):
        media_type = "text/css"
    elif path.endswith(".js"):
        media_type = "text/javascript"

    headers = {
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data: https:; script-src 'none'; frame-ancestors 'self'",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
    }

    return Response(content=content, media_type=media_type, headers=headers)


@router.get(
    "/projects/{project_id}/builds",
    response_model=APIResponse[List[WebsiteBuildResponse]],
    summary="List all AI build versions for a project",
)
async def list_project_builds(
    project_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """List all AI website builds / versions associated with a project."""
    # Verify project exists
    p_check = await db.execute(select(Project.id).where(Project.id == project_id))
    if not p_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    stmt = (
        select(WebsiteBuild)
        .where(WebsiteBuild.project_id == project_id)
        .order_by(WebsiteBuild.version_number.desc())
    )
    result = await db.execute(stmt)
    builds = result.scalars().all()

    return APIResponse(
        success=True,
        message="Website builds retrieved.",
        data=[WebsiteBuildResponse.model_validate(b) for b in builds],
    )


@router.get(
    "/projects/{project_id}/ai-context",
    response_model=APIResponse[ProjectAIContextResponse],
    summary="Get aggregated AI context payload for internal AI website builder",
)
async def get_project_ai_context(
    project_id: str,
    revision_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns normalized structured data (client info, package, requirements, files, revisions)
    ready for consumption by the AI website generation engine.
    """
    try:
        context_data = await build_project_ai_context(project_id, db, revision_id=revision_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return APIResponse(
        success=True,
        message="Project AI context synthesized successfully.",
        data=ProjectAIContextResponse(**context_data),
    )


# ---------------------------------------------------------------------------
# Phase 14: Deployment Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/builds/{build_id}/deployment-eligibility",
    response_model=APIResponse[DeploymentEligibilityResponse],
    summary="Check if website build meets all 5 production deployment gates",
)
async def check_deployment_eligibility(
    project_id: str,
    build_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates all 5 gates required for production deployment."""
    stmt = (
        select(Project)
        .options(selectinload(Project.package), selectinload(Project.payments))
        .where(Project.id == project_id)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    build_stmt = select(WebsiteBuild).where(
        WebsiteBuild.id == build_id,
        WebsiteBuild.project_id == project_id,
    )
    build = (await db.execute(build_stmt)).scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website build not found")

    service = DeploymentService()
    eligibility = await service.check_eligibility(db, project, build)

    return APIResponse(
        success=True,
        message="Deployment eligibility evaluated.",
        data=eligibility,
    )


@router.post(
    "/projects/{project_id}/builds/{build_id}/deploy",
    response_model=APIResponse[DeploymentResponse],
    summary="Trigger production deployment for an approved website build",
)
async def deploy_website_build(
    project_id: str,
    build_id: str,
    payload: Optional[DeploymentTriggerRequest] = None,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin triggers production deployment.
    Backend evaluates all 5 security gates strictly:
    1. Build status is COMPLETED
    2. Admin review status is APPROVED
    3. Client has given final approval
    4. Remaining payment is 100% cleared
    5. Artifact folder exists and passes safety checks
    """
    stmt = (
        select(Project)
        .options(selectinload(Project.package), selectinload(Project.payments))
        .where(Project.id == project_id)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    build_stmt = select(WebsiteBuild).where(
        WebsiteBuild.id == build_id,
        WebsiteBuild.project_id == project_id,
    )
    build = (await db.execute(build_stmt)).scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website build not found")

    service = DeploymentService()
    provider_name = payload.provider if payload else None
    notes = payload.notes if payload else None

    deployment = await service.deploy_build(
        db=db,
        project=project,
        build=build,
        user_id=current_user.id,
        provider_name=provider_name,
        notes=notes,
    )

    msg = (
        f"Website successfully deployed live to {deployment.live_url}"
        if deployment.status == DeploymentStatus.DEPLOYED
        else f"Deployment failed: {deployment.error_message}"
    )

    return APIResponse(
        success=(deployment.status == DeploymentStatus.DEPLOYED),
        message=msg,
        data=DeploymentResponse.model_validate(deployment),
    )


@router.get(
    "/projects/{project_id}/deployments",
    response_model=APIResponse[List[DeploymentResponse]],
    summary="List all deployments for a project (Admin)",
)
async def admin_list_project_deployments(
    project_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint to view complete deployment audit history for a project."""
    p_check = await db.execute(select(Project.id).where(Project.id == project_id))
    if not p_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    stmt = (
        select(Deployment)
        .where(Deployment.project_id == project_id)
        .order_by(Deployment.created_at.desc())
    )
    deployments = (await db.execute(stmt)).scalars().all()

    return APIResponse(
        success=True,
        message="Deployments retrieved.",
        data=[DeploymentResponse.model_validate(d) for d in deployments],
    )


