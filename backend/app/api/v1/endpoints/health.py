"""
Health and readiness endpoints for production monitoring.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    """
    Liveness: fast, no DB. Always 200.
    """
    return {
        "status": "ok",
        "service": "jp_secure_staff",
        "time": datetime.now(timezone.utc).isoformat(),
    }


def _check_db() -> Literal["ok", "fail"]:
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return "ok"
        finally:
            db.close()
    except Exception as e:
        logger.warning("Readiness DB check failed: %s", e)
        return "fail"


def _check_storage() -> Literal["ok", "fail"]:
    try:
        from app.core.config import settings
        from app.core.storage import storage_service
        if getattr(settings, "USE_MINIO", False):
            if not getattr(storage_service, "available", False):
                return "fail"
            try:
                storage_service.client.bucket_exists(storage_service.bucket)
                return "ok"
            except Exception:
                return "fail"
        else:
            # Local FS: ensure base path exists and is writable
            from pathlib import Path
            base = getattr(storage_service, "base_path", None)
            if base is None:
                return "ok"
            base = Path(base) if not isinstance(base, Path) else base
            base.mkdir(parents=True, exist_ok=True)
            test_file = base / ".ready_check"
            try:
                test_file.write_text("ok")
                test_file.unlink()
                return "ok"
            except Exception:
                return "fail"
    except Exception as e:
        logger.warning("Readiness storage check failed: %s", e)
        return "fail"


def _check_email() -> Literal["ok", "skipped", "fail"]:
    try:
        dry_run = os.getenv("EMAIL_DRY_RUN", "true").lower() in ("true", "1", "yes")
        if dry_run:
            return "skipped"
        host = os.getenv("SMTP_HOST", "")
        from_email = os.getenv("SMTP_FROM_EMAIL", "")
        if not host or not from_email:
            prod = os.getenv("ENVIRONMENT", "development").lower() == "production"
            return "fail" if prod else "skipped"
        return "ok"
    except Exception:
        return "skipped"


@router.get("/ready")
async def ready():
    """
    Readiness: DB, storage, email config. 200 if ok/degraded, 503 if fail.
    """
    db_status = _check_db()
    storage_status = _check_storage()
    email_status = _check_email()

    details = {
        "db": db_status,
        "storage": storage_status,
        "email": email_status,
    }
    overall = "ok"
    if db_status == "fail":
        overall = "fail"
    elif storage_status == "fail" or email_status == "fail":
        overall = "degraded"

    payload = {
        "status": overall,
        "db": db_status,
        "storage": storage_status,
        "email": email_status,
        "details": details,
    }
    status_code = 503 if overall == "fail" else 200
    return JSONResponse(content=payload, status_code=status_code)
