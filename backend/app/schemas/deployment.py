from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DeploymentStatus


class DeploymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    build_id: str
    version_number: int
    status: DeploymentStatus
    provider: str
    provider_deployment_id: Optional[str] = None
    live_url: Optional[str] = None
    error_message: Optional[str] = None
    deployed_by_user_id: Optional[str] = None
    deployed_at: Optional[datetime] = None
    deployment_metadata: Optional[Dict[str, Any]] = None
    smoke_test_status: Optional[str] = "NOT_RUN"
    smoke_test_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DeploymentTriggerRequest(BaseModel):
    provider: Optional[str] = Field(
        None,
        description="Optional deployment provider override ('simulated', 'vercel', 'netlify'). Defaults to configured provider.",
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Optional deployment notes")


class DeploymentEligibilityResponse(BaseModel):
    is_eligible: bool
    build_completed: bool
    admin_approved: bool
    client_approved: bool
    final_payment_cleared: bool
    artifact_available: bool
    package_price_inr: float
    total_paid_inr: float
    remaining_balance_inr: float
    blockers: List[str] = Field(default_factory=list)
