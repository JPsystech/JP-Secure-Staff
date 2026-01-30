from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SQLEnum
import enum
from app.core.database import Base

class PlanType(str, enum.Enum):
    MANDAY = "MANDAY"
    MANMONTH = "MANMONTH"
    MONTHLY_SALARY = "MONTHLY_SALARY"

class WorkingDayMode(str, enum.Enum):
    CALENDAR = "CALENDAR"
    WORKING_26 = "WORKING_26"

class RatePlan(Base):
    __tablename__ = "rate_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    working_day_mode = Column(SQLEnum(WorkingDayMode), nullable=True)
    project_id = Column(Integer, ForeignKey("project_master.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    person = relationship("Person", back_populates="rate_plans")
    project = relationship("ProjectMaster")

