from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Union
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from app.models.rate_plan import PlanType, WorkingDayMode

class RatePlanCreate(BaseModel):
    plan_type: PlanType
    amount: Union[Decimal, float, str]  # Accept float/string from frontend
    valid_from: Union[date, str]  # Accept date string from frontend
    valid_to: Optional[Union[date, str]] = None
    working_day_mode: Optional[Union[WorkingDayMode, str]] = None
    project_id: Optional[Union[int, str]] = None
    
    @field_validator('amount', mode='before')
    @classmethod
    def convert_amount(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return Decimal(v)
        if isinstance(v, float):
            return Decimal(str(v))
        return v
    
    @field_validator('valid_from', mode='before')
    @classmethod
    def convert_valid_from(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v
    
    @field_validator('valid_to', mode='before')
    @classmethod
    def convert_valid_to(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v
    
    @field_validator('plan_type', mode='before')
    @classmethod
    def convert_plan_type(cls, v):
        if isinstance(v, str):
            # Map frontend values to backend enum
            v_upper = v.upper()
            if v_upper == 'MAN_DAY' or v_upper == 'MANDAY':
                return PlanType.MANDAY
            elif v_upper == 'MAN_MONTH' or v_upper == 'MANMONTH':
                return PlanType.MANMONTH
            elif v_upper == 'MONTHLY' or v_upper == 'MONTHLY_SALARY':
                return PlanType.MONTHLY_SALARY
        return v
    
    @field_validator('working_day_mode', mode='before')
    @classmethod
    def convert_working_day_mode(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            v_upper = v.upper()
            if v_upper == 'CALENDAR':
                return WorkingDayMode.CALENDAR
            elif v_upper == 'WORKING_26' or v_upper == 'WORKING26':
                return WorkingDayMode.WORKING_26
        return v
    
    @field_validator('project_id', mode='before')
    @classmethod
    def convert_project_id(cls, v):
        if v is None or v == '' or v == 0:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v
    
    model_config = ConfigDict(
        # Pydantic v2 handles date serialization automatically
        use_enum_values=True  # Serialize enums as their values
    )

class RatePlanResponse(RatePlanCreate):
    id: int
    person_id: UUID  # FIXED: Use UUID type to match DB model
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )

