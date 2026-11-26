"""
BiofilmAI Backend — Input validation for uploaded files and form data.

Validates:
- File extensions and MIME types
- File size limits
- Required fields
- PII detection (optional basic checks)
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import UploadFile

from config import settings


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_file(
    file: Optional[UploadFile],
    field_name: str,
    allowed_extensions: list[str],
    max_size_mb: int | None = None,
) -> None:
    """
    Validate an uploaded file.
    
    Raises ValidationError if validation fails.
    """
    if file is None:
        return  # Files are optional for some modalities

    if file.filename is None or file.filename.strip() == "":
        raise ValidationError(field_name, "Filename is empty")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            field_name,
            f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}",
        )

    max_mb = max_size_mb or settings.MAX_UPLOAD_SIZE_MB
    max_bytes = max_mb * 1024 * 1024
    if file.size and file.size > max_bytes:
        raise ValidationError(
            field_name,
            f"File too large ({file.size} bytes). Maximum: {max_mb} MB",
        )


def validate_sample_info(sample_info: dict) -> None:
    """Validate sample information fields."""
    if not sample_info.get("sampleId", "").strip():
        raise ValidationError("sampleId", "Sample ID is required")
    if not sample_info.get("studyId", "").strip():
        raise ValidationError("studyId", "Study ID is required")
    if not sample_info.get("sampleType", "").strip():
        raise ValidationError("sampleType", "Sample type is required")


def validate_clinical_data(clinical_data: dict) -> None:
    """Validate clinical data fields."""
    chronicity = clinical_data.get("chronicityDays", 0)
    if not isinstance(chronicity, (int, float)):
        raise ValidationError("chronicityDays", "Must be a number")
    if chronicity < 0 or chronicity > 3650:
        raise ValidationError("chronicityDays", "Must be between 0 and 3650")


def basic_pii_check(sample_info: dict) -> list[str]:
    """
    Basic PII detection — returns warnings (not errors).
    
    This is a simple heuristic and should not be relied upon for
    full PII detection.
    """
    warnings = []
    for key in ("sampleId", "studyId", "notes"):
        value = str(sample_info.get(key, "")).lower()
        for pii_marker in ["ssn", "social security", "phone", "address", "email"]:
            if pii_marker in value:
                warnings.append(
                    f"Possible PII detected in '{key}': may contain {pii_marker}"
                )
    return warnings