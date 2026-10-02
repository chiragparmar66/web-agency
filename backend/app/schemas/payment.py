from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentStatus, PaymentType


class OrderCreate(BaseModel):
    project_id: str = Field(..., description="Project UUID to generate order for")
    payment_type: PaymentType = Field(
        default=PaymentType.ADVANCE,
        description="Type of payment: ADVANCE (50%), FINAL (50%), MILESTONE, or FULL (100%)",
    )


class OrderResponse(BaseModel):
    order_id: str
    amount_inr: float
    amount_paise: int
    currency: str = "INR"
    key_id: str
    payment_id: str
    invoice_number: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: str


class PaymentVerify(BaseModel):
    project_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    customer_id: str
    payment_type: PaymentType
    amount_inr: float
    status: PaymentStatus
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    invoice_number: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


class InvoiceDetailResponse(BaseModel):
    invoice_number: str
    payment_id: str
    project_number: str
    project_title: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: str
    customer_company: Optional[str] = None
    customer_gstin: Optional[str] = None
    payment_type: PaymentType
    amount_inr: float
    currency: str = "INR"
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime
