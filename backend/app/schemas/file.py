from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import FileCategory


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    revision_id: Optional[str] = None
    file_category: FileCategory
    original_filename: str
    file_size_bytes: int
    mime_type: str
    uploaded_by_user_id: str
    created_at: datetime
    updated_at: datetime


class FileDeleteResponse(BaseModel):
    file_id: str
    deleted: bool = True
