"""
Admin Document Download (Step-14): stream any document by ID; bypass department checks.
Requires ADMIN_DOCUMENT_DOWNLOAD_ALL. Audit: ADMIN_DOC_DOWNLOADED.
"""
import io
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.dependencies.permissions import require_permission
from app.models.user import User
from app.models.document import Document
from app.models.person import Person
from app.core.permissions import PermissionCode
from app.core.storage import storage_service
from app.services.audit_logger import log_audit_event, get_client_ip, get_user_agent

router = APIRouter()


@router.get("/{document_id}/download")
async def admin_download_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.ADMIN_DOCUMENT_DOWNLOAD_ALL)),
):
    """
    Stream document file. Bypasses department access checks.
    Document must exist and belong to a person. Audit: ADMIN_DOC_DOWNLOADED.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    person = db.query(Person).filter(Person.id == document.person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    if not storage_service.file_exists(document.file_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {document.file_key}"
        )

    try:
        file_data = storage_service.get_file(document.file_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )

    log_audit_event(
        db=db,
        action_type="ADMIN_DOC_DOWNLOADED",
        entity_type="Document",
        entity_id=str(document.id),
        actor_user_id=current_user.id,
        action_metadata={
            "person_id": str(person.id),
            "filename": document.doc_name,
            "file_key": document.file_key,
        },
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
    )

    content_disposition = "inline" if document.mime_type == "application/pdf" else "attachment"
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'{content_disposition}; filename="{document.doc_name}"'
        },
    )
