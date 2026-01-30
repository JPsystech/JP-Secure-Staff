"""Audit Log Model"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system actions
    action_type = Column(String, nullable=False, index=True)  # LOGIN_SUCCESS, TICKET_CREATED, etc.
    entity_type = Column(String, nullable=False, index=True)  # Ticket, Person, Document, etc.
    entity_id = Column(String, nullable=True, index=True)  # UUID or string ID
    action_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved word)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    actor = relationship("User", foreign_keys=[actor_user_id])

