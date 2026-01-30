"""
Admin access helpers for Step-14: Admin Person Viewer + Global Document Download.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.permissions import PermissionCode
from app.services.permission_checker import user_has_permission


def require_admin_permission(db: Session, user: User, perm_code: PermissionCode) -> None:
    """
    Raise 403 if user does not have the given admin permission.
    Use before performing admin-only operations.
    """
    if not user_has_permission(db, user, perm_code.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {perm_code.value}"
        )


def is_admin_document_override(db: Session, user: User) -> bool:
    """True if user can download any document via admin (bypass department checks)."""
    return user_has_permission(db, user, PermissionCode.ADMIN_DOCUMENT_DOWNLOAD_ALL.value)
