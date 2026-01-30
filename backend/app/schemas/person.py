import re
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from app.models.person import PersonStatus, Stream, Education, IntakeDept

# Validation pattern for India-style 10-digit mobile
MOBILE_10_DIGITS = re.compile(r"^[0-9]{10}$")


class PersonBase(BaseModel):
    name: str
    mobile: str
    alt_mobile: Optional[str] = None
    email: Optional[EmailStr] = None  # Optional for response (DB may have null)
    dob: Optional[date] = None
    stream: Optional[Stream] = None
    stream_other: Optional[str] = None
    education: Optional[Education] = None
    education_other: Optional[str] = None
    location: Optional[str] = None


class PersonCreate(PersonBase):
    """Stage-A create: name, mobile, email required; mobile 10 digits, email valid format."""
    email: EmailStr  # Required for create

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name is required")
        return v.strip()

    @field_validator("mobile")
    @classmethod
    def mobile_exactly_10_digits(cls, v: str) -> str:
        if not v:
            raise ValueError("Mobile number is required")
        cleaned = re.sub(r"\s", "", v)
        if not MOBILE_10_DIGITS.match(cleaned):
            raise ValueError("Mobile must be exactly 10 digits (digits only)")
        return cleaned

    @field_validator("email")
    @classmethod
    def email_required_and_stripped(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Email is required")
        return v.strip()

class PersonResponse(PersonBase):
    id: UUID
    status: PersonStatus
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    intake_dept: Optional[IntakeDept] = None
    
    class Config:
        from_attributes = True

class PersonSummaryResponse(PersonResponse):
    employee_code: Optional[str] = None
    company_name: Optional[str] = None
    employment_type: Optional[str] = None  # PERMANENT, FREELANCER, CONTRACTUAL
    rate_value: Optional[float] = None
    rate_label: Optional[str] = None
    rate_display: Optional[str] = None

class DuplicateResponse(BaseModel):
    existing_person_id: str
    existing_employee_code: Optional[str] = None

