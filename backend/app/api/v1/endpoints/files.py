"""
Secure Project Asset & File Upload System Endpoints.
Guarantees project access authorization, deterministic magic byte validation,
secure filename handling, physical storage abstraction, and audit logging.
"""
from typing import List, Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse as FastApiFileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.activity import ProjectActivity
from app.models.customer import Customer
from app.models.enums import FileCategory, UserRole
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.file import FileDeleteResponse, FileResponse
from app.services.file_validation import FileValidationError, validate_file_upload
from app.services.storage import storage_service

router = APIRouter()

MAX_PROJECT_FILES = 50


async def check_project_access(
    project_id: str,
    current_user: User,
    db: AsyncSession,
) -> Project:
    """
    Verify authenticated user has permission to view/modify the given project.
    Customers are strictly restricted to projects belonging to their customer account.
    Staff (Admin/Developer) can access all projects.
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if current_user.role == UserRole.CUSTOMER:
        cust_stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust_result = await db.execute(cust_stmt)
        customer = cust_result.scalar_one_or_none()

        if not customer or project.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this project",
            )

    return project


@router.post(
    "",
    response_model=APIResponse[FileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload project asset",
)
async def upload_file(
    project_id: str,
    file: UploadFile = File(...),
    file_category: FileCategory = Form(...),
    revision_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and secure a project asset.
    Validates magic bytes, enforces size limits (Image: 5MB, Document: 10MB),
    and enforces maximum 50 files per project.
    """
    await check_project_access(project_id, current_user, db)

    # 1. Enforce quota: 50 files maximum per project
    count_stmt = select(func.count(ProjectFile.id)).where(ProjectFile.project_id == project_id)
    file_count = (await db.execute(count_stmt)).scalar() or 0
    if file_count >= MAX_PROJECT_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project file quota reached ({MAX_PROJECT_FILES} files maximum).",
        )

    # 2. Read content safely
    try:
        content = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file payload.",
        )

    # 3. Deep validation: extension, magic signature, size, and category
    raw_filename = file.filename or "unnamed_file"
    try:
        safe_filename, safe_ext, canonical_mime = validate_file_upload(
            filename=raw_filename,
            content=content,
            category=file_category,
        )
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 4. Save to secure physical storage using safe random key
    stored_filename, relative_path = storage_service.save_file(
        project_id=project_id,
        content=content,
        extension=safe_ext,
    )

    # 5. Database insertion with atomic rollback and physical file cleanup on failure
    try:
        project_file = ProjectFile(
            project_id=project_id,
            revision_id=revision_id,
            file_category=file_category,
            original_filename=safe_filename,
            stored_filename=stored_filename,
            file_path=relative_path,
            mime_type=canonical_mime,
            file_size_bytes=len(content),
            uploaded_by_user_id=current_user.id,
        )
        db.add(project_file)

        # Log file upload in project audit timeline
        activity = ProjectActivity(
            project_id=project_id,
            performed_by_user_id=current_user.id,
            action_type="FILE_UPLOADED",
            note=f"Uploaded asset: {safe_filename} ({file_category.value})",
            is_visible_to_client=True,
        )
        db.add(activity)

        await db.commit()
        await db.refresh(project_file)
    except Exception:
        await db.rollback()
        storage_service.delete_file(relative_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record file metadata in database.",
        )

    return APIResponse(
        success=True,
        message="Asset uploaded successfully.",
        data=FileResponse.model_validate(project_file),
    )


@router.get(
    "",
    response_model=APIResponse[List[FileResponse]],
    summary="List project assets",
)
async def list_files(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all assets uploaded for a given project."""
    await check_project_access(project_id, current_user, db)

    stmt = (
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.created_at.desc())
    )
    result = await db.execute(stmt)
    files = result.scalars().all()

    return APIResponse(
        success=True,
        message="Project files retrieved.",
        data=[FileResponse.model_validate(f) for f in files],
    )


@router.get(
    "/{file_id}/download",
    summary="Download project asset securely",
)
async def download_file(
    project_id: str,
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download a file asset with security headers and private cache control.
    Requires authenticated access and project authorization.
    """
    await check_project_access(project_id, current_user, db)

    stmt = select(ProjectFile).where(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id,
    )
    result = await db.execute(stmt)
    project_file = result.scalar_one_or_none()

    if not project_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File asset not found in project.",
        )

    physical_path = storage_service.get_file_path(project_file.file_path)
    if not physical_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File asset missing on disk storage.",
        )

    # Safe Content-Disposition supporting UTF-8 filenames
    encoded_filename = quote(project_file.original_filename)
    safe_ascii_filename = project_file.original_filename.encode("ascii", "ignore").decode() or "download"
    content_disposition = (
        f'attachment; filename="{safe_ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    )

    return FastApiFileResponse(
        path=physical_path,
        media_type=project_file.mime_type,
        headers={
            "Content-Disposition": content_disposition,
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.delete(
    "/{file_id}",
    response_model=APIResponse[FileDeleteResponse],
    summary="Delete project asset",
)
async def delete_file(
    project_id: str,
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a project file and its physical storage asset.
    Audited in the project activity timeline.
    """
    await check_project_access(project_id, current_user, db)

    stmt = select(ProjectFile).where(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id,
    )
    result = await db.execute(stmt)
    project_file = result.scalar_one_or_none()

    if not project_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File asset not found in project.",
        )

    original_filename = project_file.original_filename
    relative_path = project_file.file_path

    # Delete record from database
    await db.delete(project_file)

    # Log deletion in activity timeline
    activity = ProjectActivity(
        project_id=project_id,
        performed_by_user_id=current_user.id,
        action_type="FILE_DELETED",
        note=f"Deleted asset: {original_filename}",
        is_visible_to_client=True,
    )
    db.add(activity)

    await db.commit()

    # Clean up physical storage
    storage_service.delete_file(relative_path)

    return APIResponse(
        success=True,
        message="Asset deleted successfully.",
        data=FileDeleteResponse(file_id=file_id, deleted=True),
    )
