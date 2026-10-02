from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RevisionStatus
from app.schemas.file import FileResponse


class RevisionCreate(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed revision feedback or requested changes",
    )
    attachment_file_ids: Optional[List[str]] = Field(
        default=[],
        description="List of ProjectFile IDs to attach to this revision",
    )


class RevisionUpdate(BaseModel):
    status: Optional[RevisionStatus] = Field(
        None,
        description="New revision status (PENDING, IN_PROGRESS, COMPLETED, REJECTED)",
    )
    admin_response: Optional[str] = Field(
        None,
        max_length=5000,
        description="Staff notes or resolution details",
    )


class RevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    revision_number: int
    requested_by_user_id: str
    description: str
    status: RevisionStatus
    admin_response: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    attachments: List[FileResponse] = []
