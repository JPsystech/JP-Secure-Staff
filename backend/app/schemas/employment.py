from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.employment import EmploymentType

class EmploymentCreate(BaseModel):
    employment_type: EmploymentType
    company_id: int

class EmploymentResponse(BaseModel):
    id: int
    person_id: UUID
    employment_type: EmploymentType
    employee_code: Optional[str] = None
    company_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

