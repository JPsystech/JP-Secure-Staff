from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.document import DocumentStage, DocumentOwnerDept, DocumentCategory, DocumentVisibilityScope

class DocumentCreate(BaseModel):
    stage: DocumentStage
    doc_name: str
    mime_type: str
    size_bytes: int
    is_mandatory: bool = False

class DocumentResponse(BaseModel):
    id: int
    person_id: UUID  # FIXED: Use UUID type to match DB model
    stage: DocumentStage
    owner_dept: Optional[DocumentOwnerDept] = None
    doc_category: Optional[DocumentCategory] = None
    visibility_scope: Optional[DocumentVisibilityScope] = None  # Access Model: Added
    doc_name: str
    file_key: str
    mime_type: str
    size_bytes: int
    is_mandatory: bool
    created_by_user_id: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True  # Serialize enums as their values (strings)
    )

class StageADocumentResponse(BaseModel):
    """Response model for Stage-A documents in CV Wallet"""
    id: int
    filename: str  # doc_name (renamed to match spec)
    file_name: str  # Keep for backward compatibility
    doc_type: Optional[str] = None  # doc_type_name (renamed for consistency)
    doc_type_name: Optional[str] = None  # From DocumentNameMaster if linked (deprecated, use doc_type)
    doc_category: Optional[str] = None  # STAGE_A, FINANCE_KYC, etc.
    doc_name: Optional[str] = None  # Optional display name
    issue_date: Optional[datetime] = None  # Not in current model, can be None
    expiry_date: Optional[datetime] = None  # Not in current model, can be None
    uploaded_at: datetime  # created_at
    download_url: str  # URL to download the file
    file_key: Optional[str] = None  # Storage key for reference
    can_download: bool  # Computed based on permission and policy
    download_block_reason: Optional[str] = None  # Reason if download is blocked (deprecated, use reason)
    # Step-7: Enhanced access information
    reason: Optional[str] = None  # AccessReason enum value: STAGE_A_PUBLIC, OWNER_DEPT, ADMIN, GRANTED, NEEDS_GRANT, EXPIRED, FORBIDDEN
    grant_expires_at: Optional[str] = None  # ISO datetime string if access via grant
    visibility_label: Optional[str] = None  # UI label: "Available", "Locked", "Expires in Xh Ym", etc.
    owner_dept: Optional[str] = None  # Document owner department: OPERATIONS, FINANCE, HR
    
    model_config = ConfigDict(
        from_attributes=True
    )

class StageADocumentsListResponse(BaseModel):
    """Response wrapper for Stage-A documents list"""
    items: List[StageADocumentResponse]
    
    model_config = ConfigDict(
        from_attributes=True
    )
