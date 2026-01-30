"""Email Log Model — traceability for all sent/skipped/dry-run emails."""
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.core.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    to_email = Column(String, nullable=False, index=True)
    cc_emails = Column(JSONB, nullable=True)  # list of strings
    subject = Column(String, nullable=False)
    template_key = Column(String, nullable=False, index=True)  # BIRTHDAY, ID_CARD
    entity_type = Column(String, nullable=True, index=True)  # User, Person
    entity_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, index=True)  # SENT, FAILED, SKIPPED, DRY_RUN
    error_message = Column(Text, nullable=True)
    provider_message_id = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    metadata_ = Column("metadata", JSONB, nullable=True)  # dob, user_id, etc.
