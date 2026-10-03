"""
Project Requirements endpoint.
Customers can GET and PUT their project requirements.
Requirements can be saved as draft (PUT without submit) or submitted (POST /submit).
Once submitted, requirements are locked and cannot be edited.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.customer import Customer
from app.models.enums import PaymentStatus, PaymentType, ProjectStatus, UserRole
from app.models.payment import Payment
from app.models.project import Project
from app.models.requirement import ProjectRequirement
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.requirement import RequirementResponse, RequirementSubmit, RequirementUpdate

router = APIRouter()


async def _get_project_with_access(
    project_id: str,
    current_user: User,
    db: AsyncSession,
) -> Project:
    """Fetch project and enforce ownership for CUSTOMER role."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CUSTOMER:
        # Resolve customer record
        cust_stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust_result = await db.execute(cust_stmt)
        customer = cust_result.scalar_one_or_none()
        if not customer or project.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project",
            )

    return project


async def _get_or_create_requirement(project: Project, db: AsyncSession) -> ProjectRequirement:
    """Return existing requirement record or create a blank one."""
    stmt = select(ProjectRequirement).where(ProjectRequirement.project_id == project.id)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()

    if not req:
        req = ProjectRequirement(
            project_id=project.id,
            reference_websites=[],
            social_links={},
            is_submitted=False,
        )
        db.add(req)
        await db.flush()

    return req


@router.get(
    "",
    response_model=APIResponse[RequirementResponse],
    summary="Get project requirements",
)
async def get_requirements(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current requirement questionnaire for a project."""
    project = await _get_project_with_access(project_id, current_user, db)
    req = await _get_or_create_requirement(project, db)
    await db.commit()
    await db.refresh(req)

    return APIResponse(
        success=True,
        message="Requirements retrieved.",
        data=RequirementResponse.model_validate(req),
    )


@router.put(
    "",
    response_model=APIResponse[RequirementResponse],
    summary="Save requirements draft",
)
async def save_requirements_draft(
    project_id: str,
    payload: RequirementUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Save requirement answers as a draft. Safe to call multiple times."""
    project = await _get_project_with_access(project_id, current_user, db)
    req = await _get_or_create_requirement(project, db)

    if req.is_submitted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Requirements have already been submitted and cannot be edited.",
        )

    # Apply only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(req, field, value)

    await db.commit()
    await db.refresh(req)

    return APIResponse(
        success=True,
        message="Requirements saved as draft.",
        data=RequirementResponse.model_validate(req),
    )


@router.post(
    "/submit",
    response_model=APIResponse[RequirementResponse],
    summary="Submit requirements (final)",
)
async def submit_requirements(
    project_id: str,
    payload: RequirementSubmit,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Finalize and submit project requirements.
    Once submitted, requirements are locked.
    Project status moves to REQUIREMENTS_PENDING.
    """
    project = await _get_project_with_access(project_id, current_user, db)
    req = await _get_or_create_requirement(project, db)

    if req.is_submitted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Requirements have already been submitted.",
        )

    # Apply all fields from the payload
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(req, field, value)

    req.is_submitted = True
    req.submitted_at = datetime.now(timezone.utc)

    # Check if advance payment has already been verified
    pay_stmt = select(Payment).where(
        Payment.project_id == project.id,
        Payment.status == PaymentStatus.SUCCESS,
        Payment.payment_type.in_([PaymentType.ADVANCE, PaymentType.FULL]),
    )
    pay_res = await db.execute(pay_stmt)
    has_advance = pay_res.scalar_one_or_none() is not None

    if has_advance:
        project.status = ProjectStatus.PENDING_APPROVAL
    elif project.status == ProjectStatus.NEW:
        project.status = ProjectStatus.REQUIREMENTS_PENDING

    await db.commit()
    await db.refresh(req)

    return APIResponse(
        success=True,
        message="Requirements submitted successfully! Our studio team will review and begin your project.",
        data=RequirementResponse.model_validate(req),
    )
