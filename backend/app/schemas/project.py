from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ProjectStatus
from app.schemas.pricing import PricingPackageResponse


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Project or website title")
    business_name: str = Field(..., min_length=2, max_length=255, description="Business or brand name")
    package_id: Optional[str] = None
    notes: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_number: str
    customer_id: str
    package_id: Optional[str] = None
    package: Optional[PricingPackageResponse] = None
    title: str
    business_name: str
    status: ProjectStatus
    preview_url: Optional[str] = None
    production_url: Optional[str] = None
    custom_domain: Optional[str] = None
    revisions_used: int
    created_at: datetime
    updated_at: datetime


class ActivityItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action_type: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


class ProjectDetailResponse(ProjectResponse):
    activities: List[ActivityItemResponse] = []


class DashboardSummaryResponse(BaseModel):
    total_projects: int
    active_project: Optional[ProjectResponse] = None
    recent_projects: List[ProjectResponse] = []
    recent_activities: List[ActivityItemResponse] = []
