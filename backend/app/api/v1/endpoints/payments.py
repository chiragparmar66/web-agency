"""
Secure Payment Integration Endpoints.
Handles Razorpay order creation, server-side price calculation,
HMAC-SHA256 signature verification, replay attack prevention,
atomic project lifecycle state transitions, and invoice retrieval.
"""
from datetime import datetime, timezone
import hashlib
import hmac
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.models.activity import ProjectActivity
from app.models.customer import Customer
from app.models.enums import PaymentStatus, PaymentType, ProjectStatus, UserRole
from app.models.payment import Payment
from app.models.project import Project
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.payment import (
    InvoiceDetailResponse,
    OrderCreate,
    OrderResponse,
    PaymentResponse,
    PaymentVerify,
)

router = APIRouter()


async def _get_project_with_payment_access(
    project_id: str,
    current_user: User,
    db: AsyncSession,
) -> Project:
    """Validate project exists and authenticated user has access."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.package),
        )
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CUSTOMER:
        cust_stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust_res = await db.execute(cust_stmt)
        customer = cust_res.scalar_one_or_none()
        if not customer or project.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access billing for this project",
            )

    return project


@router.post(
    "/create-order",
    response_model=APIResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay payment order",
)
async def create_payment_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a secure payment order and invoice number.
    Price is calculated authoritatively from the project package in the database.
    Prevents client-side price tampering.
    """
    project = await _get_project_with_payment_access(payload.project_id, current_user, db)

    # Calculate authoritative amount in INR
    base_price = 4999.0
    if project.package and project.package.price_inr:
        base_price = float(project.package.price_inr)

    if payload.payment_type in [PaymentType.ADVANCE, PaymentType.FINAL]:
        amount_inr = round(base_price / 2.0, 2)
    elif payload.payment_type == PaymentType.MILESTONE:
        amount_inr = round(base_price / 4.0, 2)
    else:  # FULL
        amount_inr = round(base_price, 2)

    # Generate sequential invoice number
    count_stmt = select(func.count(Payment.id))
    inv_count = (await db.execute(count_stmt)).scalar() or 0
    invoice_number = f"INV-2026-{inv_count + 1:04d}"

    # Generate unique Razorpay order ID (simulated or API integrated)
    order_id = f"order_{uuid.uuid4().hex[:16]}"

    # Customer metadata for checkout prefill
    customer = project.customer
    customer_name = customer.full_name if customer else current_user.full_name
    customer_phone = customer.phone if customer else (current_user.phone or "+919876543210")
    customer_email = customer.email if customer else current_user.email

    # Insert pending Payment record
    new_payment = Payment(
        project_id=project.id,
        customer_id=project.customer_id,
        payment_type=payload.payment_type,
        amount_inr=amount_inr,
        status=PaymentStatus.PENDING,
        razorpay_order_id=order_id,
        invoice_number=invoice_number,
    )
    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)

    return APIResponse(
        success=True,
        message="Payment order created successfully.",
        data=OrderResponse(
            order_id=order_id,
            amount_inr=amount_inr,
            amount_paise=int(round(amount_inr * 100)),
            currency="INR",
            key_id=settings.RAZORPAY_KEY_ID,
            payment_id=new_payment.id,
            invoice_number=invoice_number,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
        ),
    )


