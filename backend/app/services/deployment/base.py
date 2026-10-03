from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DeploymentResult:
    success: bool
    live_url: Optional[str] = None
    provider_deployment_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    smoke_test_status: str = "NOT_RUN"
    smoke_test_details: Optional[Dict[str, Any]] = None


class DeploymentProvider(ABC):
    """Abstract base class for static website deployment providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks whether the provider is configured and available."""
        pass

    @abstractmethod
    async def deploy(
        self,
        project_id: str,
        project_number: str,
        build_id: str,
        version_number: int,
        artifact_path: Path,
    ) -> DeploymentResult:
        """Deploy build artifacts to production."""
        pass
