"""
Test birthday wish + ID card with real email to a given address.
Usage (from backend folder):
  python scripts/test_email_real_data.py iamsachin152003@gmail.com

1. Finds or uses the first person in DB, sets their email and DOB=today (for birthday).
2. Sets that person to SENT_TO_HR (so ID card can be sent).
3. Runs birthday job -> sends real birthday email.
4. Sends ID card email with PDF attachment.

Requires .env: EMAIL_DRY_RUN=false and SMTP_* configured.
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

def main():
    to_email = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not to_email:
        print("Usage: python scripts/test_email_real_data.py <email>")
        print("Example: python scripts/test_email_real_data.py iamsachin152003@gmail.com")
        sys.exit(1)

    from app.core.email_config import EMAIL_DRY_RUN, SMTP_HOST, SMTP_FROM_EMAIL
    if EMAIL_DRY_RUN:
        print("ERROR: Set EMAIL_DRY_RUN=false in .env to send real emails.")
        sys.exit(1)
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        print("ERROR: Configure SMTP_HOST and SMTP_FROM_EMAIL in .env")
        sys.exit(1)

    from app.core.database import SessionLocal
    from app.models.person import Person, PersonStatus
    from app.services.email_automation import run_birthday_job, send_id_card_email

    db = SessionLocal()
    try:
        # Use first person or create minimal one
        person = db.query(Person).first()
        if not person:
            print("ERROR: No person in database. Create at least one person (e.g. via UI) and run again.")
            sys.exit(1)

        # Set test email and DOB = today so birthday job picks them up
        person.email = to_email
        person.dob = date.today()
        person.status = PersonStatus.SENT_TO_HR  # So we can send ID card
        db.commit()
        db.refresh(person)
        print(f"Updated person id={person.id} name={person.name} email={person.email} dob={person.dob} status={person.status.value}")

        # 1. Birthday job -> sends birthday email to person
        print("\n--- 1. Running birthday job ---")
        n = run_birthday_job(db)
        print(f"Birthday job: emails_processed={n} (check inbox for: {to_email})")

        # 2. Send ID card email
        print("\n--- 2. Sending ID card email ---")
        log = send_id_card_email(db, person, skip_if_already_sent=False)
        print(f"ID card: status={log.status} (check inbox for: {to_email})")
        if log.error_message:
            print(f"  Error: {log.error_message}")

        print("\nDone. Check inbox (and spam) for:", to_email)
    finally:
        db.close()

if __name__ == "__main__":
    main()
