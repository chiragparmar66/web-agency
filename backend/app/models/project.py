from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ProjectStatus

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.pricing_package import PricingPackage
    from app.models.inquiry import Inquiry
    from app.models.user import User
    from app.models.requirement import ProjectRequirement
    from app.models.project_file import ProjectFile
    from app.models.revision import Revision
    from app.models.payment import Payment
    from app.models.activity import ProjectActivity
    from app.models.deployment import Deployment
    from app.models.message import ProjectMessage
    from app.models.website_build import WebsiteBuild


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    project_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("pricing_packages.id", ondelete="SET NULL"),
        nullable=True,
    )
    inquiry_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("inquiries.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status_enum", native_enum=False),
        default=ProjectStatus.NEW,
        nullable=False,
        index=True,
    )
    assigned_developer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    preview_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    production_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    revisions_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="projects")
    package: Mapped[Optional["PricingPackage"]] = relationship("PricingPackage", back_populates="projects")
    inquiry: Mapped[Optional["Inquiry"]] = relationship("Inquiry", back_populates="converted_project")
    assigned_developer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_projects",
        foreign_keys=[assigned_developer_id],
    )
    requirements: Mapped[Optional["ProjectRequirement"]] = relationship(
        "ProjectRequirement",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    files: Mapped[List["ProjectFile"]] = relationship(
        "ProjectFile",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    revisions: Mapped[List["Revision"]] = relationship(
        "Revision",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    activities: Mapped[List["ProjectActivity"]] = relationship(
        "ProjectActivity",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    messages: Mapped[List["ProjectMessage"]] = relationship(
        "ProjectMessage",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    builds: Mapped[List["WebsiteBuild"]] = relationship(
        "WebsiteBuild",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    deployments: Mapped[List["Deployment"]] = relationship(
        "Deployment",
        back_populates="project",
        cascade="all, delete-orphan",
    )

