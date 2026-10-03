from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.models.activity import ProjectActivity
from app.models.customer import Customer
from app.models.deployment import Deployment
from app.models.enums import BuildReviewStatus, BuildStatus, PaymentStatus, ProjectStatus, RevisionStatus, UserRole
from app.models.payment import Payment
from app.models.pricing_package import PricingPackage
from app.models.project import Project
from app.models.revision import Revision
from app.models.user import User
from app.models.website_build import WebsiteBuild
from app.schemas.common import APIResponse
from app.schemas.deployment import DeploymentResponse
from app.schemas.pricing import PricingPackageResponse
from app.schemas.project import (
    ActivityItemResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
)
from app.schemas.website_build import (
    ClientBuildApprovalRequest,
    ClientBuildPreviewResponse,
    ClientRevisionCreateRequest,
    WebsiteBuildResponse,
)
from app.services.ai.artifact_storage import ArtifactStorage

router = APIRouter()


async def get_or_create_customer(user: User, db: AsyncSession) -> Customer:
    """Helper to ensure authenticated user has an associated Customer record."""
    if user.customer_profile:
        return user.customer_profile

    stmt = select(Customer).where(Customer.user_id == user.id)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if customer:
        return customer

    # Create new customer profile if missing
    new_customer = Customer(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone or "",
        company_name=None,
    )
    db.add(new_customer)
    await db.flush()
    return new_customer


@router.get(
    "",
    response_model=APIResponse[List[ProjectResponse]],
    summary="List customer websites and projects",
)
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all projects belonging to the authenticated customer."""
    customer = await get_or_create_customer(current_user, db)

    stmt = (
        select(Project)
        .options(selectinload(Project.package))
        .where(Project.customer_id == customer.id)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()

    return APIResponse(
        success=True,
        message="Projects retrieved.",
        data=[ProjectResponse.model_validate(p) for p in projects],
    )


@router.post(
    "",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Start a new website project",
)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Commission a new website/project."""
    customer = await get_or_create_customer(current_user, db)

    # Validate package_id if provided (ensure package exists and is active)
    if project_in.package_id:
        pkg_stmt = select(PricingPackage).where(
            PricingPackage.id == project_in.package_id,
            PricingPackage.is_active == True,  # noqa: E712
        )
        pkg_res = await db.execute(pkg_stmt)
        pkg = pkg_res.scalar_one_or_none()
        if not pkg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected package not found or is no longer active.",
            )

    # Generate sequential human-readable project number
    count_stmt = select(func.count(Project.id))
    total_count = (await db.execute(count_stmt)).scalar() or 0
    project_number = f"PRJ-2026-{total_count + 1:03d}"

    new_project = Project(
        project_number=project_number,
        customer_id=customer.id,
        package_id=project_in.package_id,
        title=project_in.title.strip(),
        business_name=project_in.business_name.strip(),
        status=ProjectStatus.NEW,
    )
    db.add(new_project)
    await db.flush()

    # Log initial activity in audit timeline
    initial_activity = ProjectActivity(
        project_id=new_project.id,
        performed_by_user_id=current_user.id,
        action_type="PROJECT_CREATED",
        new_status=ProjectStatus.NEW.value,
        note=f"Project commissioned by {current_user.full_name}",
        is_visible_to_client=True,
    )
    db.add(initial_activity)

    await db.commit()

    # Reload with package relationship
    reload_stmt = (
        select(Project)
        .options(selectinload(Project.package))
        .where(Project.id == new_project.id)
    )
    loaded_project = (await db.execute(reload_stmt)).scalar_one()

    return APIResponse(
        success=True,
        message="Project initiated successfully! Our studio team will review your requirements.",
        data=ProjectResponse.model_validate(loaded_project),
    )


