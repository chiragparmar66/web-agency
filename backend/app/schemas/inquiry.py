from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from app.models.enums import InquirySource, InquiryStatus


class InquiryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=5, max_length=50)
    subject: Optional[str] = Field(None, max_length=255)
    business_name: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    source: InquirySource = InquirySource.CONTACT_FORM
    selected_package: Optional[str] = Field(None, max_length=100)
    message: str = Field(..., min_length=5, max_length=5000)

    @model_validator(mode="after")
    def validate_contact_channel(self) -> "InquiryCreate":
        if not self.email and not self.phone:
            raise ValueError("Please provide at least an email address or a phone number so our engineers can reply.")
        return self


class InquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    subject: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    city: Optional[str] = None
    source: InquirySource
    selected_package: Optional[str] = None
    message: Optional[str] = None
    status: InquiryStatus
    read_at: Optional[datetime] = None
    created_at: datetime

