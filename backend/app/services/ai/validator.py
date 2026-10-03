import os
import re
from typing import List, Set
from app.schemas.ai_generation import (
    CodeValidationFinding,
    CodeValidationResult,
    GeneratedFile,
    GeneratedWebsite,
)

# Common regex patterns for secret leakage detection
SECRET_PATTERNS = [
    (r"(?i)(?:api_key|apikey|secret_key|private_key)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "Exposed API key or secret token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI or OpenAI-compatible Secret Key"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
    (r"rzp_(?:test|live)_[a-zA-Z0-9]{14,}", "Razorpay Key"),
]

# Patterns for dangerous execution in client-side code
DANGEROUS_PATTERNS = [
    (r"(?i)\bchild_process\b", "Server-side process invocation"),
    (r"(?i)\bexec\s*\(", "Dangerous string execution"),
    (r"(?i)\beval\s*\(", "Potential arbitrary JS evaluation"),
    (r"(?i)\b(?:require|import)\s*\(\s*['\"](?:fs|path|os|child_process)['\"]\s*\)", "Node.js system module import in client code"),
]


def sanitize_relative_path(path: str) -> str:
    """
    Sanitize and normalize a relative file path, preventing directory traversal.
    """
    normalized = path.replace("\\", "/").strip().lstrip("/")
    # Disallow '..' components
    parts = normalized.split("/")
    safe_parts = []
    for part in parts:
        part = part.strip()
        if not part or part == ".":
            continue
        if part == "..":
            raise ValueError(f"Path traversal attempted with '..' in path: {path}")
        # Disallow Windows drive letters or colons
        if ":" in part:
            raise ValueError(f"Drive letter or invalid character in path: {path}")
        safe_parts.append(part)

    if not safe_parts:
        raise ValueError(f"Invalid empty path: {path}")

    return "/".join(safe_parts)


class CodeValidator:
    """Validates generated website artifacts for syntax, security, and integrity."""

    def validate_website(self, website: GeneratedWebsite) -> CodeValidationResult:
        findings: List[CodeValidationFinding] = []

        if not website.files:
            findings.append(
                CodeValidationFinding(
                    file_path="",
                    severity="ERROR",
                    rule="EMPTY_WEBSITE",
                    message="Generated website contains no files.",
                )
            )
            return CodeValidationResult(is_valid=False, findings=findings, score=0.0)

        # 1. Entry file check
        entry_file_found = False
        file_paths: Set[str] = set()

        for f in website.files:
            # Path sanitization check
            try:
                sanitized = sanitize_relative_path(f.path)
                if sanitized in file_paths:
                    findings.append(
                        CodeValidationFinding(
                            file_path=f.path,
                            severity="ERROR",
                            rule="DUPLICATE_FILE",
                            message=f"Duplicate file path detected: '{f.path}'",
                        )
                    )
                file_paths.add(sanitized)
            except ValueError as err:
                findings.append(
                    CodeValidationFinding(
                        file_path=f.path,
                        severity="ERROR",
                        rule="PATH_TRAVERSAL",
                        message=str(err),
                    )
                )

            if f.path.lower() in (website.entry_file.lower(), "index.html"):
                entry_file_found = True

            # 2. Content validation
            self._validate_file_content(f, findings)

        if not entry_file_found:
            findings.append(
                CodeValidationFinding(
                    file_path=website.entry_file,
                    severity="ERROR",
                    rule="MISSING_ENTRY_FILE",
                    message=f"Required entry file '{website.entry_file}' was not found in generated files.",
                )
            )

        # 3. Cross-reference assets
        self._validate_asset_references(website.files, file_paths, findings)

        has_errors = any(finding.severity == "ERROR" for finding in findings)
        num_errors = sum(1 for f in findings if f.severity == "ERROR")
        num_warnings = sum(1 for f in findings if f.severity == "WARNING")

        score = max(0.0, 100.0 - (num_errors * 40.0) - (num_warnings * 10.0))

        return CodeValidationResult(
            is_valid=not has_errors,
            findings=findings,
            score=score,
        )

    def _validate_file_content(self, file: GeneratedFile, findings: List[CodeValidationFinding]) -> None:
        content = file.content or ""
        lower_path = file.path.lower()

        # Check for empty content
        if not content.strip():
            findings.append(
                CodeValidationFinding(
                    file_path=file.path,
                    severity="ERROR",
                    rule="EMPTY_FILE",
                    message="File content is completely empty.",
                )
            )
            return

        # HTML specific validation
        if lower_path.endswith(".html") or lower_path.endswith(".htm"):
            if "<html" not in content.lower() and "<body" not in content.lower():
                findings.append(
                    CodeValidationFinding(
                        file_path=file.path,
                        severity="WARNING",
                        rule="MALFORMED_HTML",
                        message="HTML file lacks standard <html> or <body> tags.",
                    )
                )

        # Security check: Secret leak detection
        for pattern, desc in SECRET_PATTERNS:
            if re.search(pattern, content):
                findings.append(
                    CodeValidationFinding(
                        file_path=file.path,
                        severity="ERROR",
                        rule="LEAKED_SECRET",
                        message=f"Potential secret or credential leaked in code: {desc}",
                    )
                )

        # Security check: Dangerous server-side execution
        for pattern, desc in DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                findings.append(
                    CodeValidationFinding(
                        file_path=file.path,
                        severity="ERROR",
                        rule="DANGEROUS_CODE",
                        message=f"Potentially dangerous pattern detected: {desc}",
                    )
                )

    def _validate_asset_references(
        self, files: List[GeneratedFile], known_paths: Set[str], findings: List[CodeValidationFinding]
    ) -> None:
        """Verify referenced local CSS/JS files exist in package."""
        ref_pattern = r'''(?:src|href)=["'](?!https?:\/\/|\/\/|#|mailto:|tel:)([^"']+)["']'''

        for f in files:
            if f.path.lower().endswith(".html"):
                matches = re.findall(ref_pattern, f.content, re.IGNORECASE)
                for ref in matches:
                    clean_ref = ref.split("?")[0].split("#")[0].strip().lstrip("/")
                    if not clean_ref:
                        continue
                    if clean_ref not in known_paths:
                        findings.append(
                            CodeValidationFinding(
                                file_path=f.path,
                                severity="WARNING",
                                rule="MISSING_LOCAL_ASSET",
                                message=f"Referenced local asset '{clean_ref}' not found in generated file list.",
                            )
                        )
