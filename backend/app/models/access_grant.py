"""Access Grant Models"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from app.core.database import Base

class GrantScopeType(str, enum.Enum):
    DOCUMENTS = "DOCUMENTS"  # Specific document IDs
    CATEGORY = "CATEGORY"    # All docs in a category

class AccessGrant(Base):
    __tablename__ = "access_grants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)  # Nullable as per requirements
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False, index=True)
    granted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_by_dept_id = Column(Integer, ForeignKey("departments.id"), nullable=False)  # HR/Finance
    granted_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    scope_type = Column(SQLEnum(GrantScopeType), nullable=False)
    scope_value = Column(String, nullable=False)  # documentId OR categoryKey like HR_SIGNED_DOCS, FINANCE_KYC_DOCS
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ticket = relationship("Ticket", back_populates="access_grants")
    person = relationship("Person")
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])
    granted_to = relationship("User", foreign_keys=[granted_to_user_id])
    granted_dept = relationship("Department", foreign_keys=[granted_by_dept_id])