@router.post(
    "/verify",
    response_model=APIResponse[PaymentResponse],
    summary="Verify Razorpay payment signature & update project lifecycle",
)
async def verify_payment(
    payload: PaymentVerify,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify HMAC-SHA256 signature from Razorpay checkout.
    Guards against signature tampering and replay attacks.
    On success: marks payment SUCCESS, updates project status, and logs activity.
    """
    project = await _get_project_with_payment_access(payload.project_id, current_user, db)

    # 1. Replay attack guard: check if payment_id has already been consumed
    replay_stmt = select(Payment).where(
        Payment.razorpay_payment_id == payload.razorpay_payment_id,
        Payment.status == PaymentStatus.SUCCESS,
    )
    replay_res = await db.execute(replay_stmt)
    if replay_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment has already been processed and verified (replay attack prevented).",
        )

    # 2. Retrieve corresponding pending payment
    stmt = select(Payment).where(
        Payment.project_id == payload.project_id,
        Payment.razorpay_order_id == payload.razorpay_order_id,
    )
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matching payment order not found for this project.",
        )

    if payment.status == PaymentStatus.SUCCESS:
        return APIResponse(
            success=True,
            message="Payment was already verified.",
            data=PaymentResponse.model_validate(payment),
        )

    # 3. Compute HMAC-SHA256 signature
    message = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode("utf-8")
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
        payment.status = PaymentStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature. Verification failed.",
        )

    # 4. Atomic transaction update
    payment.status = PaymentStatus.SUCCESS
    payment.razorpay_payment_id = payload.razorpay_payment_id
    payment.razorpay_signature = payload.razorpay_signature
    payment.paid_at = datetime.now(timezone.utc)

    # 5. Project lifecycle transition
    old_status = project.status.value
    if payment.payment_type in [PaymentType.ADVANCE, PaymentType.FULL]:
        if project.status in [ProjectStatus.NEW, ProjectStatus.PAYMENT_PENDING]:
            project.status = ProjectStatus.REQUIREMENTS_PENDING
    elif payment.payment_type == PaymentType.FINAL:
        if project.status in [ProjectStatus.CLIENT_REVIEW, ProjectStatus.APPROVED]:
            project.status = ProjectStatus.DEPLOYING

    # 6. Audit timeline activity logging
    activity = ProjectActivity(
        project_id=project.id,
        performed_by_user_id=current_user.id,
        action_type="PAYMENT_COMPLETED",
        old_status=old_status,
        new_status=project.status.value,
        note=(
            f"Payment of ₹{payment.amount_inr:,.2f} ({payment.payment_type.value}) "
            f"verified successfully. Invoice: {payment.invoice_number}"
        ),
        is_visible_to_client=True,
    )
    db.add(activity)

    await db.commit()
    await db.refresh(payment)

    return APIResponse(
        success=True,
        message="Payment verified successfully! Receipt has been generated.",
        data=PaymentResponse.model_validate(payment),
    )


@router.get(
    "/projects/{project_id}",
    response_model=APIResponse[List[PaymentResponse]],
    summary="List payments and invoices for a project",
)
async def list_project_payments(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve billing history, invoices, and payment statuses for a project."""
    await _get_project_with_payment_access(project_id, current_user, db)

    stmt = (
        select(Payment)
        .where(Payment.project_id == project_id)
        .order_by(Payment.created_at.desc())
    )
    result = await db.execute(stmt)
    payments = result.scalars().all()

    return APIResponse(
        success=True,
        message="Project payments retrieved.",
        data=[PaymentResponse.model_validate(p) for p in payments],
    )


@router.get(
    "/{payment_id}/invoice",
    response_model=APIResponse[InvoiceDetailResponse],
    summary="Get invoice receipt details",
)
async def get_invoice(
    payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve complete tax invoice details for a payment record."""
    stmt = (
        select(Payment)
        .options(
            selectinload(Payment.project),
            selectinload(Payment.customer),
        )
        .where(Payment.id == payment_id)
    )
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    # Access check: Customer can only view own invoices
    if current_user.role == UserRole.CUSTOMER:
        cust_stmt = select(Customer).where(Customer.user_id == current_user.id)
        customer = (await db.execute(cust_stmt)).scalar_one_or_none()
        if not customer or payment.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this invoice",
            )

    customer = payment.customer
    project = payment.project

    return APIResponse(
        success=True,
        message="Invoice retrieved.",
        data=InvoiceDetailResponse(
            invoice_number=payment.invoice_number or "INV-PENDING",
            payment_id=payment.id,
            project_number=project.project_number if project else "PRJ-UNKNOWN",
            project_title=project.title if project else "Website Development",
            customer_name=customer.full_name if customer else "Client",
            customer_email=customer.email if customer else None,
            customer_phone=customer.phone if customer else "",
            customer_company=customer.company_name if customer else None,
            customer_gstin=customer.gstin if customer else None,
            payment_type=payment.payment_type,
            amount_inr=float(payment.amount_inr),
            currency="INR",
            status=payment.status,
            paid_at=payment.paid_at,
            created_at=payment.created_at,
        ),
    )
