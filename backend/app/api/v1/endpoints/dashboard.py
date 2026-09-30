from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints.projects import get_or_create_customer
from app.models.activity import ProjectActivity
from app.models.enums import UserRole
from app.models.project import Project
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.project import (
    ActivityItemResponse,
    DashboardSummaryResponse,
    ProjectResponse,
)

router = APIRouter()


@router.get(
    "/summary",
    response_model=APIResponse[DashboardSummaryResponse],
    summary="Get customer dashboard summary and recent activity",
)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve real summary metrics and recent activity for the customer portal."""
    customer = await get_or_create_customer(current_user, db)

    # Fetch customer's projects
    proj_stmt = (
        select(Project)
        .where(Project.customer_id == customer.id)
        .order_by(Project.created_at.desc())
    )
    proj_res = await db.execute(proj_stmt)
    projects = proj_res.scalars().all()

    total_projects = len(projects)
    active_project = projects[0] if projects else None

    # Fetch recent activities for these projects
    recent_activities = []
    if projects:
        project_ids = [p.id for p in projects]
        act_stmt = (
            select(ProjectActivity)
            .where(
                ProjectActivity.project_id.in_(project_ids),
                ProjectActivity.is_visible_to_client == True,
            )
            .order_by(ProjectActivity.created_at.desc())
            .limit(10)
        )
        act_res = await db.execute(act_stmt)
        recent_activities = act_res.scalars().all()

    summary_data = DashboardSummaryResponse(
        total_projects=total_projects,
        active_project=ProjectResponse.model_validate(active_project) if active_project else None,
        recent_projects=[ProjectResponse.model_validate(p) for p in projects[:5]],
        recent_activities=[ActivityItemResponse.model_validate(a) for a in recent_activities],
    )

    return APIResponse(
        success=True,
        message="Dashboard summary loaded.",
        data=summary_data,
    )
