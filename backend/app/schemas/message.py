from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Message content")
    is_internal_note: bool = Field(default=False, description="Internal developer/admin note (Staff only)")


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    sender_user_id: str
    sender_name: Optional[str] = None
    sender_role: Optional[str] = None
    message: str
    is_internal_note: bool
    created_at: datetime
