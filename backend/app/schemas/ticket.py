"""Ticket Schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.ticket import TicketCategory, TicketPriority, TicketStatus

class TicketBase(BaseModel):
    to_dept_id: int
    person_id: Optional[UUID] = None
    category: TicketCategory
    priority: TicketPriority = TicketPriority.NORMAL
    subject: str
    description: str

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    assigned_to_user_id: Optional[int] = None
    priority: Optional[TicketPriority] = None

class TicketCommentCreate(BaseModel):
    message: str

class TicketCommentResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    author_user_id: int
    message: str
    created_at: datetime
    author_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class TicketAttachmentResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    file_name: str
    mime_type: str
    size_bytes: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TicketResponse(BaseModel):
    id: UUID
    ticket_no: str
    from_dept_id: int
    to_dept_id: int
    created_by_user_id: int
    assigned_to_user_id: Optional[int] = None
    person_id: Optional[UUID] = None
    category: TicketCategory
    priority: TicketPriority
    subject: str
    description: str
    status: TicketStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Related data
    from_dept_name: Optional[str] = None
    to_dept_name: Optional[str] = None
    creator_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    person_name: Optional[str] = None
    comments: List[TicketCommentResponse] = []
    attachments: List[TicketAttachmentResponse] = []
    
    class Config:
        from_attributes = True

class TicketSummaryResponse(BaseModel):
    id: UUID
    ticket_no: str
    from_dept_id: int
    to_dept_id: int
    created_by_user_id: int
    assigned_to_user_id: Optional[int] = None
    person_id: Optional[UUID] = None
    category: TicketCategory
    priority: TicketPriority
    subject: str
    status: TicketStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    from_dept_name: Optional[str] = None
    to_dept_name: Optional[str] = None
    creator_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    person_name: Optional[str] = None
    
    class Config:
        from_attributes = True

