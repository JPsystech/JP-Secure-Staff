"""
Admin endpoints for permission and role management + email logs
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import date, datetime, timezone
from pydantic import BaseModel
from uuid import UUID

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.dependencies.permissions import require_permission
from app.models.user import User
from app.models.role import Role, Permission
from app.models.email_log import EmailLog
from app.core.permissions import PermissionCode, get_all_permission_codes, get_permission_metadata
from app.services.permission_checker import is_master_admin, user_has_permission
from app.services.audit_logger import log_audit_event
from app.schemas.role import PermissionResponse

router = APIRouter()


class PermissionListResponse(BaseModel):
    """Response for permission list"""
    code: str
    label: str
    description: str
    module: str
    action: str


class RolePermissionsResponse(BaseModel):
    """Response for role permissions"""
    role_id: int
    role_name: str
    role_code: str
    permission_codes: List[str]


class UpdateRolePermissionsRequest(BaseModel):
    """Request to update role permissions"""
    codes: List[str]


class EmailLogResponse(BaseModel):
    id: UUID
    to_email: str
    subject: str
    template_key: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    metadata_: Optional[dict] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class EmailLogListResponse(BaseModel):
    items: List[EmailLogResponse]
    total: int
    page: int
    page_size: int


@router.get("/permissions", response_model=List[PermissionListResponse], operation_id="get_all_permissions")
async def get_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all permissions (read-only).
    Only code defines permissions - UI cannot create/delete.
    """
    # All authenticated users can view permissions list
    permissions = db.query(Permission).order_by(Permission.code).all()
    
    result = []
    for perm in permissions:
        result.append(PermissionListResponse(
            code=perm.code,
            label=perm.label or perm.code,
            description=perm.description or "",
            module=perm.module,
            action=perm.action
        ))
    
    return result


@router.get("/roles/{role_id}/permissions", response_model=RolePermissionsResponse, operation_id="get_role_permissions")
async def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get assigned permission codes for a role.
    Returns list of permission codes (strings).
    """
    # Check access: MASTER_ADMIN or user with ROLE_MANAGE permission
    if not is_master_admin(current_user, db):
        if not user_has_permission(db, current_user, PermissionCode.ROLE_MANAGE.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing required permission: ROLE_MANAGE"
            )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    permission_codes = [perm.code for perm in role.permissions]
    
    return RolePermissionsResponse(
        role_id=role.id,
        role_name=role.name,
        role_code=role.code,
        permission_codes=permission_codes
    )


@router.put("/roles/{role_id}/permissions", response_model=RolePermissionsResponse, operation_id="update_role_permissions")
async def update_role_permissions(
    role_id: int,
    request: UpdateRolePermissionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update assigned permissions for a role.
    Replaces all existing permissions with the provided codes.
    
    Only MASTER_ADMIN or users with ROLE_MANAGE permission can update.
    Creates audit log entry for the change.
    """
    # Check access: MASTER_ADMIN or user with ROLE_MANAGE permission
    if not is_master_admin(current_user, db):
        if not user_has_permission(db, current_user, PermissionCode.ROLE_MANAGE.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing required permission: ROLE_MANAGE"
            )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Get old permissions for audit log
    old_permission_codes = {perm.code for perm in role.permissions}
    
    # Validate permission codes exist
    if request.codes:
        permissions = db.query(Permission).filter(Permission.code.in_(request.codes)).all()
        found_codes = {perm.code for perm in permissions}
        missing_codes = set(request.codes) - found_codes
        
        if missing_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission codes: {', '.join(sorted(missing_codes))}"
            )
        
        # Update role permissions
        role.permissions = permissions
    else:
        # Empty list means remove all permissions
        role.permissions = []
    
    db.commit()
    db.refresh(role)
    
    # Get new permissions
    new_permission_codes = {perm.code for perm in role.permissions}
    
    # Calculate added and removed
    added = sorted(list(new_permission_codes - old_permission_codes))
    removed = sorted(list(old_permission_codes - new_permission_codes))
    
    # Create audit log
    log_audit_event(
        db=db,
        action_type="ROLE_PERMISSION_UPDATE",
        entity_type="Role",
        entity_id=str(role.id),
        actor_user_id=current_user.id,
        action_metadata={
            "role_id": role.id,
            "role_name": role.name,
            "role_code": role.code,
            "added_permissions": added,
            "removed_permissions": removed,
            "total_permissions": len(new_permission_codes)
        },
        ip_address=None,
        user_agent=None
    )
    
    return RolePermissionsResponse(
        role_id=role.id,
        role_name=role.name,
        role_code=role.code,
        permission_codes=list(new_permission_codes)
    )


@router.get("/email-logs", response_model=EmailLogListResponse)
async def get_email_logs(
    from_date: Optional[date] = Query(None, alias="from", description="From date YYYY-MM-DD"),
    to_date: Optional[date] = Query(None, alias="to", description="To date YYYY-MM-DD"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    template_key: Optional[str] = Query(None, description="Filter by template_key"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.ADMIN_EMAIL_LOG_VIEW)),
):
    """
    Get email logs with filters and pagination. Requires ADMIN_EMAIL_LOG_VIEW.
    """
    query = db.query(EmailLog)
    if from_date:
        query = query.filter(EmailLog.created_at >= datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc))
    if to_date:
        end_of_day = datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)
        query = query.filter(EmailLog.created_at <= end_of_day)
    if status_filter:
        query = query.filter(EmailLog.status == status_filter)
    if template_key:
        query = query.filter(EmailLog.template_key == template_key)
    total = query.count()
    query = query.order_by(desc(EmailLog.created_at))
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()
    items = [
        EmailLogResponse(
            id=log.id,
            to_email=log.to_email,
            subject=log.subject,
            template_key=log.template_key,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            status=log.status,
            error_message=log.error_message,
            sent_at=log.sent_at,
            created_at=log.created_at,
            metadata_=log.metadata_,
        )
        for log in logs
    ]
    return EmailLogListResponse(items=items, total=total, page=page, page_size=page_size)
