"""Document download endpoint - backward-compatible alias for cv-wallet download"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.api.v1.endpoints.cv_wallet import download_document

router = APIRouter()

@router.get("/{doc_id}/download")
async def download_document_alias(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Backward-compatible alias for document download.
    
    This endpoint redirects to the cv-wallet download endpoint
    to maintain compatibility with frontend code that may use
    /api/v1/documents/{id}/download instead of /api/v1/cv-wallet/documents/{id}/download
    """
    # Call the same download function from cv_wallet endpoint
    return await download_document(
        doc_id=doc_id,
        request=request,
        db=db,
        current_user=current_user
    )

