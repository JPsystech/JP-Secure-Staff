from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.template import TemplateType, RevisionStatus

class TemplateRevisionBase(BaseModel):
    version: str
    content: str
    status: RevisionStatus = RevisionStatus.DRAFT

class TemplateRevisionCreate(TemplateRevisionBase):
    pass

class TemplateRevisionResponse(TemplateRevisionBase):
    id: int
    template_id: int
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TemplateBase(BaseModel):
    type: TemplateType
    name: Optional[str] = None

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None

class TemplateResponse(TemplateBase):
    id: int
    name: Optional[str] = None
    is_active: bool = False
    active_revision_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    revisions: List[TemplateRevisionResponse] = []
    
    class Config:
        from_attributes = True

