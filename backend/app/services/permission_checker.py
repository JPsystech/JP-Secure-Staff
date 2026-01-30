"""
Permission checking utilities
"""
from typing import Set
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Permission, Role
from app.core.permissions import PermissionCode


def is_master_admin(user: User, db: Session) -> bool:
    """Check if user is Master Admin"""
    if not user.role_id:
        return False
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return role and role.code == "MASTER_ADMIN"


def get_user_permission_codes(db: Session, user: User) -> Set[str]:
    """
    Get all permission codes for a user.
    
    Args:
        db: Database session
        user: User object
    
    Returns:
        Set of permission code strings (e.g., {"DOC_STAGEA_VIEW", "DOC_STAGEA_DOWNLOAD", ...})
    """
    if not user.role_id:
        return set()
    
    # Get user's role
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        return set()
    
    # Get all permission codes for this role
    permission_codes = {perm.code for perm in role.permissions}
    return permission_codes


def user_has_permission(db: Session, user: User, permission_code: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        db: Database session
        user: User object
        permission_code: Permission code (e.g., "DOC_STAGEA_VIEW", "DOC_STAGEA_DOWNLOAD")
    
    Returns:
        True if user has the permission, False otherwise
    """
    # Master Admin bypass
    if is_master_admin(user, db):
        return True
    
    if not user.role_id:
        return False
    
    # Get user's role
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        return False
    
    # Check if role has the permission
    permission = db.query(Permission).filter(Permission.code == permission_code).first()
    if not permission:
        return False
    
    # Check if role has this permission
    return permission in role.permissions

