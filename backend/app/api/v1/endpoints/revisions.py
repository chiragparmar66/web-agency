"""
Revision Management System Endpoints.
Handles client revision requests, sequential revision numbering,
package revision quotas, attachment linking, developer/admin status management,
and audit timeline activity logging.
"""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.activity import ProjectActivity
from app.models.customer import Customer
from app.models.enums import FileCategory, ProjectStatus, RevisionStatus, UserRole
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.pricing_package import PricingPackage
from app.models.revision import Revision
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.revision import RevisionCreate, RevisionResponse, RevisionUpdate

router = APIRouter()


async def check_project_access(
    project_id: str,
    current_user: User,
    db: AsyncSession,
) -> Project:
    """
    Verify authenticated user has permission to access the project.
    Customers are strictly limited to their own projects.
    Staff (Admin/Developer) can access any project.
    """
    stmt = (
        select(Project)
        .options(selectinload(Project.package))
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if current_user.role == UserRole.CUSTOMER:
        cust_stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust_result = await db.execute(cust_stmt)
        customer = cust_result.scalar_one_or_none()

        if not customer or project.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this project",
            )

    return project


@router.post(
    "",
    response_model=APIResponse[RevisionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a revision request",
)
async def create_revision(
    project_id: str,
    rev_in: RevisionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new revision request for a project.
    Enforces revision quotas according to the chosen package,
    generates sequential revision numbers, links attachment files,
    updates project status to REVISION_REQUESTED, and records audit activity.
    """
    project = await check_project_access(project_id, current_user, db)

    # 1. Status eligibility: cannot request revisions before project requirements are submitted
    if project.status in {ProjectStatus.NEW, ProjectStatus.REQUIREMENTS_PENDING}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot request revisions before initial project requirements are submitted and development begins.",
        )

    # 2. Package revision quota check for customers
    if current_user.role == UserRole.CUSTOMER and project.package:
        if project.revisions_used >= project.package.revisions_included:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Revision limit reached ({project.package.revisions_included} "
                    f"revisions included in {project.package.name}). Please contact support for additional revisions."
                ),
            )

    # 3. Calculate sequential revision number
    count_stmt = select(func.count(Revision.id)).where(Revision.project_id == project_id)
    rev_count = (await db.execute(count_stmt)).scalar() or 0
    revision_number = rev_count + 1

    # 4. Create Revision record
    new_revision = Revision(
        project_id=project_id,
        revision_number=revision_number,
        requested_by_user_id=current_user.id,
        description=rev_in.description.strip(),
        status=RevisionStatus.PENDING,
    )
    db.add(new_revision)
    await db.flush()

    # 5. Link attachments if provided
    if rev_in.attachment_file_ids:
        files_stmt = select(ProjectFile).where(
            ProjectFile.id.in_(rev_in.attachment_file_ids),
            ProjectFile.project_id == project_id,
        )
        files_result = await db.execute(files_stmt)
        files = files_result.scalars().all()
        for f in files:
            f.revision_id = new_revision.id
            if f.file_category != FileCategory.REVISION_ATTACHMENT:
                f.file_category = FileCategory.REVISION_ATTACHMENT

    # 6. Update project revisions_used and lifecycle status
    old_status = project.status.value
    project.revisions_used = revision_number
    project.status = ProjectStatus.REVISION_REQUESTED

    # 7. Audit timeline logging
    summary_note = (
        f"Revision #{revision_number} requested by {current_user.full_name}: "
        f"{rev_in.description[:80]}..."
    )
    activity = ProjectActivity(
        project_id=project_id,
        performed_by_user_id=current_user.id,
        action_type="REVISION_REQUESTED",
        old_status=old_status,
        new_status=ProjectStatus.REVISION_REQUESTED.value,
        note=summary_note,
        is_visible_to_client=True,
    )
    db.add(activity)

    await db.commit()

    # Reload revision with attachments eager-loaded
    stmt_reload = (
        select(Revision)
        .options(selectinload(Revision.attachments))
        .where(Revision.id == new_revision.id)
    )
    res_reload = await db.execute(stmt_reload)
    full_revision = res_reload.scalar_one()

    return APIResponse(
        success=True,
        message=f"Revision #{revision_number} submitted successfully.",
        data=RevisionResponse.model_validate(full_revision),
    )


@router.get(
    "",
    response_model=APIResponse[List[RevisionResponse]],
    summary="List project revisions",
)
async def list_revisions(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all revisions submitted for a project, including attachments and status."""
    await check_project_access(project_id, current_user, db)

    stmt = (
        select(Revision)
        .options(selectinload(Revision.attachments))
        .where(Revision.project_id == project_id)
        .order_by(Revision.revision_number.asc())
    )
    result = await db.execute(stmt)
    revisions = result.scalars().all()

    return APIResponse(
        success=True,
        message="Revisions retrieved.",
        data=[RevisionResponse.model_validate(r) for r in revisions],
    )


@router.get(
    "/{revision_id}",
    response_model=APIResponse[RevisionResponse],
    summary="Get single revision detail",
)
async def get_revision(
    project_id: str,
    revision_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a single revision request."""
    await check_project_access(project_id, current_user, db)

    stmt = (
        select(Revision)
        .options(selectinload(Revision.attachments))
        .where(Revision.id == revision_id, Revision.project_id == project_id)
    )
    result = await db.execute(stmt)
    revision = result.scalar_one_or_none()

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision not found",
        )

    return APIResponse(
        success=True,
        message="Revision retrieved.",
        data=RevisionResponse.model_validate(revision),
    )


@router.patch(
    "/{revision_id}",
    response_model=APIResponse[RevisionResponse],
    summary="Update revision status & staff feedback (Staff Only)",
)
async def update_revision(
    project_id: str,
    revision_id: str,
    rev_update: RevisionUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
    db: AsyncSession = Depends(get_db),
):
    """
    Update revision status and resolution response.
    Accessible only to staff (Admin and Developer roles).
    Updates project lifecycle accordingly and logs audit timeline event.
    """
    project = await check_project_access(project_id, current_user, db)

    stmt = (
        select(Revision)
        .options(selectinload(Revision.attachments))
        .where(Revision.id == revision_id, Revision.project_id == project_id)
    )
    result = await db.execute(stmt)
    revision = result.scalar_one_or_none()

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision not found",
        )

    old_status = revision.status.value

    # Update admin response
    if rev_update.admin_response is not None:
        revision.admin_response = rev_update.admin_response.strip()

    # Update revision status and handle project lifecycle transition
    if rev_update.status is not None:
        revision.status = rev_update.status

        if rev_update.status == RevisionStatus.COMPLETED:
            revision.resolved_at = datetime.now(timezone.utc)
            # If project was addressing revision, transition to CLIENT_REVIEW
            if project.status in {ProjectStatus.REVISION_REQUESTED, ProjectStatus.DEVELOPMENT}:
                project.status = ProjectStatus.CLIENT_REVIEW
        elif rev_update.status == RevisionStatus.IN_PROGRESS:
            if project.status == ProjectStatus.REVISION_REQUESTED:
                project.status = ProjectStatus.DEVELOPMENT

    # Audit timeline logging
    activity = ProjectActivity(
        project_id=project_id,
        performed_by_user_id=current_user.id,
        action_type="REVISION_STATUS_CHANGED",
        old_status=old_status,
        new_status=revision.status.value,
        note=f"Revision #{revision.revision_number} status updated to {revision.status.value}",
        is_visible_to_client=True,
    )
    db.add(activity)

    await db.commit()

    # Reload revision with attachments eager-loaded
    stmt_reload = (
        select(Revision)
        .options(selectinload(Revision.attachments))
        .where(Revision.id == revision_id)
    )
    res_reload = await db.execute(stmt_reload)
    full_revision = res_reload.scalar_one()

    return APIResponse(
        success=True,
        message=f"Revision #{revision.revision_number} updated successfully.",
        data=RevisionResponse.model_validate(full_revision),
    )
