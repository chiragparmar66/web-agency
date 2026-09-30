"""
Project Messages endpoint.
Customers can send and read client-facing messages.
Internal notes (is_internal_note=True) are hidden from CUSTOMER role.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.customer import Customer
from app.models.enums import UserRole
from app.models.message import ProjectMessage
from app.models.project import Project
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter()


async def _get_project_with_access(
    project_id: str,
    current_user: User,
    db: AsyncSession,
) -> Project:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CUSTOMER:
        cust_stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust_result = await db.execute(cust_stmt)
        customer = cust_result.scalar_one_or_none()
        if not customer or project.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project",
            )
    return project


@router.get(
    "",
    response_model=APIResponse[List[MessageResponse]],
    summary="List project messages",
)
async def list_messages(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all client-visible messages on a project. Internal notes are hidden from customers."""
    await _get_project_with_access(project_id, current_user, db)

    stmt = select(ProjectMessage).where(ProjectMessage.project_id == project_id)
    # Hide internal notes from CUSTOMER role
    if current_user.role == UserRole.CUSTOMER:
        stmt = stmt.where(ProjectMessage.is_internal_note == False)  # noqa: E712
    stmt = stmt.order_by(ProjectMessage.created_at.asc())

    result = await db.execute(stmt)
    messages = result.scalars().all()

    return APIResponse(
        success=True,
        message="Messages retrieved.",
        data=[MessageResponse.model_validate(m) for m in messages],
    )


@router.post(
    "",
    response_model=APIResponse[MessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Send a message on a project",
)
async def send_message(
    project_id: str,
    payload: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message on this project.
    Customers always send non-internal messages.
    Admins/Developers can send internal notes via admin endpoint.
    """
    await _get_project_with_access(project_id, current_user, db)

    msg = ProjectMessage(
        project_id=project_id,
        sender_user_id=current_user.id,
        message=payload.message.strip(),
        is_internal_note=False,  # Customers never post internal notes
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return APIResponse(
        success=True,
        message="Message sent.",
        data=MessageResponse.model_validate(msg),
    )
