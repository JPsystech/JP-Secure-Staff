"""
Email sender service: send_email with TLS, retries, DRY_RUN.
Always writes to EmailLog and calls audit_logger for EMAIL_SENT/FAILED/SKIPPED/DRY_RUN.
"""
import logging
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.email_config import (
    EMAIL_DRY_RUN,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_USE_TLS,
)
from app.models.email_log import EmailLog
from app.services.audit_logger import log_audit_event

logger = logging.getLogger(__name__)

SMTP_TIMEOUT = 30
MAX_RETRIES = 3


def _send_via_smtp(to_email: str, subject: str, html_body: str, text_body: Optional[str], cc: Optional[List[str]], attachments: Optional[List[tuple]]) -> tuple[str, Optional[str]]:
    """
    Send one email via SMTP. Returns (provider_message_id_or_empty, error_message_or_None).
    """
    msg = EmailMessage()
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>" if SMTP_FROM_NAME else SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.set_content(text_body if text_body else "(HTML content)")
    msg.add_alternative(html_body, subtype="html")
    if attachments:
        for filename, content, mime_type in attachments:
            msg.add_attachment(content, maintype=mime_type.split("/")[0], subtype=mime_type.split("/")[-1], filename=filename)

    recipients = [to_email] + (cc or [])
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                if SMTP_USERNAME and SMTP_PASSWORD:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg, to_addrs=recipients)
            return "", None
        except Exception as e:
            last_error = str(e)
            logger.warning("SMTP send attempt %s failed: %s", attempt + 1, last_error)
    return "", last_error


def send_email(
    db: Session,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    cc: Optional[List[str]] = None,
    attachments: Optional[List[tuple]] = None,
    template_key: str = "",
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    log_metadata: Optional[Dict[str, Any]] = None,
) -> EmailLog:
    """
    Send email (or simulate if EMAIL_DRY_RUN). Always creates EmailLog and audit event.
    attachments: list of (filename, bytes_content, mime_type) e.g. ("id_card.pdf", pdf_bytes, "application/pdf")
    """
    log_metadata = log_metadata or {}
    status = "DRY_RUN"
    error_message = None
    provider_message_id = None
    sent_at = None

    if EMAIL_DRY_RUN:
        status = "DRY_RUN"
        logger.info("[EMAIL] DRY_RUN: would send to %s subject=%s template_key=%s", to_email, subject, template_key)
    else:
        if not SMTP_HOST or not SMTP_FROM_EMAIL:
            status = "SKIPPED"
            error_message = "SMTP not configured"
            logger.warning("[EMAIL] SKIPPED: SMTP not configured")
        else:
            provider_message_id, error_message = _send_via_smtp(to_email, subject, html_body, text_body, cc, attachments)
            if error_message:
                status = "FAILED"
                logger.error("[EMAIL] FAILED to %s: %s", to_email, error_message)
            else:
                status = "SENT"
                sent_at = datetime.now(timezone.utc)
                logger.info("[EMAIL] SENT to %s subject=%s", to_email, subject)

    cc_json = list(cc) if cc else None
    if isinstance(entity_id, UUID):
        entity_id = str(entity_id)

    email_log = EmailLog(
        to_email=to_email,
        cc_emails=cc_json,
        subject=subject,
        template_key=template_key,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        error_message=error_message,
        provider_message_id=provider_message_id or None,
        sent_at=sent_at,
        metadata_=dict(log_metadata),
    )
    db.add(email_log)
    db.commit()
    db.refresh(email_log)

    action_type = {"SENT": "EMAIL_SENT", "FAILED": "EMAIL_FAILED", "SKIPPED": "EMAIL_SKIPPED", "DRY_RUN": "EMAIL_DRY_RUN"}.get(status, "EMAIL_DRY_RUN")
    log_audit_event(
        db=db,
        action_type=action_type,
        entity_type=entity_type or "Email",
        entity_id=entity_id,
        actor_user_id=None,
        action_metadata={
            "template_key": template_key,
            "to_email": to_email,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": status,
            "email_log_id": str(email_log.id),
            **log_metadata,
        },
        ip_address=None,
        user_agent=None,
    )
    return email_log
