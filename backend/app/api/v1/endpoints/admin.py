from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import APIResponse

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

    return APIResponse(
        success=True,
        message="Admin overview accessed.",
        data={
            "admin_email": admin_user.email,
            "total_users": user_count,
            "system_status": "operational",
        },
    )
