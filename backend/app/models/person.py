from sqlalchemy import Column, String, Date, Enum as SQLEnum, ForeignKey, DateTime, Integer
from app.models.department import Department
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum
from app.core.database import Base

class PersonStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED_TO_FINANCE = "SUBMITTED_TO_FINANCE"
    FINANCE_IN_PROGRESS = "FINANCE_IN_PROGRESS"
    SENT_TO_HR = "SENT_TO_HR"
    ACTIVE = "ACTIVE"
    HR_COMPLETED = "HR_COMPLETED"

class Stream(str, Enum):
    MECH = "MECH"
    CIVIL = "CIVIL"
    ELEC = "ELEC"
    OTHER = "OTHER"

class Education(str, Enum):
    DIPLOMA = "DIPLOMA"
    DEGREE = "DEGREE"
    ME = "ME"
    OTHER = "OTHER"

class IntakeDept(str, Enum):
    OPERATION = "OPERATION"
    HR = "HR"


class Person(Base):
    __tablename__ = "persons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    mobile = Column(String, nullable=False)
    alt_mobile = Column(String, nullable=True)
    email = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    stream = Column(SQLEnum(Stream), nullable=True)
    stream_other = Column(String, nullable=True)
    education = Column(SQLEnum(Education), nullable=True)
    education_other = Column(String, nullable=True)
    location = Column(String, nullable=True)
    status = Column(SQLEnum(PersonStatus), default=PersonStatus.DRAFT, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)  # Access model: Added
    intake_dept = Column(SQLEnum(IntakeDept), nullable=True)  # Which department performed Stage-A intake
    finance_submitted_at = Column(DateTime(timezone=True), nullable=True)  # Access model: Added
    hr_submitted_at = Column(DateTime(timezone=True), nullable=True)  # Access model: Added
    activated_at = Column(DateTime(timezone=True), nullable=True)  # Access model: Added - when person becomes visible to all
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    creator = relationship("User", foreign_keys=[created_by_user_id])
    employments = relationship("Employment", back_populates="person", cascade="all, delete-orphan")
    finance_kyc = relationship("FinanceKYC", back_populates="person", uselist=False, cascade="all, delete-orphan")
    rate_plans = relationship("RatePlan", back_populates="person", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="person", cascade="all, delete-orphan")

