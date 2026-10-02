from fastapi import APIRouter
from app.api.v1.endpoints import (
    admin,
    auth,
    dashboard,
    files,
    health,
    inquiries,
    messages,
    payments,
    pricing,
    projects,
    requirements,
    revisions,
    showcase,
)

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Profile"])
api_router.include_router(inquiries.router, prefix="/inquiries", tags=["Inquiries & Contact"])
api_router.include_router(showcase.router, tags=["Public Showcase"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Pricing Packages"])
api_router.include_router(projects.router, prefix="/projects", tags=["Customer Projects"])
api_router.include_router(
    requirements.router,
    prefix="/projects/{project_id}/requirements",
    tags=["Project Requirements"],
)
api_router.include_router(
    messages.router,
    prefix="/projects/{project_id}/messages",
    tags=["Project Messages"],
)
api_router.include_router(
    files.router,
    prefix="/projects/{project_id}/files",
    tags=["Project Files"],
)
api_router.include_router(
    revisions.router,
    prefix="/projects/{project_id}/revisions",
    tags=["Project Revisions"],
)
api_router.include_router(payments.router, prefix="/payments", tags=["Secure Payments"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Customer Dashboard"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Operations"])
