"""
JP Secure Staff FastAPI Application

CRITICAL: Windows event loop policy must be set BEFORE any async operations.
This must be at the very top, before any other imports that might create event loops.
"""
import sys
import asyncio

# Load .env so email_config and other os.getenv() readers see env vars
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# CRITICAL FIX for Windows: Set event loop policy for Playwright async subprocess support
# This MUST be done before any event loop is created (before FastAPI/uvicorn starts)
if sys.platform.startswith("win"):
    # WindowsSelectorEventLoopPolicy doesn't support subprocess_exec
    # WindowsProactorEventLoopPolicy is required for Playwright's subprocess operations
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
import logging.handlers
import traceback
import os

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.core.config import settings
from app.api.v1.router import api_router

# Logging: console + rotating file (20MB, keep 10 files)
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_root = logging.getLogger()
_root.setLevel(logging.INFO)
_root.handlers.clear()
_console = logging.StreamHandler()
_console.setFormatter(_fmt)
_root.addHandler(_console)
try:
    _file = logging.handlers.RotatingFileHandler(
        os.path.join(_LOG_DIR, "app.log"),
        maxBytes=20 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    _file.setFormatter(_fmt)
    _root.addHandler(_file)
except Exception:
    pass
logger = logging.getLogger(__name__)

app = FastAPI(
    title="JP Secure Staff API",
    description="Backend API for JP Secure Staff system",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    import os
    from app.core.config_validation import validate_config, mask_db_url

    # Config validation + masked logs (never log secrets)
    warnings, errors = validate_config()
    db_url = os.getenv("DATABASE_URL", "NOT_SET")
    logger.info("[STARTUP] DATABASE_URL: %s", mask_db_url(db_url))
    for w in warnings:
        logger.warning("[STARTUP] Config warning: %s", w)
    for e in errors:
        logger.error("[STARTUP] Config error: %s", e)
    if errors:
        raise RuntimeError("Config validation failed: " + "; ".join(errors))

    if sys.platform.startswith("win"):
        current_policy = type(asyncio.get_event_loop_policy()).__name__
        logger.info("[STARTUP] Windows event loop policy: %s", current_policy)

    # Email config (fail if not DRY_RUN and SMTP missing)
    try:
        from app.core.email_config import validate_email_config
        validate_email_config()
    except RuntimeError as e:
        logger.error("[STARTUP] Email config: %s", e)
        raise

    # DB verified via permission seeding (lightweight)
    try:
        from app.services.permission_seeder import seed_permissions
        seeded, updated = seed_permissions()
        logger.info("[STARTUP] Permission seeding: %s new, %s updated", seeded, updated)
    except Exception as e:
        logger.error("[STARTUP] Permission seeding failed: %s", e, exc_info=True)
        # Don't fail startup - log and continue

    # Templates table schema self-check (warning only; do not crash)
    try:
        from sqlalchemy import text
        from app.core.database import SessionLocal
        required_columns = {"name", "type", "is_active", "active_revision_id", "created_at", "updated_at"}
        db = SessionLocal()
        try:
            r = db.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'templates'"
            ))
            present = {row[0] for row in r}
            missing = required_columns - present
            if missing:
                logger.warning(
                    "[STARTUP] templates table missing columns: %s. Run: alembic upgrade head",
                    sorted(missing),
                )
        finally:
            db.close()
    except Exception as e:
        logger.warning("[STARTUP] Templates table self-check skipped: %s", e)

    # Scheduler: start only once (advisory lock); after DB is reachable
    try:
        from app.services.scheduler import start_scheduler
        started = start_scheduler()
        if not started:
            logger.info("[STARTUP] Scheduler skipped (already running elsewhere or disabled)")
    except Exception as e:
        logger.warning("[STARTUP] Scheduler: %s", e)

    logger.info("[STARTUP] API starting on port 8000")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on shutdown."""
    try:
        from app.services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception as e:
        logger.warning("[SHUTDOWN] Scheduler: %s", e)

# CORS: must be added before routers so preflight OPTIONS returns 200 and browser allows POST.
# Allows Vercel frontend + local dev; OPTIONS (preflight) are handled by CORSMiddleware and do not hit auth.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jp-secure-staff.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,  # Required when frontend uses credentials: 'include'
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers to prevent crashes
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions to prevent server crashes"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Request method: {request.method}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error. Please try again later.",
            "error_type": type(exc).__name__
        }
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors gracefully"""
    logger.error(f"Database error: {type(exc).__name__}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database service temporarily unavailable. Please try again later.",
            "error_type": "DatabaseError"
        }
    )

@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    """Handle database connection errors"""
    logger.error(f"Database connection error: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database connection failed. Please check database service.",
            "error_type": "DatabaseConnectionError"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "JP Secure Staff API"}

@app.get("/health")
async def health():
    """Liveness: always 200, no DB check."""
    return {"status": "healthy", "service": "JP Secure Staff API", "version": "1.0.0"}


@app.get("/ready")
async def ready():
    """Readiness: 200 if DB reachable, 503 otherwise."""
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok", "db": "ok"}
        finally:
            db.close()
    except Exception as e:
        logger.warning("Ready check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "fail", "db": "fail", "detail": "Database unreachable"},
        )

