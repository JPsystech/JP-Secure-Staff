"""
Send one real test email to verify SMTP config.
Usage (from backend folder):
  python scripts/test_real_email.py your@email.com

Requires in .env:
  EMAIL_DRY_RUN=false
  SMTP_HOST=smtp.gmail.com (or your provider)
  SMTP_PORT=587
  SMTP_USERNAME=your@gmail.com
  SMTP_PASSWORD=your_app_password
  SMTP_FROM_EMAIL=your@gmail.com
  SMTP_FROM_NAME=JP Secure Staff
  SMTP_USE_TLS=true
"""
import sys
import os

# Load .env and add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_real_email.py <to_email>")
        print("Example: python scripts/test_real_email.py you@gmail.com")
        sys.exit(1)
    to_email = sys.argv[1].strip()

    from app.core.email_config import EMAIL_DRY_RUN, SMTP_HOST, SMTP_FROM_EMAIL
    if EMAIL_DRY_RUN:
        print("ERROR: Set EMAIL_DRY_RUN=false in .env to send real emails.")
        sys.exit(1)
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        print("ERROR: Set SMTP_HOST and SMTP_FROM_EMAIL (and SMTP_USERNAME/SMTP_PASSWORD) in .env")
        sys.exit(1)

    from app.core.database import SessionLocal
    from app.services.email_sender import send_email

    db = SessionLocal()
    try:
        subject = "JP Secure Staff – Test email"
        html = """
        <p>This is a test email from <strong>JP Secure Staff</strong>.</p>
        <p>If you received this, SMTP is configured correctly.</p>
        <p>— AKSHAR CONSULTANCY SERVICES</p>
        """
        text = "This is a test email from JP Secure Staff. If you received this, SMTP is configured correctly."
        log = send_email(
            db=db,
            to_email=to_email,
            subject=subject,
            html_body=html,
            text_body=text,
            template_key="TEST",
            entity_type="Test",
            entity_id=None,
        )
        print(f"Email sent. Status: {log.status}. Check inbox (and spam) for: {to_email}")
        if log.status == "FAILED" and log.error_message:
            print(f"Error: {log.error_message}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
