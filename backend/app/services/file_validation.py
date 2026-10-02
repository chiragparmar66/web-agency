import io
import os
import re
import zipfile
from typing import Optional, Set, Tuple
from app.models.enums import FileCategory

# Maximum sizes in bytes
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024      # 5 MB
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# Strict allowed extensions
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_DOCUMENT_EXTENSIONS: Set[str] = {".pdf", ".docx"}
ALLOWED_EXTENSIONS: Set[str] = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

# Explicitly forbidden extensions
FORBIDDEN_EXTENSIONS: Set[str] = {
    ".svg", ".html", ".htm", ".js", ".mjs", ".ts", ".jsx", ".tsx",
    ".exe", ".bat", ".cmd", ".dll", ".so", ".sh", ".bash", ".vbs",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".php", ".phtml", ".py", ".rb", ".pl", ".jar", ".war",
    ".jsp", ".asp", ".aspx", ".cgi",
}

# Canonical MIME mappings
MIME_BY_EXTENSION = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class FileValidationError(Exception):
    """Raised when file fails security or format validation."""
    pass


def sanitize_filename(filename: str) -> str:
    """Sanitize user-provided filename against traversal, null bytes, and control characters."""
    if not filename:
        return "unnamed_file"

    # Remove null bytes and control characters
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", filename)
    # Strip path components
    cleaned = os.path.basename(cleaned.replace("\\", "/"))
    # Replace dangerous characters while preserving unicode and alphanumeric
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", cleaned)
    # Collapse consecutive dots or spaces
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    cleaned = cleaned.strip(". ")

    if not cleaned:
        return "unnamed_file"
    return cleaned[:200]


def _detect_file_signature(content: bytes) -> Optional[str]:
    """
    Examine magic header bytes to deterministically determine file format.
    Does not trust client-reported Content-Type.
    """
    if len(content) < 4:
        return None

    # Check for executable signature (MZ header)
    if content.startswith(b"MZ"):
        return "exe"

    # PNG magic: 89 50 4E 47 0D 0A 1A 0A
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    # JPEG magic: FF D8 FF
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    # GIF magic: GIF87a or GIF89a
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return "gif"

    # WEBP magic: RIFF....WEBP
    if len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "webp"

    # PDF magic: %PDF-
    if content.startswith(b"%PDF-"):
        return "pdf"

    # DOCX magic: PK\x03\x04 and must be valid Office OpenXML document
    if content.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                namelist = zf.namelist()
                # Must contain [Content_Types].xml or word/ folder
                has_content_types = "[Content_Types].xml" in namelist
                has_word_dir = any(name.startswith("word/") for name in namelist)

                # Ensure no executable or dangerous files hidden inside
                for name in namelist:
                    lower_name = name.lower()
                    for ext in FORBIDDEN_EXTENSIONS:
                        if lower_name.endswith(ext):
                            return "malicious_zip"

                if has_content_types or has_word_dir:
                    return "docx"
                return "zip"
        except zipfile.BadZipFile:
            return None

    # Check for script / markup signatures in text payloads
    header_preview = content[:512].lower().strip()
    if b"<!doctype html" in header_preview or b"<html" in header_preview or b"<script" in header_preview:
        return "html"
    if b"<svg" in header_preview:
        return "svg"
    if b"<?php" in header_preview:
        return "php"

    return None


def validate_file_upload(
    filename: str,
    content: bytes,
    category: FileCategory,
) -> Tuple[str, str, str]:
    """
    Perform deep security and integrity validation on uploaded file.
    Returns: (safe_filename, safe_extension, canonical_mime_type)
    Raises: FileValidationError if file fails any security check.
    """
    # 1. Null and empty check
    if not content or len(content) == 0:
        raise FileValidationError("File is empty (0 bytes).")

    # 2. Sanitize and extract extension
    safe_filename = sanitize_filename(filename)
    _, ext = os.path.splitext(safe_filename)
    ext = ext.lower()

    if not ext:
        raise FileValidationError("File must have a valid extension.")

    # 3. Check explicitly forbidden formats
    if ext in FORBIDDEN_EXTENSIONS:
        raise FileValidationError(f"File type '{ext}' is strictly prohibited.")

    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file format '{ext}'. Allowed: PNG, JPG, JPEG, WEBP, GIF, PDF, DOCX."
        )

    # 4. Size validation based on media type
    content_size = len(content)
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        if content_size > MAX_IMAGE_SIZE_BYTES:
            raise FileValidationError(
                f"Image size exceeds 5 MB limit (file size: {content_size / (1024 * 1024):.1f} MB)."
            )
    elif ext in ALLOWED_DOCUMENT_EXTENSIONS:
        if content_size > MAX_DOCUMENT_SIZE_BYTES:
            raise FileValidationError(
                f"Document size exceeds 10 MB limit (file size: {content_size / (1024 * 1024):.1f} MB)."
            )

    # 5. Magic bytes signature validation
    signature_format = _detect_file_signature(content)
    if not signature_format:
        raise FileValidationError("File content does not match any valid supported file signature.")

    if signature_format in {"exe", "html", "svg", "php", "malicious_zip", "zip"}:
        raise FileValidationError(
            f"Dangerous or unrecognized file payload detected (identified as {signature_format})."
        )

    # Validate that extension matches actual payload signature
    if ext == ".png" and signature_format != "png":
        raise FileValidationError("File extension '.png' does not match payload signature.")
    if ext in {".jpg", ".jpeg"} and signature_format != "jpeg":
        raise FileValidationError("File extension does not match JPEG payload signature.")
    if ext == ".webp" and signature_format != "webp":
        raise FileValidationError("File extension '.webp' does not match WEBP payload signature.")
    if ext == ".gif" and signature_format != "gif":
        raise FileValidationError("File extension '.gif' does not match GIF payload signature.")
    if ext == ".pdf" and signature_format != "pdf":
        raise FileValidationError("File extension '.pdf' does not match PDF payload signature.")
    if ext == ".docx" and signature_format != "docx":
        raise FileValidationError("File extension '.docx' does not match Word document structure.")

    # 6. Category compatibility verification
    if category in {FileCategory.LOGO, FileCategory.IMAGE, FileCategory.PREVIEW_SCREENSHOT}:
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise FileValidationError(
                f"Category '{category.value}' requires an image file (PNG, JPG, WEBP, GIF)."
            )
    elif category == FileCategory.DOCUMENT:
        if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise FileValidationError(
                f"Category '{category.value}' requires a document file (PDF, DOCX)."
            )

    canonical_mime = MIME_BY_EXTENSION[ext]
    return safe_filename, ext, canonical_mime
