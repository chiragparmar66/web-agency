from typing import Optional
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PortfolioProject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "portfolio_projects"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    technologies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False)
    gallery_urls: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    live_demo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    results_summary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Service(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "services"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(String(500), nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)
    deliverables: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    icon_name: Mapped[str] = mapped_column(String(100), nullable=False)
    starting_price_inr: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Testimonial(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "testimonials"

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
