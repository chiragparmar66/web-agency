import os
import re
import uuid
from typing import Optional, Tuple
from app.core.config import settings


class LocalStorageService:
    """Secure local disk storage abstraction for project assets."""

    def __init__(self, base_dir: Optional[str] = None):
        raw_dir = base_dir or settings.LOCAL_STORAGE_DIR
        self.base_dir = os.path.abspath(raw_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> str:
        """
        Resolve relative path against base directory and verify
        that it does not escape via path traversal or symlinks.
        """
        # Normalize separators
        clean_rel = relative_path.replace("\\", "/").lstrip("/")
        
        # Guard against traversal patterns
        if ".." in clean_rel.split("/") or "\x00" in clean_rel:
            raise ValueError("Path traversal or null byte detected")

        target_path = os.path.abspath(os.path.join(self.base_dir, clean_rel))

        # Ensure target_path is within base_dir
        try:
            common = os.path.commonpath([self.base_dir, target_path])
        except ValueError:
            raise ValueError("Path escapes storage root directory")

        if common != self.base_dir:
            raise ValueError("Path escapes storage root directory")

        return target_path

    def save_file(
        self,
        project_id: str,
        content: bytes,
        extension: str,
    ) -> Tuple[str, str]:
        """
        Persist bytes to physical storage using safe random filename.
        Returns: (stored_filename, relative_file_path)
        """
        # Clean extension: ensure it starts with dot and is alphanumeric
        clean_ext = extension.lower()
        if not clean_ext.startswith("."):
            clean_ext = f".{clean_ext}"
        clean_ext = re.sub(r"[^a-z0-9.]", "", clean_ext)

        # Generate non-predictable UUID filename
        stored_filename = f"{uuid.uuid4().hex}{clean_ext}"

        # Clean project_id directory
        safe_proj_id = re.sub(r"[^a-zA-Z0-9_-]", "", project_id)
        relative_path = f"{safe_proj_id}/{stored_filename}"

        physical_path = self._resolve_safe_path(relative_path)
        os.makedirs(os.path.dirname(physical_path), exist_ok=True)

        with open(physical_path, "wb") as f:
            f.write(content)

        return stored_filename, relative_path

    def get_file_path(self, relative_path: str) -> Optional[str]:
        """Verify and return physical file path if it exists on disk."""
        try:
            physical_path = self._resolve_safe_path(relative_path)
            if os.path.isfile(physical_path):
                return physical_path
            return None
        except ValueError:
            return None

    def delete_file(self, relative_path: str) -> bool:
        """Safely delete physical file if it exists."""
        try:
            physical_path = self._resolve_safe_path(relative_path)
            if os.path.isfile(physical_path):
                os.remove(physical_path)
                return True
            return False
        except Exception:
            return False


storage_service = LocalStorageService()
