from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.project import Project
    from app.models.message import ProjectMessage
    from app.models.revision import Revision


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.CUSTOMER,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    customer_profile: Mapped[Optional["Customer"]] = relationship(
        "Customer",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    assigned_projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="assigned_developer",
        foreign_keys="Project.assigned_developer_id",
    )
    sent_messages: Mapped[List["ProjectMessage"]] = relationship(
        "ProjectMessage",
        back_populates="sender",
    )
    requested_revisions: Mapped[List["Revision"]] = relationship(
        "Revision",
        back_populates="requested_by",
    )
