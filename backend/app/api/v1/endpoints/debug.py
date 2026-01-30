"""
Temporary debug endpoint for document verification and email automation testing.
MARK FOR REMOVAL after verification is complete.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.person import Person
from app.models.document import Document, DocumentCategory
from app.services.document_access import is_master_admin
from app.core.storage import storage_service
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


@router.post("/email/run-birthday-job")
async def debug_run_birthday_job(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger the birthday email job (for local testing).
    Finds persons with DOB = today and creates EmailLog + AuditLog entries (DRY_RUN or sends).
    Master Admin only.
    """
    if not is_master_admin(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Master Admin required")
    from app.services.email_automation import run_birthday_job
    sent = run_birthday_job(db)
    return {"message": "Birthday job completed", "emails_processed": sent}

class DebugDocumentInfo(BaseModel):
    id: int
    doc_name: str
    doc_category: Optional[str]
    stage: str
    owner_dept: Optional[str]
    file_key: str
    file_exists_on_disk: bool
    file_size_bytes: Optional[int] = None

class DebugPersonDocumentsResponse(BaseModel):
    person_id: str
    person_name: str
    documents: List[DebugDocumentInfo]

@router.get("/person/{person_id}/documents", response_model=DebugPersonDocumentsResponse)
async def debug_person_documents(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    TEMPORARY DEBUG ENDPOINT - MARK FOR REMOVAL
    
    Returns ALL documents for a person with:
    - doc_type, category, file_path, exists_on_disk
    
    Master Admin only.
    """
    # Only Master Admin can access
    if not is_master_admin(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master Admin access required"
        )
    
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Get all documents
    all_documents = db.query(Document).filter(Document.person_id == person_id).all()
    
    debug_docs = []
    for doc in all_documents:
        # Check if file exists on disk
        file_exists = False
        file_size = None
        if storage_service.available:
            try:
                file_exists = storage_service.file_exists(doc.file_key)
                if file_exists:
                    # Try to get file size
                    try:
                        file_data = storage_service.get_file(doc.file_key)
                        file_size = len(file_data) if file_data else None
                    except:
                        pass
            except:
                pass
        
        debug_docs.append(DebugDocumentInfo(
            id=doc.id,
            doc_name=doc.doc_name,
            doc_category=doc.doc_category.value if doc.doc_category else None,
            stage=doc.stage.value if doc.stage else None,
            owner_dept=doc.owner_dept.value if doc.owner_dept else None,
            file_key=doc.file_key,
            file_exists_on_disk=file_exists,
            file_size_bytes=file_size or doc.size_bytes
        ))
    
    return DebugPersonDocumentsResponse(
        person_id=str(person.id),
        person_name=person.name,
        documents=debug_docs
    )

