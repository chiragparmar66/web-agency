from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Message content")


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    sender_user_id: str
    message: str
    is_internal_note: bool
    created_at: datetime
