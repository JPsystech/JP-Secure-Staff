from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SQLEnum
import enum
from app.core.database import Base

class EmploymentType(str, enum.Enum):
    PERMANENT = "PERMANENT"
    FREELANCER = "FREELANCER"
    CONTRACTUAL = "CONTRACTUAL"

class Employment(Base):
    __tablename__ = "employments"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    employment_type = Column(SQLEnum(EmploymentType), nullable=False)
    employee_code = Column(String, unique=True, nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("company_master.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    person = relationship("Person", back_populates="employments")
    company = relationship("CompanyMaster")

