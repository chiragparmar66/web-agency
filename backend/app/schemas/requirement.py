from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RequirementUpdate(BaseModel):
    """Used for saving draft or final submission of project requirements."""
    business_summary: Optional[str] = Field(None, max_length=3000)
    target_audience: Optional[str] = Field(None, max_length=2000)
    services_offered: Optional[str] = Field(None, max_length=2000)
    color_preferences: Optional[str] = Field(None, max_length=255)
    reference_websites: Optional[List[str]] = None
    social_links: Optional[dict] = None
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    physical_address: Optional[str] = Field(None, max_length=1000)
    special_requests: Optional[str] = Field(None, max_length=3000)


class RequirementSubmit(RequirementUpdate):
    """Marks requirements as final — cannot be undone."""
    pass


class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    business_summary: Optional[str] = None
    target_audience: Optional[str] = None
    services_offered: Optional[str] = None
    color_preferences: Optional[str] = None
    reference_websites: List[str] = []
    social_links: dict = {}
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    physical_address: Optional[str] = None
    special_requests: Optional[str] = None
    is_submitted: bool
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
