from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CompanyMasterBase(BaseModel):
    name: str
    short_code: str
    is_akshar: bool = False

class CompanyMasterCreate(CompanyMasterBase):
    pass

class CompanyMasterUpdate(BaseModel):
    name: Optional[str] = None
    short_code: Optional[str] = None
    is_akshar: Optional[bool] = None

class CompanyMasterResponse(CompanyMasterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DocumentNameMasterBase(BaseModel):
    name: str
    is_active: bool = True

class DocumentNameMasterCreate(DocumentNameMasterBase):
    pass

class DocumentNameMasterUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class DocumentNameMasterResponse(DocumentNameMasterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LocationMasterBase(BaseModel):
    name: str
    is_active: bool = True

class LocationMasterCreate(LocationMasterBase):
    pass

class LocationMasterUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class LocationMasterResponse(LocationMasterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProjectMasterBase(BaseModel):
    name: str
    client: Optional[str] = None
    location: Optional[str] = None
    is_active: bool = True

class ProjectMasterCreate(ProjectMasterBase):
    pass

class ProjectMasterUpdate(BaseModel):
    name: Optional[str] = None
    client: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class ProjectMasterResponse(ProjectMasterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

