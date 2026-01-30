"""
Email templates: birthday and ID card.
Branded: JP Secure Staff / AKSHAR CONSULTANCY SERVICES.
"""
from typing import Any, Optional

BRAND = "JP Secure Staff"
COMPANY = "AKSHAR CONSULTANCY SERVICES"
FOOTER = (
    "This is an automated message. Please do not reply to this email. "
    "For queries, contact your HR or system administrator."
)


def _wrap_html(body: str, subject_hint: str = "") -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{subject_hint or 'Message'}</title></head>
<body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="border-bottom: 2px solid #1a365d; padding-bottom: 10px; margin-bottom: 20px;">
    <strong style="color: #1a365d;">{BRAND}</strong><br/>
    <span style="font-size: 12px; color: #666;">{COMPANY}</span>
  </div>
  {body}
  <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; font-size: 11px; color: #888;">
    {FOOTER}
  </div>
</body>
</html>"""


def render_birthday_email(person_or_user: Any) -> tuple[str, str, str]:
    """
    Returns (subject, html_body, text_body) for birthday greeting.
    person_or_user must have: name, email (optional for validation), dob (optional for display).
    """
    name = getattr(person_or_user, "name", None) or getattr(person_or_user, "full_name", "Team Member")
    subject = f"Happy Birthday, {name}!"
    body = f"""
    <p>Dear <strong>{name}</strong>,</p>
    <p>Wishing you a very Happy Birthday from everyone at {COMPANY}!</p>
    <p>We hope your day is filled with joy and success.</p>
    <p>Best regards,<br/><strong>{BRAND} Team</strong></p>
    """
    html = _wrap_html(body.strip(), subject)
    text = f"Dear {name},\n\nWishing you a very Happy Birthday from everyone at {COMPANY}!\n\nBest regards,\n{BRAND} Team"
    return subject, html, text


def render_id_card_email(person_or_user: Any, attachment_name: str = "ID_Card.pdf") -> tuple[str, str, str]:
    """
    Returns (subject, html_body, text_body) for ID card email.
    person_or_user should have name (and optionally email for validation).
    """
    name = getattr(person_or_user, "name", None) or getattr(person_or_user, "full_name", "Team Member")
    subject = f"Your ID Card – {BRAND}"
    body = f"""
    <p>Dear <strong>{name}</strong>,</p>
    <p>Please find your official ID card attached to this email.</p>
    <p>Keep it safe and present it when required at the workplace.</p>
    <p>Best regards,<br/><strong>{BRAND} Team</strong></p>
    """
    html = _wrap_html(body.strip(), subject)
    text = f"Dear {name},\n\nPlease find your official ID card attached ({attachment_name}).\n\nBest regards,\n{BRAND} Team"
    return subject, html, text
