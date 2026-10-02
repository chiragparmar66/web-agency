from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BuildStatus, ProjectStatus


class WebsiteBuildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    revision_id: Optional[str] = None
    version_number: int
    status: BuildStatus
    spec_data: Optional[Dict[str, Any]] = None
    architecture_data: Optional[Dict[str, Any]] = None
    design_system: Optional[Dict[str, Any]] = None
    generated_code_path: Optional[str] = None
    preview_url: Optional[str] = None
    admin_notes: Optional[str] = None
    is_active: bool = False
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class BuildApprovalRequest(BaseModel):
    admin_notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional admin notes for starting this website build",
    )
    revision_id: Optional[str] = Field(
        None,
        description="Optional revision id if this build run addresses a client revision",
    )
    force_override_payment: bool = Field(
        False,
        description="Allow admin to proceed even if advance payment check is waived",
    )


class BuildApprovalResponse(BaseModel):
    success: bool = True
    message: str
    build: WebsiteBuildResponse
    project_status: ProjectStatus


class ProjectAIContextResponse(BaseModel):
    project_id: str
    title: str
    client_name: str
    client_email: str
    company_name: Optional[str] = None
    package: Optional[Dict[str, Any]] = None
    requirements: Optional[Dict[str, Any]] = None
    files: List[Dict[str, Any]] = []
    active_revision: Optional[Dict[str, Any]] = None
    ready_for_build: bool = True
    context_summary: Dict[str, Any]
