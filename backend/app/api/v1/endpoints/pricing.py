"""Public pricing packages endpoint."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.pricing_package import PricingPackage
from app.schemas.common import APIResponse
from app.schemas.pricing import PricingPackageResponse

router = APIRouter()


@router.get(
    "/packages",
    response_model=APIResponse[List[PricingPackageResponse]],
    summary="List pricing packages",
)
async def list_packages(db: AsyncSession = Depends(get_db)):
    """Return all active pricing packages ordered by price."""
    stmt = (
        select(PricingPackage)
        .where(PricingPackage.is_active == True)  # noqa: E712
        .order_by(PricingPackage.price_inr.asc())
    )
    result = await db.execute(stmt)
    packages = result.scalars().all()

    return APIResponse(
        success=True,
        message="Pricing packages retrieved.",
        data=[PricingPackageResponse.model_validate(p) for p in packages],
    )