@router.get(
    "/{project_id}",
    response_model=APIResponse[ProjectDetailResponse],
    summary="Get single project details and activity timeline",
)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a single project with strict ownership enforcement."""
    customer = await get_or_create_customer(current_user, db)

    stmt = (
        select(Project)
        .options(
            selectinload(Project.activities),
            selectinload(Project.package),
        )
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Strict server-side ownership boundary: Customer can only access their own project
    if current_user.role == UserRole.CUSTOMER and project.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project",
        )

    # Filter visible activities for customer
    visible_activities = [
        ActivityItemResponse.model_validate(a)
        for a in project.activities
        if a.is_visible_to_client or current_user.role != UserRole.CUSTOMER
    ]

    detail = ProjectDetailResponse(
        id=project.id,
        project_number=project.project_number,
        customer_id=project.customer_id,
        package_id=project.package_id,
        package=PricingPackageResponse.model_validate(project.package) if project.package else None,
        title=project.title,
        business_name=project.business_name,
        status=project.status,
        preview_url=project.preview_url,
        production_url=project.production_url,
        custom_domain=project.custom_domain,
        revisions_used=project.revisions_used,
        created_at=project.created_at,
        updated_at=project.updated_at,
        activities=visible_activities,
    )

    return APIResponse(
        success=True,
        message="Project details retrieved.",
        data=detail,
    )


@router.get(
    "/{project_id}/builds",
    response_model=APIResponse[List[WebsiteBuildResponse]],
    summary="List approved builds for project (customer)",
)
async def list_customer_builds(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List approved website builds accessible to customer."""
    customer = await get_or_create_customer(current_user, db)
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CUSTOMER and project.customer_id != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    build_query = select(WebsiteBuild).where(WebsiteBuild.project_id == project_id)
    if current_user.role == UserRole.CUSTOMER:
        build_query = build_query.where(
            WebsiteBuild.status == BuildStatus.COMPLETED,
            WebsiteBuild.review_status == BuildReviewStatus.APPROVED,
        )
    build_query = build_query.order_by(WebsiteBuild.version_number.desc())
    builds = (await db.execute(build_query)).scalars().all()

    return APIResponse(
        success=True,
        message="Builds retrieved.",
        data=[WebsiteBuildResponse.model_validate(b) for b in builds],
    )


