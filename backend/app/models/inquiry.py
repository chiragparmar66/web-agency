from typing import TYPE_CHECKING, Optional
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import InquirySource, InquiryStatus

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.project import Project


class Inquiry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "inquiries"

    customer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    business_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    business_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source: Mapped[InquirySource] = mapped_column(
        Enum(InquirySource, name="inquiry_source_enum", native_enum=False),
        default=InquirySource.WHATSAPP,
        nullable=False,
    )
    selected_package: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[InquiryStatus] = mapped_column(
        Enum(InquiryStatus, name="inquiry_status_enum", native_enum=False),
        default=InquiryStatus.NEW,
        nullable=False,
        index=True,
    )

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="inquiries")
    converted_project: Mapped[Optional["Project"]] = relationship("Project", back_populates="inquiry")
