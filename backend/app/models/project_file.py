from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FileCategory

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.revision import Revision
    from app.models.user import User


class ProjectFile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_files"

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
    file_category: Mapped[FileCategory] = mapped_column(
        Enum(FileCategory, name="file_category_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="files")
    revision: Mapped[Optional["Revision"]] = relationship("Revision", back_populates="attachments")
