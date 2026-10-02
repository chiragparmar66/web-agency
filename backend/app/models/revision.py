from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import RevisionStatus

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.project_file import ProjectFile
    from app.models.website_build import WebsiteBuild


class Revision(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "revisions"

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_by_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RevisionStatus] = mapped_column(
        Enum(RevisionStatus, name="revision_status_enum", native_enum=False),
        default=RevisionStatus.PENDING,
        nullable=False,
        index=True,
    )
    admin_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="revisions")
    requested_by: Mapped["User"] = relationship("User", back_populates="requested_revisions")
    attachments: Mapped[List["ProjectFile"]] = relationship(
        "ProjectFile",
        back_populates="revision",
        cascade="all, delete-orphan",
    )
    builds: Mapped[List["WebsiteBuild"]] = relationship(
        "WebsiteBuild",
        back_populates="revision",
    )
