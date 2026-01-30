"""
Email configuration loaded from environment.
Fails startup if not EMAIL_DRY_RUN and SMTP vars are missing.
"""
import os
import logging

logger = logging.getLogger(__name__)

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "JP Secure Staff")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

# Email behavior
EMAIL_DRY_RUN = os.getenv("EMAIL_DRY_RUN", "true").lower() in ("true", "1", "yes")
EMAIL_BIRTHDAY_SEND_HOUR = int(os.getenv("EMAIL_BIRTHDAY_SEND_HOUR", "9"))
AUTO_SEND_ID_CARD = os.getenv("AUTO_SEND_ID_CARD", "true").lower() in ("true", "1", "yes")

# App
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:3000")


def validate_email_config() -> None:
    """
    Validate email config. Raises RuntimeError if not DRY_RUN and SMTP is missing.
    Call at application startup.
    """
    if EMAIL_DRY_RUN:
        logger.info("[EMAIL_CONFIG] EMAIL_DRY_RUN=true — emails will be logged only, not sent")
        return
    missing = []
    if not SMTP_HOST:
        missing.append("SMTP_HOST")
    if not SMTP_FROM_EMAIL:
        missing.append("SMTP_FROM_EMAIL")
    # Username/password optional for some SMTP (e.g. local)
    if missing:
        raise RuntimeError(
            "Email is not in DRY_RUN mode but required env vars are missing: " + ", ".join(missing)
            + ". Set EMAIL_DRY_RUN=true to skip sending, or configure SMTP_HOST, SMTP_FROM_EMAIL, etc."
        )
    logger.info("[EMAIL_CONFIG] SMTP configured; emails will be sent")
