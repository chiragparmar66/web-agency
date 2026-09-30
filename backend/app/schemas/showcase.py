from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    title: str
    short_description: str
    full_description: str
    deliverables: List[str]
    icon_name: str
    starting_price_inr: float
    sort_order: int


class PortfolioProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    client_name: str
    industry: str
    description: str
    technologies: List[str]
    thumbnail_url: str
    gallery_urls: List[str]
    live_demo_url: Optional[str] = None
    results_summary: Optional[str] = None
    is_featured: bool
    sort_order: int
