from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

class PolicyBase(BaseModel):
    key: str
    value_json: dict

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    value_json: Optional[dict] = None

class PolicyResponse(PolicyBase):
    id: int
    updated_by: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

