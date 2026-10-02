from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import FileCategory, PaymentStatus, PaymentType, RevisionStatus
from app.models.project import Project
from app.models.customer import Customer
from app.models.user import User


async def get_project_with_context(project_id: str, db: AsyncSession) -> Optional[Project]:
    """
    Fetch a project with all related models loaded for AI context aggregation.
    """
    query = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.customer).selectinload(Customer.user),
            selectinload(Project.package),
            selectinload(Project.requirements),
            selectinload(Project.files),
            selectinload(Project.revisions),
            selectinload(Project.payments),
            selectinload(Project.builds),
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def build_project_ai_context(
    project_id: str,
    db: AsyncSession,
    revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Aggregate client details, requirements, uploaded assets, package specs,
    and revision requests into a normalized structured context for AI generation.
    """
    project = await get_project_with_context(project_id, db)
    if not project:
        raise ValueError(f"Project with ID '{project_id}' not found.")

    # 1. Client details
    user = project.customer.user if project.customer else None
    client_name = user.full_name if user else "Valued Client"
    client_email = user.email if user else ""
    company_name = project.customer.company_name if project.customer else None
    client_phone = project.customer.phone if project.customer else None

    # 2. Package details
    package_data = None
    if project.package:
        package_data = {
            "id": project.package.id,
            "name": project.package.name,
            "slug": project.package.slug,
            "price_inr": float(project.package.price_inr),
            "advance_percentage": getattr(project.package, "advance_percentage", 50),
            "delivery_days": project.package.delivery_days,
            "revision_limit": getattr(project.package, "revisions_included", 2),
            "features": project.package.features or [],
        }

    # 3. Requirements
    req = project.requirements
    requirements_data = None
    if req:
        requirements_data = {
            "id": req.id,
            "business_summary": req.business_summary or "",
            "target_audience": req.target_audience or "",
            "services_offered": req.services_offered or "",
            "color_preferences": req.color_preferences or "",
            "reference_websites": req.reference_websites or [],
            "social_links": req.social_links or {},
            "contact_email": req.contact_email or client_email,
            "contact_phone": req.contact_phone or client_phone,
            "physical_address": req.physical_address or "",
            "special_requests": req.special_requests or "",
            "is_submitted": req.is_submitted,
            "submitted_at": req.submitted_at.isoformat() if req.submitted_at else None,
        }

    # 4. Uploaded files & categorized assets
    files_list = []
    files_by_category: Dict[str, List[Dict[str, Any]]] = {}
    has_logo = False

    for file in project.files or []:
        cat_key = file.file_category.value if hasattr(file.file_category, "value") else str(file.file_category)
        file_info = {
            "id": file.id,
            "category": cat_key,
            "original_filename": file.original_filename,
            "mime_type": file.mime_type,
            "file_size_bytes": file.file_size_bytes,
            "file_path": file.file_path,
        }
        files_list.append(file_info)
        files_by_category.setdefault(cat_key, []).append(file_info)

        if cat_key in ("LOGO", "BRAND_ASSET") and "logo" in file.original_filename.lower():
            has_logo = True
        elif cat_key == "LOGO":
            has_logo = True

    # 5. Revisions (active revision for iteration)
    active_revision_data = None
    target_revision = None

    if revision_id:
        target_revision = next((r for r in (project.revisions or []) if r.id == revision_id), None)
    elif project.revisions:
        # Check for pending or in-progress revision
        for r in project.revisions:
            if r.status in (RevisionStatus.PENDING, RevisionStatus.IN_PROGRESS):
                target_revision = r
                break

    if target_revision:
        active_revision_data = {
            "id": target_revision.id,
            "revision_number": target_revision.revision_number,
            "description": target_revision.description,
            "status": target_revision.status.value,
        }

    # 6. Payment status verification
    advance_paid = False
    total_paid = 0.0
    for p in project.payments or []:
        if p.status == PaymentStatus.SUCCESS:
            total_paid += float(p.amount_inr)
            if p.payment_type == PaymentType.ADVANCE:
                advance_paid = True

    # 7. Suggested pages based on package / business
    suggested_pages = ["Home", "About", "Services", "Contact"]
    if package_data and "e-commerce" in package_data.get("name", "").lower():
        suggested_pages.extend(["Products", "Cart", "Checkout"])
    elif package_data and "portfolio" in package_data.get("name", "").lower():
        suggested_pages.insert(2, "Portfolio")

    # 8. High-level Context Summary
    context_summary = {
        "project_title": project.title,
        "package_name": package_data["name"] if package_data else "Standard Package",
        "has_logo": has_logo,
        "total_files": len(files_list),
        "total_files_by_category": {k: len(v) for k, v in files_by_category.items()},
        "suggested_pages": suggested_pages,
        "color_preferences": requirements_data.get("color_preferences") if requirements_data else "Modern Slate & Indigo",
        "advance_payment_verified": advance_paid,
        "total_paid_inr": total_paid,
        "revisions_count": len(project.revisions or []),
        "previous_builds_count": len(project.builds or []),
    }

    ready_for_build = bool(requirements_data and requirements_data.get("business_summary")) or bool(project.title)

    return {
        "project_id": project.id,
        "title": project.title,
        "status": project.status.value,
        "client_name": client_name,
        "client_email": client_email,
        "company_name": company_name,
        "client_phone": client_phone,
        "package": package_data,
        "requirements": requirements_data,
        "files": files_list,
        "files_by_category": files_by_category,
        "active_revision": active_revision_data,
        "advance_payment_verified": advance_paid,
        "ready_for_build": ready_for_build,
        "context_summary": context_summary,
    }
