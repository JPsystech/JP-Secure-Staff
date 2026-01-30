"""
Permission dependency for FastAPI endpoints

Usage:
    @router.get("/some-endpoint")
    async def some_endpoint(
        current_user: User = Depends(get_current_user),
        _: None = Depends(require_permission(PermissionCode.DOC_STAGEA_DOWNLOAD))
    ):
        # User has permission, proceed
        ...
"""
from typing import List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.core.permissions import PermissionCode
from app.services.permission_checker import is_master_admin, get_user_permission_codes


def require_permission(*codes: PermissionCode):
    """
    Dependency factory that requires user to have ALL specified permissions.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_permission(PermissionCode.DOC_STAGEA_DOWNLOAD))
        ):
            ...
    
    Args:
        *codes: One or more PermissionCode enum values that are ALL required
    
    Returns:
        FastAPI dependency function
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> None:
        # Master Admin bypass
        if is_master_admin(current_user, db):
            return None
        
        # Get user's permissions
        user_permissions = get_user_permission_codes(db, current_user)
        
        # Check if user has ALL required permissions
        required_codes = {code.value for code in codes}
        missing = required_codes - user_permissions
        
        if missing:
            missing_list = sorted(list(missing))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_list)}"
            )
        
        return None
    
    return permission_checker
