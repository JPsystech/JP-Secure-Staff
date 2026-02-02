"""
Startup config validation: returns warnings + errors.
Never log secrets; mask in startup logs.
"""
import os
from typing import List, Tuple


def mask_db_url(url: str) -> str:
    """Return DATABASE_URL with password masked."""
    if not url or url == "NOT_SET":
        return url
    if "@" in url:
        parts = url.split("@", 1)
        return "***@" + parts[1] if len(parts) == 2 else url
    return url[:50] + "..." if len(url) > 50 else url


def validate_config() -> Tuple[List[str], List[str]]:
    """
    Validate app config. Returns (warnings, errors).
    In production (ENVIRONMENT=production), missing required vars are errors and exit.
    In dev, missing vars are warnings; app may still fail when connecting.
    """
    warnings: List[str] = []
    errors: List[str] = []
    is_production = os.getenv("ENVIRONMENT", "").lower() == "production"

    db_url = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
    if not db_url or db_url == "NOT_SET":
        if is_production:
            errors.append("DATABASE_URL is not set")
        else:
            warnings.append("DATABASE_URL is not set (set in .env for backend)")

    secret = (os.getenv("SECRET_KEY") or "").strip()
    if not secret or len(secret) < 16:
        if is_production:
            errors.append("SECRET_KEY is missing or too short (min 16 characters)")
        else:
            warnings.append("SECRET_KEY is missing or too short (use at least 16 characters)")

    use_minio = os.getenv("USE_MINIO", "false").lower() in ("true", "1", "yes")
    if use_minio:
        if not os.getenv("MINIO_ENDPOINT"):
            warnings.append("USE_MINIO=True but MINIO_ENDPOINT not set")
        if not os.getenv("MINIO_ACCESS_KEY"):
            warnings.append("USE_MINIO=True but MINIO_ACCESS_KEY not set")

    email_dry_run = os.getenv("EMAIL_DRY_RUN", "true").lower() in ("true", "1", "yes")
    if not email_dry_run:
        if not os.getenv("SMTP_HOST"):
            errors.append("EMAIL_DRY_RUN=false but SMTP_HOST not set")
        if not os.getenv("SMTP_FROM_EMAIL"):
            errors.append("EMAIL_DRY_RUN=false but SMTP_FROM_EMAIL not set")

    return warnings, errors
