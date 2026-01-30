"""
Scheduler service: idempotent start with Postgres advisory lock.
Ensures birthday/email automation runs only once (no double-run with reload/workers).
"""
import logging
import os

logger = logging.getLogger(__name__)

# Module-level: only one process should hold the lock and run the scheduler
_started = False
_scheduler_instance = None

# Advisory lock key (constant); must be unique and same across all workers (single bigint)
SCHEDULER_LOCK_KEY = 0x4A505F5345435552  # unique constant for JP Secure Staff


def _try_advisory_lock(db) -> bool:
    """Try to acquire Postgres advisory lock. Returns True if acquired."""
    try:
        from sqlalchemy import text
        # pg_try_advisory_lock(bigint) - session-level lock
        r = db.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": SCHEDULER_LOCK_KEY})
        row = r.scalar()
        return row is True
    except Exception as e:
        logger.warning("[SCHEDULER] Advisory lock failed: %s", e)
        return False


def start_scheduler() -> bool:
    """
    Start the background scheduler if not already started and this process holds the advisory lock.
    Idempotent: safe to call multiple times; only one process will actually start.
    Returns True if scheduler was started, False if skipped (already started or lock not acquired).
    """
    global _started, _scheduler_instance

    if _started and _scheduler_instance is not None:
        logger.info("[SCHEDULER] Already started, skipping")
        return False

    enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() in ("true", "1", "yes")
    if not enabled:
        logger.info("[SCHEDULER] SCHEDULER_ENABLED=false, skipping")
        return False

    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        if not _try_advisory_lock(db):
            logger.info("[SCHEDULER] Another process holds scheduler lock, skipping")
            return False
    finally:
        db.close()

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.core.email_config import EMAIL_BIRTHDAY_SEND_HOUR
        from app.services.email_automation import run_birthday_job

        def _birthday_job():
            d = SessionLocal()
            try:
                run_birthday_job(d)
            except Exception as e:
                logger.exception("[BIRTHDAY_JOB] Error: %s", e)
            finally:
                d.close()

        _scheduler_instance = BackgroundScheduler()
        _scheduler_instance.add_job(_birthday_job, "cron", hour=EMAIL_BIRTHDAY_SEND_HOUR, minute=0)
        _scheduler_instance.start()
        _started = True
        logger.info("[SCHEDULER] Started (advisory lock acquired), birthday job at %s:00", EMAIL_BIRTHDAY_SEND_HOUR)
        return True
    except Exception as e:
        logger.warning("[SCHEDULER] Failed to start: %s", e)
        return False


def stop_scheduler() -> None:
    """Stop scheduler if running (e.g. on app shutdown)."""
    global _started, _scheduler_instance
    if _scheduler_instance is not None:
        try:
            _scheduler_instance.shutdown(wait=False)
            logger.info("[SCHEDULER] Stopped")
        except Exception as e:
            logger.warning("[SCHEDULER] Shutdown: %s", e)
        _scheduler_instance = None
        _started = False
