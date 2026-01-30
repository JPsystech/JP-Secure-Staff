"""Access Grant Schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.access_grant import GrantScopeType

class AccessGrantCreate(BaseModel):
    ticket_id: Optional[UUID] = None
    person_id: UUID
    granted_to_user_id: int
    scope_type: GrantScopeType
    scope_value: str  # documentId (UUID string) OR categoryKey (e.g., "HR_SIGNED_DOCS", "FINANCE_KYC_DOCS")
    expires_in_hours: int = 8

class AccessGrantResponse(BaseModel):
    id: UUID
    ticket_id: Optional[UUID] = None
    person_id: UUID
    granted_by_user_id: int
    granted_by_dept_id: int
    granted_to_user_id: int
    scope_type: GrantScopeType
    scope_value: str
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    created_at: datetime
    
    # Related data
    granted_by_name: Optional[str] = None
    granted_to_name: Optional[str] = None
    person_name: Optional[str] = None
    
    class Config:
        from_attributes = True

