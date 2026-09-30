from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class PricingPackage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "pricing_packages"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_inr: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    features: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    delivery_days: Mapped[int] = mapped_column(Integer, nullable=False)
    revisions_included: Mapped[int] = mapped_column(Integer, nullable=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="package")
