from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class FinanceKYCCreate(BaseModel):
    aadhaar: Optional[str] = None
    pan: Optional[str] = None
    bank_account_no: Optional[str] = None
    ifsc: Optional[str] = None
    bank_name: str  # Required for Finance KYC submit
    branch: Optional[str] = None

    @field_validator("bank_name")
    @classmethod
    def bank_name_required_and_stripped(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Bank name is required")
        return v.strip()

class FinanceKYCResponse(FinanceKYCCreate):
    person_id: UUID  # FIXED: Use UUID type to match DB model
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )

