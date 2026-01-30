from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class FinanceKYC(Base):
    __tablename__ = "finance_kyc"
    
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), primary_key=True)
    aadhaar = Column(String, nullable=True)
    pan = Column(String, nullable=True)
    bank_account_no = Column(String, nullable=True)
    ifsc = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    person = relationship("Person", back_populates="finance_kyc")

