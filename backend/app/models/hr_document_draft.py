"""HR document draft: edited content per person per doc type (APPOINTMENT/DECLARATION)."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class HrDocumentDraft(Base):
    __tablename__ = "hr_document_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    doc_type = Column(String(32), nullable=False)  # APPOINTMENT | DECLARATION
    content = Column(Text, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
