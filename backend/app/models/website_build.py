from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BuildStatus

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.revision import Revision
    from app.models.user import User


class WebsiteBuild(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "website_builds"

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("revisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[BuildStatus] = mapped_column(
        Enum(BuildStatus, name="build_status_enum", native_enum=False),
        default=BuildStatus.QUEUED,
        nullable=False,
        index=True,
    )
    spec_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    architecture_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    design_system: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    generated_code_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preview_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="builds")
    revision: Mapped[Optional["Revision"]] = relationship("Revision", back_populates="builds")
    approved_by: Mapped[Optional["User"]] = relationship("User")
