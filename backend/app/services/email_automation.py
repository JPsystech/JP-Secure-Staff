"""
Email automation: birthday job (daily) and ID card send.
Finds persons with DOB = today (day+month), skips missing email, prevents duplicates via EmailLog.
"""
import logging
from datetime import date, datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.person import Person
from app.models.email_log import EmailLog
from app.models.employment import Employment
from app.services.email_sender import send_email
from app.services.email_templates import render_birthday_email, render_id_card_email
from app.services.id_card_generator import generate_id_card_pdf

logger = logging.getLogger(__name__)

TEMPLATE_BIRTHDAY = "BIRTHDAY"
TEMPLATE_ID_CARD = "ID_CARD"
ENTITY_PERSON = "Person"


def run_birthday_job(db: Session) -> int:
    """
    Find persons with DOB matching today (day+month). Skip if no email.
    Prevent duplicates: skip if EmailLog already has BIRTHDAY for same entity_id with sent_at date = today.
    Returns count of emails sent (or DRY_RUN logged).
    """
    today = date.today()
    # Persons with DOB today (extract month/day in DB-agnostic way)
    # PostgreSQL: EXTRACT(MONTH FROM dob), EXTRACT(DAY FROM dob)
    persons_today = (
        db.query(Person)
        .filter(
            Person.dob.isnot(None),
            func.extract("month", Person.dob) == today.month,
            func.extract("day", Person.dob) == today.day,
        )
        .all()
    )
    sent = 0
    for person in persons_today:
        if not person.email or not person.email.strip():
            logger.info("[BIRTHDAY_JOB] Skip person %s: no email", person.id)
            continue
        # Prevent duplicates: already logged today (created_at) for this person
        existing_any = (
            db.query(EmailLog)
            .filter(
                EmailLog.template_key == TEMPLATE_BIRTHDAY,
                EmailLog.entity_id == str(person.id),
                func.date(EmailLog.created_at) == today,
            )
            .first()
        )
        if existing_any:
            logger.info("[BIRTHDAY_JOB] Skip person %s: already logged today", person.id)
            continue
        subject, html, text = render_birthday_email(person)
        send_email(
            db=db,
            to_email=person.email.strip(),
            subject=subject,
            html_body=html,
            text_body=text,
            template_key=TEMPLATE_BIRTHDAY,
            entity_type=ENTITY_PERSON,
            entity_id=str(person.id),
            log_metadata={"dob": person.dob.isoformat() if person.dob else None},
        )
        sent += 1
    logger.info("[BIRTHDAY_JOB] Processed %s persons with DOB today, sent=%s", len(persons_today), sent)
    return sent


def send_id_card_email(
    db: Session,
    person: Person,
    skip_if_already_sent: bool = True,
) -> EmailLog | None:
    """
    Generate ID card PDF, send email to person, log to EmailLog + audit.
    Returns EmailLog or None if skipped (no email or duplicate).
    """
    if not person.email or not person.email.strip():
        logger.info("[ID_CARD] Skip person %s: no email", person.id)
        return None
    if skip_if_already_sent:
        existing = (
            db.query(EmailLog)
            .filter(
                EmailLog.template_key == TEMPLATE_ID_CARD,
                EmailLog.entity_id == str(person.id),
            )
            .first()
        )
        if existing:
            logger.info("[ID_CARD] Skip person %s: already sent", person.id)
            return existing
    employment = (
        db.query(Employment)
        .filter(Employment.person_id == person.id, Employment.is_active == True)
        .first()
    )
    employee_code = employment.employee_code if employment else None
    department_name = None
    if person.created_dept_id:
        from app.models.department import Department
        dept = db.query(Department).filter(Department.id == person.created_dept_id).first()
        department_name = dept.name if dept else None
    designation = employment.employment_type.value if employment else "Staff"
    joining_date = person.created_at.date() if person.created_at else None
    pdf_bytes = generate_id_card_pdf(
        person_id=person.id,
        name=person.name,
        employee_code=employee_code,
        department_name=department_name,
        designation=designation,
        joining_date=joining_date,
    )
    attachment_name = "ID_Card.pdf"
    subject, html, text = render_id_card_email(person, attachment_name)
    return send_email(
        db=db,
        to_email=person.email.strip(),
        subject=subject,
        html_body=html,
        text_body=text,
        template_key=TEMPLATE_ID_CARD,
        entity_type=ENTITY_PERSON,
        entity_id=str(person.id),
        attachments=[(attachment_name, pdf_bytes, "application/pdf")],
        log_metadata={"employee_code": employee_code},
    )
