"""
Centralized uppercase normalization for ID-like fields across the application.
Any field whose key matches these patterns is stored and displayed in UPPERCASE.
"""
from typing import Any

# Keys (lowercase) that contain any of these substrings will be uppercased
UPPERCASE_KEY_PATTERNS = (
    "code", "id", "pan", "emp", "employee", "reference", "irn",
    "aadhar", "aadhaar", "ifsc"
)


def _key_matches(key: str) -> bool:
    k = (key or "").lower()
    return any(p in k for p in UPPERCASE_KEY_PATTERNS)


def normalize_uppercase_fields(data: dict) -> dict:
    """
    Return a new dict with string values uppercased for keys matching ID-like patterns.
    Only affects string values; None and non-strings are left unchanged.
    """
    if not data or not isinstance(data, dict):
        return data
    out = {}
    for key, value in data.items():
        if _key_matches(key) and value is not None and isinstance(value, str):
            stripped = value.strip()
            out[key] = stripped.upper() if stripped else value
        else:
            out[key] = value
    return out
