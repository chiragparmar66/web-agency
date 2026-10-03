from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BuildReviewStatus, BuildStatus, ProjectStatus


class WebsiteBuildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    revision_id: Optional[str] = None
    version_number: int
    status: BuildStatus
    review_status: BuildReviewStatus = BuildReviewStatus.PENDING_REVIEW
    review_notes: Optional[str] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    client_approved: bool = False
    client_approved_at: Optional[datetime] = None
    client_feedback: Optional[str] = None
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


class BuildFileItem(BaseModel):
    """File item listed in build artifact directory."""
    path: str
    file_type: str
    size_bytes: int
    is_text: bool = True


class BuildFileContentResponse(BaseModel):
    """Safe read-only content of a generated file."""
    path: str
    file_type: str
    size_bytes: int
    content: Optional[str] = None
    is_text: bool = True
    is_truncated: bool = False


class BuildReviewDetailResponse(BaseModel):
    """Comprehensive build review details for admin inspection console."""
    project_id: str
    project_title: str
    build_id: str
    version_number: int
    status: BuildStatus
    review_status: BuildReviewStatus
    review_notes: Optional[str] = None
    client_approved: bool = False
    client_approved_at: Optional[datetime] = None
    client_feedback: Optional[str] = None
    is_active: bool
    created_at: datetime
    approved_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by_name: Optional[str] = None
    providers_used: Dict[str, str] = Field(default_factory=dict)
    entry_file: str = "index.html"
    files_count: int = 0
    total_size_bytes: int = 0
    validation_score: float = 100.0
    validation_findings: List[Dict[str, Any]] = Field(default_factory=list)
    spec_summary: Dict[str, Any] = Field(default_factory=dict)
    architecture_summary: Optional[Dict[str, Any]] = None
    generated_code_path: Optional[str] = None
    admin_notes: Optional[str] = None


class ClientBuildPreviewResponse(BaseModel):
    """Safe client-facing build preview metadata."""
    project_id: str
    project_title: str
    build_id: str
    version_number: int
    status: BuildStatus
    review_status: BuildReviewStatus
    client_approved: bool = False
    client_approved_at: Optional[datetime] = None
    preview_url: Optional[str] = None
    entry_file: str = "index.html"
    files_count: int = 0
    created_at: datetime


class ClientBuildApprovalRequest(BaseModel):
    feedback: Optional[str] = Field(None, max_length=2000, description="Optional client acceptance comments")


class ClientRevisionCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Brief summary of requested revision")
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed change requests")
    change_items: Optional[List[str]] = Field(default_factory=list, description="Specific itemized changes")



class BuildReviewApproveRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=1000, description="Optional approval notes")


class BuildReviewRejectRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000, description="Mandatory rejection reason")


class BuildRebuildRequest(BaseModel):
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Directives for rebuilding")



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
    waive_payment: Optional[bool] = Field(
        None,
        description="Explicit payment waiver control to bypass advance payment requirement",
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
