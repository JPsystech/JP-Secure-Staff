"""Audit Log Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class AuditLogResponse(BaseModel):
    id: UUID
    actor_user_id: Optional[int] = None
    action_type: str
    entity_type: str
    entity_id: Optional[str] = None
    action_metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    # Related data
    actor_name: Optional[str] = None
    actor_email: Optional[str] = None
    actor_dept_id: Optional[int] = None
    actor_dept_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    page: int
    page_size: int
    total: int

class AuditLogFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    action_type: Optional[str] = None
    entity_type: Optional[str] = None
    actor_user_id: Optional[int] = None
    dept_id: Optional[int] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    sort: str = Field(default="-created_at")  # "-created_at" for desc, "created_at" for asc

