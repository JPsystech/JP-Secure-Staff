from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class TemplateType(str, enum.Enum):
    DECLARATION = "DECLARATION"
    APPOINTMENT_PERMANENT = "APPOINTMENT_PERMANENT"
    APPOINTMENT_FREELANCER = "APPOINTMENT_FREELANCER"
    APPOINTMENT_CONTRACTUAL = "APPOINTMENT_CONTRACTUAL"

class RevisionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    type = Column(SQLEnum(TemplateType), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    active_revision_id = Column(Integer, ForeignKey("template_revisions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    revisions = relationship("TemplateRevision", back_populates="template", foreign_keys="TemplateRevision.template_id")
    active_revision = relationship("TemplateRevision", foreign_keys=[active_revision_id])

class TemplateRevision(Base):
    __tablename__ = "template_revisions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    version = Column(String, nullable=False)
    content = Column(String, nullable=False)
    status = Column(SQLEnum(RevisionStatus), default=RevisionStatus.DRAFT)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    template = relationship("Template", back_populates="revisions", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by])

