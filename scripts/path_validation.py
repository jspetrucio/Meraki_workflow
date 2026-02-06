"""
Path validation utilities to prevent path traversal attacks.

Provides functions to validate and sanitize user-supplied paths
and path components (client names, filenames, snapshot IDs).
"""

import re
from pathlib import Path

from fastapi import HTTPException

# Base directory for all client data
_BASE_DIR = Path("clients").resolve()

# Pattern for safe path components (no path separators, no ..)
_SAFE_COMPONENT_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._\-]{0,127}$')


def validate_path_within_base(user_path: str, base_dir: Path | None = None) -> Path:
    """
    Validate that a user-supplied path resolves within the allowed base directory.

    Args:
        user_path: The raw path string from user input.
        base_dir: Allowed base directory (defaults to clients/).

    Returns:
        Resolved, validated Path object.

    Raises:
        HTTPException 400: If path escapes the base directory or contains
                           suspicious components.
    """
    if base_dir is None:
        base_dir = _BASE_DIR

    resolved_base = base_dir.resolve()

    # Reject paths with .. components before resolving
    path_obj = Path(user_path)
    if ".." in path_obj.parts:
        raise HTTPException(
            status_code=400,
            detail="Invalid path: directory traversal not allowed."
        )

    # Resolve to absolute and check containment
    resolved = path_obj.resolve()
    try:
        resolved.relative_to(resolved_base)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid path: outside allowed directory."
        )

    return resolved


def validate_path_component(value: str, label: str = "parameter") -> str:
    """
    Validate a single path component (client name, filename, snapshot ID).

    Ensures the value does not contain path separators, '..' sequences,
    or other dangerous characters.

    Args:
        value: The raw string from a URL parameter or request body.
        label: Human-readable label for error messages (e.g., "client", "filename").

    Returns:
        The validated string (unchanged if valid).

    Raises:
        HTTPException 400: If the value contains dangerous characters.
    """
    if not value:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {label}: must not be empty."
        )

    # Check for path separators and traversal
    if "/" in value or "\\" in value or ".." in value:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {label}: contains forbidden characters."
        )

    # Enforce safe character pattern
    if not _SAFE_COMPONENT_PATTERN.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {label}: must be alphanumeric with .-_ only, max 128 chars."
        )

    return value
