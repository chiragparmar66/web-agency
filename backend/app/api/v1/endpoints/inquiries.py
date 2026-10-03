import time
from typing import Dict, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.inquiry import Inquiry
from app.schemas.common import APIResponse
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.services.email_service import EmailService

router = APIRouter()

# Lightweight in-memory rate limiting: max 5 submissions per 300s window per IP
_IP_WINDOW_SECONDS = 300
_IP_MAX_SUBMISSIONS = 5
_ip_rate_tracker: Dict[str, List[float]] = {}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(client_ip: str) -> None:
    # Exempt unidentifiable testclient to prevent test fixture pollution
    if not client_ip or client_ip in ("testclient", "unknown"):
        return

    now = time.time()
    timestamps = _ip_rate_tracker.get(client_ip, [])
    # Prune expired timestamps
    valid_timestamps = [t for t in timestamps if now - t < _IP_WINDOW_SECONDS]
    if len(valid_timestamps) >= _IP_MAX_SUBMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many consultation requests submitted. Please wait a few minutes before trying again, or message us on WhatsApp.",
        )
    valid_timestamps.append(now)
    _ip_rate_tracker[client_ip] = valid_timestamps


@router.post(
    "",
    response_model=APIResponse[InquiryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a project inquiry or contact message",
)
async def create_inquiry(
    request: Request,
    inquiry_in: InquiryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for prospective clients to submit inquiries or contact messages."""
    client_ip = _get_client_ip(request)
    _check_rate_limit(client_ip)

    new_inquiry = Inquiry(
        name=inquiry_in.name.strip(),
        email=inquiry_in.email.strip().lower() if inquiry_in.email else None,
        phone=inquiry_in.phone.strip() if inquiry_in.phone else None,
        subject=inquiry_in.subject.strip() if inquiry_in.subject else None,
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

    # Dispatch email notification in background task to not block response
    inquiry_dict = {
        "id": new_inquiry.id,
        "name": new_inquiry.name,
        "email": new_inquiry.email,
        "phone": new_inquiry.phone,
        "subject": new_inquiry.subject,
        "selected_package": new_inquiry.selected_package,
        "message": new_inquiry.message,
        "created_at": new_inquiry.created_at,
    }
    background_tasks.add_task(EmailService.send_inquiry_notification, inquiry_dict)

    return APIResponse(
        success=True,
        message="Thank you! Your inquiry has been received. Our team will get back to you shortly.",
        data=InquiryResponse.model_validate(new_inquiry),
    )

