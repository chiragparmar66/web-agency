from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.inquiry import Inquiry
from app.schemas.common import APIResponse
from app.schemas.inquiry import InquiryCreate, InquiryResponse

router = APIRouter()


@router.post(
    "",
    response_model=APIResponse[InquiryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a project inquiry or contact message",
)
async def create_inquiry(
    inquiry_in: InquiryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for prospective clients to submit inquiries or contact messages."""
    new_inquiry = Inquiry(
        name=inquiry_in.name.strip(),
        email=inquiry_in.email.strip().lower() if inquiry_in.email else None,
        phone=inquiry_in.phone.strip(),
        business_name=inquiry_in.business_name.strip() if inquiry_in.business_name else None,
        business_type=inquiry_in.business_type.strip() if inquiry_in.business_type else None,
        city=inquiry_in.city.strip() if inquiry_in.city else None,
        source=inquiry_in.source,
        selected_package=inquiry_in.selected_package,
        message=inquiry_in.message.strip(),
    )
    db.add(new_inquiry)
    await db.commit()
    await db.refresh(new_inquiry)

    return APIResponse(
        success=True,
        message="Thank you! Your inquiry has been received. Our team will get back to you shortly.",
        data=InquiryResponse.model_validate(new_inquiry),
    )
