from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.role import Role, Permission, role_permission
from app.schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionResponse
)
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()

# Permission endpoints
@router.get("/permissions", response_model=List[PermissionResponse])
async def get_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all permissions"""
    permissions = db.query(Permission).all()
    return permissions

@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new permission"""
    existing = db.query(Permission).filter(Permission.code == permission.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission code already exists"
        )
    
    db_permission = Permission(**permission.dict())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

# Role endpoints
@router.get("/", response_model=List[RoleResponse])
async def get_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roles with optional filtering"""
    query = db.query(Role)
    
    if search:
        query = query.filter(
            (Role.name.ilike(f"%{search}%")) |
            (Role.code.ilike(f"%{search}%"))
        )
    
    # Default: show only active roles if is_active not specified
    if is_active is None:
        query = query.filter(Role.is_active == True)
    elif is_active is not None:
        query = query.filter(Role.is_active == is_active)
    
    roles = query.offset(skip).limit(limit).all()
    return roles

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific role by ID"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new role"""
    existing = db.query(Role).filter(Role.code == role.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role code already exists"
        )
    
    db_role = Role(
        name=role.name,
        code=role.code,
        description=role.description,
        is_active=role.is_active
    )
    db.add(db_role)
    db.flush()
    
    # Assign permissions
    if role.permission_ids:
        permissions = db.query(Permission).filter(Permission.id.in_(role.permission_ids)).all()
        db_role.permissions = permissions
    
    db.commit()
    db.refresh(db_role)
    return db_role

@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a role"""
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    update_data = role_update.dict(exclude_unset=True)
    permission_ids = update_data.pop("permission_ids", None)
    
    # Check if code is being updated and if it already exists
    if "code" in update_data:
        existing = db.query(Role).filter(
            Role.code == update_data["code"],
            Role.id != role_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role code already exists"
            )
    
    for field, value in update_data.items():
        setattr(db_role, field, value)
    
    # Update permissions if provided
    if permission_ids is not None:
        permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        db_role.permissions = permissions
    
    db.commit()
    db.refresh(db_role)
    return db_role

@router.post("/{role_id}/permissions", response_model=RoleResponse)
async def assign_permissions(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign permissions to a role"""
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    db_role.permissions = permissions
    db.commit()
    db.refresh(db_role)
    return db_role

