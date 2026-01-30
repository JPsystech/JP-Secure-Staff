from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.department import Department
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    dept_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users with optional filtering"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if dept_id is not None:
        query = query.filter(User.dept_id == dept_id)
    
    users = query.offset(skip).limit(limit).all()
    
    # Enrich with role_name and department_name
    result = []
    for user in users:
        role_name = None
        department_name = None
        if user.role_id:
            role = db.query(Role).filter(Role.id == user.role_id).first()
            role_name = role.name if role else None
        if user.dept_id:
            dept = db.query(Department).filter(Department.id == user.dept_id).first()
            department_name = dept.name if dept else None
        
        user_dict = UserResponse.model_validate(user).model_dump()
        user_dict['role_name'] = role_name
        user_dict['department_name'] = department_name
        result.append(UserResponse(**user_dict))
    
    return result

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Enrich with role_name and department_name
    role_name = None
    department_name = None
    if user.role_id:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        role_name = role.name if role else None
    if user.dept_id:
        dept = db.query(Department).filter(Department.id == user.dept_id).first()
        department_name = dept.name if dept else None
    
    user_dict = UserResponse.model_validate(user).model_dump()
    user_dict['role_name'] = role_name
    user_dict['department_name'] = department_name
    return UserResponse(**user_dict)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user"""
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Verify department exists
    if user.dept_id:
        dept = db.query(Department).filter(Department.id == user.dept_id).first()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
    
    # Verify role exists
    if user.role_id:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role not found"
            )
    
    db_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=get_password_hash(user.password),
        dept_id=user.dept_id,
        role_id=user.role_id,
        is_active=user.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Enrich with role_name and department_name
    role_name = None
    department_name = None
    if db_user.role_id:
        role = db.query(Role).filter(Role.id == db_user.role_id).first()
        role_name = role.name if role else None
    if db_user.dept_id:
        dept = db.query(Department).filter(Department.id == db_user.dept_id).first()
        department_name = dept.name if dept else None
    
    user_dict = UserResponse.model_validate(db_user).model_dump()
    user_dict['role_name'] = role_name
    user_dict['department_name'] = department_name
    return UserResponse(**user_dict)

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Check if email is being updated and if it already exists
    if "email" in update_data:
        existing = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Verify department exists
    if "dept_id" in update_data and update_data["dept_id"]:
        dept = db.query(Department).filter(Department.id == update_data["dept_id"]).first()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
    
    # Verify role exists
    if "role_id" in update_data and update_data["role_id"]:
        role = db.query(Role).filter(Role.id == update_data["role_id"]).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role not found"
            )
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    # Enrich with role_name and department_name
    role_name = None
    department_name = None
    if db_user.role_id:
        role = db.query(Role).filter(Role.id == db_user.role_id).first()
        role_name = role.name if role else None
    if db_user.dept_id:
        dept = db.query(Department).filter(Department.id == db_user.dept_id).first()
        department_name = dept.name if dept else None
    
    user_dict = UserResponse.model_validate(db_user).model_dump()
    user_dict['role_name'] = role_name
    user_dict['department_name'] = department_name
    return UserResponse(**user_dict)

@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle user active status"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_user.is_active = not db_user.is_active
    db.commit()
    db.refresh(db_user)
    
    # Enrich with role_name and department_name
    role_name = None
    department_name = None
    if db_user.role_id:
        role = db.query(Role).filter(Role.id == db_user.role_id).first()
        role_name = role.name if role else None
    if db_user.dept_id:
        dept = db.query(Department).filter(Department.id == db_user.dept_id).first()
        department_name = dept.name if dept else None
    
    user_dict = UserResponse.model_validate(db_user).model_dump()
    user_dict['role_name'] = role_name
    user_dict['department_name'] = department_name
    return UserResponse(**user_dict)

@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: int,
    password_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset user password (stub - in production, send email)"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_password = password_data.get("new_password")
    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_password is required"
        )
    
    db_user.password_hash = get_password_hash(new_password)
    db.commit()
    return {"message": "Password reset successfully"}

