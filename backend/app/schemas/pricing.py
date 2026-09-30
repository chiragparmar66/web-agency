from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class PricingPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    price_inr: float
    description: str
    features: List[str] = []
    delivery_days: int
    revisions_included: int
    is_popular: bool = False
    is_active: bool = True
