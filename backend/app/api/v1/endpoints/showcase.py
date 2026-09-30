from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.showcase import PortfolioProject, Service
from app.schemas.common import APIResponse
from app.schemas.showcase import PortfolioProjectResponse, ServiceResponse

router = APIRouter()


@router.get(
    "/services",
    response_model=APIResponse[List[ServiceResponse]],
    summary="Get studio development services",
)
async def get_services(db: AsyncSession = Depends(get_db)):
    """Retrieve public web development services provided by the studio."""
    stmt = select(Service).order_by(Service.sort_order.asc())
    result = await db.execute(stmt)
    services = result.scalars().all()

    return APIResponse(
        success=True,
        message="Services retrieved.",
        data=[ServiceResponse.model_validate(s) for s in services],
    )


@router.get(
    "/portfolio",
    response_model=APIResponse[List[PortfolioProjectResponse]],
    summary="Get studio showcase portfolio",
)
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    """Retrieve public portfolio projects. Returns empty list if no projects exist yet."""
    stmt = select(PortfolioProject).order_by(PortfolioProject.sort_order.asc())
    result = await db.execute(stmt)
    projects = result.scalars().all()

    return APIResponse(
        success=True,
        message="Portfolio retrieved.",
        data=[PortfolioProjectResponse.model_validate(p) for p in projects],
    )
