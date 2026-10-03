from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InquiryStatus, ProjectStatus, UserRole


class AdminOverviewResponse(BaseModel):
    admin_email: str
    total_users: int
    total_projects: int
    active_projects: int
    total_inquiries: int
    system_status: str


class StaffUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool


class AdminCustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: Optional[str] = None
    phone: str
    company_name: Optional[str] = None


class AdminProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_number: str
    customer_id: str
    package_id: Optional[str] = None
    title: str
    business_name: str
    status: ProjectStatus
    revisions_used: int
    preview_url: Optional[str] = None
    production_url: Optional[str] = None
    custom_domain: Optional[str] = None
    assigned_developer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Associated nested entities
    customer: Optional[AdminCustomerSummary] = None
    assigned_developer: Optional[StaffUserResponse] = None
    package_name: Optional[str] = None
    advance_payment_status: Optional[str] = "PENDING"
    total_paid_inr: Optional[float] = 0.0


class AdminProjectUpdate(BaseModel):
    status: Optional[ProjectStatus] = Field(None, description="New lifecycle status for the project")
    assigned_developer_id: Optional[str] = Field(None, description="Staff user ID to assign as project developer")
    preview_url: Optional[str] = Field(None, max_length=500, description="Staging preview URL")
    production_url: Optional[str] = Field(None, max_length=500, description="Live production URL")
    custom_domain: Optional[str] = Field(None, max_length=255, description="Client custom domain")


class AdminInquiryUpdate(BaseModel):
    status: Optional[InquiryStatus] = Field(None, description="Updated CRM status for lead/inquiry")
    is_read: Optional[bool] = Field(None, description="Mark inquiry as read or unread")
