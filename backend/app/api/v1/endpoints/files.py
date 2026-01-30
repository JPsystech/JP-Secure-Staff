"""File serving endpoint for local storage files"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.core.storage import storage_service
import mimetypes
import os
from pathlib import Path

router = APIRouter()

@router.get("/{file_key:path}")
async def serve_file(
    file_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    Serve files from local storage.
    
    Prevents path traversal attacks.
    Uses storage_service.open_file() for streaming.
    """
    try:
        # Prevent path traversal: reject "..", "/", "\"
        if ".." in file_key or file_key.startswith("/") or file_key.startswith("\\"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )
        
        # Check if file exists
        if not storage_service.file_exists(file_key):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Open file for streaming
        if hasattr(storage_service, 'open_file'):
            # Local storage: use open_file for streaming
            file_stream = storage_service.open_file(file_key)
        else:
            # MinIO: read into memory and create BytesIO stream
            file_data = storage_service.get_file(file_key)
            file_stream = io.BytesIO(file_data)
        
        # Determine content type using mimetypes
        content_type, _ = mimetypes.guess_type(file_key)
        if not content_type:
            # Fallback content type map
            if "." in file_key:
                ext = file_key.split(".")[-1].lower()
                content_type_map = {
                    "pdf": "application/pdf",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "doc": "application/msword",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "xls": "application/vnd.ms-excel",
                    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                }
                content_type = content_type_map.get(ext, "application/octet-stream")
            else:
                content_type = "application/octet-stream"
        
        # Get filename from file_key (basename)
        filename = file_key.split("/")[-1] if "/" in file_key else file_key
        filename = filename.split("\\")[-1]  # Handle Windows paths
        
        # Return file as streaming response
        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve file: {str(e)}"
        )

