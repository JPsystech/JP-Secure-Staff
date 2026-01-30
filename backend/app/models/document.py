from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SQLEnum
import enum
from app.core.database import Base

class DocumentStage(str, enum.Enum):
    OPERATION = "OPERATION"
    FINANCE = "FINANCE"
    HR = "HR"

class DocumentOwnerDept(str, enum.Enum):
    OPERATIONS = "OPERATIONS"
    FINANCE = "FINANCE"
    HR = "HR"

class DocumentCategory(str, enum.Enum):
    STAGE_A = "STAGE_A"
    FINANCE_KYC = "FINANCE_KYC"
    HR_SIGNED = "HR_SIGNED"
    APPOINTMENT = "APPOINTMENT"
    DECLARATION = "DECLARATION"
    ID_CARD = "ID_CARD"
    OTHER = "OTHER"

class DocumentVisibilityScope(str, enum.Enum):
    """
    Document visibility scope enum.
    
    - PRIVATE: Only owner dept + master admin + active access grants
    - DEPARTMENT: Owner dept + master admin (no grants needed for owner dept)
    - GRANT_ONLY: Nobody except admin/owner; others only via grant
    - PUBLIC_AFTER_FINANCE: Visible to all when person.status in {SENT_TO_HR, ACTIVE, HR_COMPLETED}
    - PUBLIC_ALWAYS: Always visible to all internal departments (used for Stage-A)
    - STAGE_A: Special rule - everyone can view/download (alias for PUBLIC_ALWAYS for Stage-A docs)
    """
    PRIVATE = "PRIVATE"  # Only owner dept + master admin + active access grants
    DEPARTMENT = "DEPARTMENT"  # Owner dept + master admin (clearer than DEPT_ONLY)
    GRANT_ONLY = "GRANT_ONLY"  # Nobody except admin/owner; others only via grant
    PUBLIC_AFTER_FINANCE = "PUBLIC_AFTER_FINANCE"  # Visible to all when person.status in {SENT_TO_HR, ACTIVE, HR_COMPLETED}
    PUBLIC_ALWAYS = "PUBLIC_ALWAYS"  # Always visible to all internal departments (used for Stage-A)
    STAGE_A = "STAGE_A"  # Special rule: everyone can view/download (Stage-A documents)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    stage = Column(SQLEnum(DocumentStage), nullable=False)
    owner_dept = Column(SQLEnum(DocumentOwnerDept), nullable=True)  # Phase 3: Added
    doc_category = Column(SQLEnum(DocumentCategory), nullable=True)  # Phase 3: Added
    visibility_scope = Column(SQLEnum(DocumentVisibilityScope), nullable=True)  # Access model: Added
    doc_name = Column(String, nullable=False)
    file_key = Column(String, nullable=False)  # MinIO path
    mime_type = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    is_mandatory = Column(Boolean, default=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    person = relationship("Person", back_populates="documents")
    creator = relationship("User", foreign_keys=[created_by_user_id])

