from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DeploymentStatus

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.website_build import WebsiteBuild


class Deployment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "deployments"

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    build_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("website_builds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus, name="deployment_status_enum", native_enum=False),
        default=DeploymentStatus.READY,
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_deployment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    live_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deployed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deployment_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    smoke_test_status: Mapped[Optional[str]] = mapped_column(String(50), default="NOT_RUN", nullable=True)
    smoke_test_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="deployments")
    build: Mapped["WebsiteBuild"] = relationship("WebsiteBuild", back_populates="deployments")
    deployed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[deployed_by_user_id])
