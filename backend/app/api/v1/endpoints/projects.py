import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_db
from app.models.activity import ProjectActivity
from app.models.customer import Customer
from app.models.enums import ProjectStatus, UserRole
from app.models.project import Project
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.project import (
    ActivityItemResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
)

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
    await db.refresh(new_project)

    return APIResponse(
        success=True,
        message="Project initiated successfully! Our studio team will review your requirements.",
        data=ProjectResponse.model_validate(new_project),
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
        .options(selectinload(Project.activities))
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
