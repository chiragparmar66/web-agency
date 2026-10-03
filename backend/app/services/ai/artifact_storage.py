import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.ai_generation import BuildManifest, GeneratedWebsite
from app.services.ai.validator import sanitize_relative_path


SAFE_TEXT_EXTENSIONS = {
    ".html", ".htm", ".css", ".js", ".mjs", ".json", ".svg", ".txt", ".md", ".xml", ".webmanifest"
}


class ArtifactStorage:
    """Manages isolated disk storage of generated website artifacts and manifests."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.ARTIFACT_STORAGE_PATH).resolve()

    def get_build_directory(self, project_id: str, version_number: int) -> Path:
        """Get canonical directory for a specific project build version."""
        # Sanitize project_id
        safe_proj_id = project_id.replace("/", "").replace("\\", "").strip()
        dir_path = (self.base_path / safe_proj_id / f"v{version_number}").resolve()

        # Strict containment verification
        if not str(dir_path).startswith(str(self.base_path)):
            raise ValueError(f"Path traversal detected for build directory: {dir_path}")

        return dir_path

    get_build_dir = get_build_directory

    def save_build(
        self,
        project_id: str,
        build_id: str,
        version_number: int,
        website: GeneratedWebsite,
        providers_used: Dict[str, str],
        spec_summary: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Write generated website files and manifest to disk.
        Returns the absolute string path to the build directory.
        """
        build_dir = self.get_build_directory(project_id, version_number)
        build_dir.mkdir(parents=True, exist_ok=True)

        manifest_files: List[Dict[str, Any]] = []

        for gen_file in website.files:
            safe_rel_path = sanitize_relative_path(gen_file.path)
            target_path = (build_dir / safe_rel_path).resolve()

            # Ensure file is inside build_dir
            if not str(target_path).startswith(str(build_dir)):
                raise ValueError(f"File path traversal attempted: {gen_file.path}")

            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(gen_file.content, encoding="utf-8")

            manifest_files.append({
                "path": safe_rel_path,
                "file_type": gen_file.file_type,
                "size_bytes": len(gen_file.content.encode("utf-8")),
            })

        # Save manifest.json
        manifest = BuildManifest(
            project_id=project_id,
            build_id=build_id,
            version_number=version_number,
            entry_file=website.entry_file,
            files=manifest_files,
            generated_at=datetime.now(timezone.utc).isoformat(),
            providers_used=providers_used,
            spec_summary=spec_summary or {},
        )

        manifest_path = build_dir / "manifest.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        return str(build_dir)

    def read_manifest(self, project_id: str, version_number: int) -> Optional[BuildManifest]:
        """Read manifest.json for a build if it exists."""
        build_dir = self.get_build_directory(project_id, version_number)
        manifest_path = build_dir / "manifest.json"
        if not manifest_path.exists():
            return None
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return BuildManifest.model_validate(data)

    def list_files(self, project_id: str, version_number: int) -> List[str]:
        """List all relative file paths inside a build directory."""
        build_dir = self.get_build_directory(project_id, version_number)
        if not build_dir.exists():
            return []
        files = []
        for p in build_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(build_dir).as_posix()
                files.append(rel)
        return files

    def list_files_metadata(self, project_id: str, version_number: int) -> List[Dict[str, Any]]:
        """List all files inside a build directory with metadata (path, file_type, size_bytes, is_text)."""
        build_dir = self.get_build_directory(project_id, version_number)
        if not build_dir.exists():
            return []
        files = []
        for p in sorted(build_dir.rglob("*")):
            if p.is_file():
                rel = p.relative_to(build_dir).as_posix()
                ext = p.suffix.lower()
                is_text = ext in SAFE_TEXT_EXTENSIONS
                file_type = ext.lstrip(".") or "txt"
                size = p.stat().st_size
                files.append({
                    "path": rel,
                    "file_type": file_type,
                    "size_bytes": size,
                    "is_text": is_text,
                })
        return files

    def read_file(self, project_id: str, version_number: int, relative_path: str) -> Optional[str]:
        """Read content of a specific file inside a build directory."""
        safe_rel = sanitize_relative_path(relative_path)
        build_dir = self.get_build_directory(project_id, version_number)
        target = (build_dir / safe_rel).resolve()
        if not str(target).startswith(str(build_dir)) or not target.exists() or not target.is_file():
            return None
        return target.read_text(encoding="utf-8")

    def read_file_safe(
        self,
        project_id: str,
        version_number: int,
        relative_path: str,
        max_bytes: int = 1_048_576,
    ) -> tuple[Optional[str], bool, bool, int]:
        """
        Safely read a file's content up to max_bytes.
        Returns: (content_str, is_text, is_truncated, total_size_bytes)
        """
        safe_rel = sanitize_relative_path(relative_path)
        build_dir = self.get_build_directory(project_id, version_number)
        target = (build_dir / safe_rel).resolve()
        if not str(target).startswith(str(build_dir)) or not target.exists() or not target.is_file():
            return None, False, False, 0

        ext = target.suffix.lower()
        is_text = ext in SAFE_TEXT_EXTENSIONS
        total_size = target.stat().st_size

        if not is_text:
            return None, False, False, total_size

        is_truncated = False
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            if total_size > max_bytes:
                content = f.read(max_bytes)
                is_truncated = True
            else:
                content = f.read()

        return content, True, is_truncated, total_size
