from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class ProjectRequirement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_requirements"

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    business_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    services_offered: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color_preferences: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reference_websites: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    social_links: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    physical_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    special_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="requirements")
