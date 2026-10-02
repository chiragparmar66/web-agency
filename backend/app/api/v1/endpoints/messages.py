"""
Project Messages endpoint.
Customers can send and read client-facing messages.
Internal notes (is_internal_note=True) are hidden from CUSTOMER role.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

    stmt = (
        select(ProjectMessage)
        .options(selectinload(ProjectMessage.sender))
        .where(ProjectMessage.project_id == project_id)
    )
    # Hide internal notes from CUSTOMER role
    if current_user.role == UserRole.CUSTOMER:
        stmt = stmt.where(ProjectMessage.is_internal_note == False)  # noqa: E712
    stmt = stmt.order_by(ProjectMessage.created_at.asc())

    result = await db.execute(stmt)
    messages = result.scalars().all()

    resp_data = [
        MessageResponse(
            id=m.id,
            project_id=m.project_id,
            sender_user_id=m.sender_user_id,
            sender_name=m.sender.full_name if m.sender else None,
            sender_role=m.sender.role.value if m.sender else None,
            message=m.message,
            is_internal_note=m.is_internal_note,
            created_at=m.created_at,
        )
        for m in messages
    ]

    return APIResponse(
        success=True,
        message="Messages retrieved.",
        data=resp_data,
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
    Admins/Developers can post internal notes by setting is_internal_note=True.
    """
    await _get_project_with_access(project_id, current_user, db)

    is_internal = False
    if current_user.role in {UserRole.ADMIN, UserRole.DEVELOPER}:
        is_internal = payload.is_internal_note

    msg = ProjectMessage(
        project_id=project_id,
        sender_user_id=current_user.id,
        message=payload.message.strip(),
        is_internal_note=is_internal,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    resp = MessageResponse(
        id=msg.id,
        project_id=msg.project_id,
        sender_user_id=msg.sender_user_id,
        sender_name=current_user.full_name,
        sender_role=current_user.role.value,
        message=msg.message,
        is_internal_note=msg.is_internal_note,
        created_at=msg.created_at,
    )

    return APIResponse(
        success=True,
        message="Internal note recorded." if is_internal else "Message sent.",
        data=resp,
    )