@router.get(
    "/{project_id}/builds/{build_id}/preview",
    response_model=APIResponse[ClientBuildPreviewResponse],
    summary="Client preview metadata for an approved website build",
)
async def get_client_build_preview(
    project_id: str,
    build_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve safe client-facing preview metadata for an approved website build."""
    customer = await get_or_create_customer(current_user, db)

    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CUSTOMER and project.customer_id != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    build_stmt = select(WebsiteBuild).where(
        WebsiteBuild.id == build_id,
        WebsiteBuild.project_id == project_id,
    )
    build = (await db.execute(build_stmt)).scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website build not found")

    if current_user.role == UserRole.CUSTOMER:
        if build.status != BuildStatus.COMPLETED or build.review_status != BuildReviewStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This website build is still undergoing internal review and is not yet available for client preview.",
            )

    storage = ArtifactStorage(settings.ARTIFACT_STORAGE_PATH)
    artifact_dir = storage.get_build_dir(project_id, build.version_number)
    file_count = len(list(artifact_dir.rglob("*"))) if artifact_dir.exists() else 0

    return APIResponse(
        success=True,
        message="Build preview details retrieved.",
        data=ClientBuildPreviewResponse(
            project_id=project.id,
            project_title=project.title,
            build_id=build.id,
            version_number=build.version_number,
            status=build.status,
            review_status=build.review_status,
            client_approved=build.client_approved,
            client_approved_at=build.client_approved_at,
            preview_url=f"/api/v1/projects/{project_id}/builds/{build_id}/preview-sandbox",
            entry_file="index.html",
            files_count=file_count,
            created_at=build.created_at,
        ),
    )


@router.get(
    "/{project_id}/builds/{build_id}/preview-sandbox",
    response_class=HTMLResponse,
    summary="Client sandboxed HTML preview with strict security isolation",
)
async def get_client_preview_sandbox(
    project_id: str,
    build_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Serve generated website HTML in a secure sandbox with disabled scripts and CSP isolation."""
    customer = await get_or_create_customer(current_user, db)

    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CUSTOMER and project.customer_id != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    build_stmt = select(WebsiteBuild).where(
        WebsiteBuild.id == build_id,
        WebsiteBuild.project_id == project_id,
    )
    build = (await db.execute(build_stmt)).scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website build not found")

    if current_user.role == UserRole.CUSTOMER:
        if build.status != BuildStatus.COMPLETED or build.review_status != BuildReviewStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This website build is still undergoing internal review and is not ready for client preview.",
            )

    storage = ArtifactStorage(settings.ARTIFACT_STORAGE_PATH)
    artifact_dir = storage.get_build_dir(project_id, build.version_number)
    entry_file = artifact_dir / "index.html"

    if not entry_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website entry file index.html is missing for this build.",
        )

    try:
        content = entry_file.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to read preview file: {str(e)}")

    headers = {
        "Content-Security-Policy": (
            "default-src 'self' 'unsafe-inline' https: data:; "
            "script-src 'none'; "
            "object-src 'none'; "
            "frame-ancestors 'self' http://localhost:3000 http://127.0.0.1:3000;"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
    }

    return HTMLResponse(content=content, status_code=200, headers=headers)


@router.post(
    "/{project_id}/builds/{build_id}/approve",
    response_model=APIResponse[WebsiteBuildResponse],
    summary="Client final approval on website build",
)
async def approve_client_build(
    project_id: str,
    build_id: str,
    payload: ClientBuildApprovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Customer explicitly approves the generated website build, advancing to remaining payment or deployment."""
    customer = await get_or_create_customer(current_user, db)

    stmt = select(Project).options(selectinload(Project.package), selectinload(Project.payments)).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CUSTOMER and project.customer_id != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    build_stmt = select(WebsiteBuild).where(
        WebsiteBuild.id == build_id,
        WebsiteBuild.project_id == project_id,
    )
    build = (await db.execute(build_stmt)).scalar_one_or_none()
    if not build:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website build not found")

    if build.status != BuildStatus.COMPLETED or build.review_status != BuildReviewStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only admin-approved completed website builds can receive client final approval.",
        )

    # Set client approval state
    build.client_approved = True
    build.client_approved_at = datetime.now(timezone.utc)
    if payload.feedback:
        build.client_feedback = payload.feedback

    # Check remaining payment balance
    package_price = float(project.package.price_inr) if project.package else 0.0
    total_paid = sum(float(p.amount_inr) for p in (project.payments or []) if p.status == PaymentStatus.SUCCESS)
    remaining_balance = max(0.0, package_price - total_paid)

    old_status = project.status.value
    if remaining_balance <= 0.01:
        # Full payment already settled; project becomes APPROVED (deployment ready)
        project.status = ProjectStatus.APPROVED
        note_text = f"Client approved build v{build.version_number}. Full payment settled (₹{total_paid:,.2f}). Project is ready for production deployment."
    else:
        # Remaining balance is required before live production deployment
        project.status = ProjectStatus.PAYMENT_PENDING
        note_text = f"Client approved build v{build.version_number}. Remaining payment of ₹{remaining_balance:,.2f} is required before live deployment."

    activity = ProjectActivity(
        project_id=project.id,
        performed_by_user_id=current_user.id,
        action_type="CLIENT_BUILD_APPROVED",
        old_status=old_status,
        new_status=project.status.value,
        note=note_text,
        is_visible_to_client=True,
    )
    db.add(activity)

    await db.commit()
    await db.refresh(build)

    return APIResponse(
        success=True,
        message=note_text,
        data=WebsiteBuildResponse.model_validate(build),
    )


@router.get(
    "/{project_id}/deployments",
    response_model=APIResponse[List[DeploymentResponse]],
    summary="List deployments for a project",
)
async def list_project_deployments(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve production deployment history for a project."""
    customer = await get_or_create_customer(current_user, db)

    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CUSTOMER and project.customer_id != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    dep_stmt = (
        select(Deployment)
        .where(Deployment.project_id == project_id)
        .order_by(Deployment.created_at.desc())
    )
    deployments = (await db.execute(dep_stmt)).scalars().all()

    return APIResponse(
        success=True,
        message="Deployments retrieved.",
        data=[DeploymentResponse.model_validate(d) for d in deployments],
    )

