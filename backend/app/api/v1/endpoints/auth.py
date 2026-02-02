import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, status, Request, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, decode_access_token
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import LoginRequest, Token
from datetime import timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)  # FIXED: Don't auto-raise on missing token

def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    FIXED: Safely extract and validate JWT token.
    Handles missing token, invalid JWT, and database errors gracefully.
    """
    try:
        # Try to get token from Authorization header
        token = None
        if authorization:
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != "bearer":
                token = None
        
        # If no token in header, try to get from cookie
        if not token and request:
            token = request.cookies.get("access_token") or request.cookies.get("token")
        
        if not token:
            logger.debug("No token provided in request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Decode token safely
        try:
            payload = decode_access_token(token)
        except Exception as e:
            logger.warning(f"Token decode error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if payload is None:
            logger.warning("Token decode returned None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token payload missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Query user from database safely (case-insensitive email)
        try:
            user = db.query(User).filter(func.lower(User.email) == (email or "").strip().lower()).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching user: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service temporarily unavailable"
            )
        
        if user is None:
            logger.warning(f"User not found for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

@router.post("/login", response_model=Token)
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    from app.services.login_rate_limiter import is_rate_limited, get_client_ip
    client_ip = get_client_ip(request)
    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in a few minutes.",
        )
    email_clean = (login_data.email or "").strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Get user role
    role = None
    if user.role_id:
        role = db.query(Role).filter(Role.id == user.role_id).first()
    
    # Get user department
    from app.models.department import Department
    department = None
    if user.dept_id:
        department = db.query(Department).filter(Department.id == user.dept_id).first()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": role.code if role else None},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": role.code if role else None,
            "role_name": role.name if role else None,
            "dept_id": user.dept_id,
            "department": {
                "id": department.id if department else None,
                "name": department.name if department else None,
                "code": department.code if department else None,
            } if department else None,
            "is_active": user.is_active,
        }
    }

@router.get("/me")
async def get_current_user_info(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    FIXED: Get current user info with robust error handling.
    Returns 401 if not authenticated, never crashes.
    """
    try:
        # Get current user - this will raise 401 if not authenticated
        current_user = get_current_user(request, authorization, db)
        
        # Safely query role and department
        role = None
        try:
            if current_user.role_id:
                role = db.query(Role).filter(Role.id == current_user.role_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching role: {str(e)}")
            # Continue without role - don't fail the request
        
        department = None
        try:
            if current_user.dept_id:
                from app.models.department import Department
                department = db.query(Department).filter(Department.id == current_user.dept_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching department: {str(e)}")
            # Continue without department - don't fail the request
        except Exception as e:
            logger.error(f"Unexpected error while fetching department: {str(e)}")
            # Continue without department

        # Permission codes for frontend (e.g. permission-gated menu items)
        permission_codes = []
        try:
            from app.services.permission_checker import get_user_permission_codes
            permission_codes = list(get_user_permission_codes(db, current_user))
        except Exception as e:
            logger.debug("Could not resolve permission codes for /me: %s", e)
        
        return {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": role.code if role else None,
            "role_name": role.name if role else None,
            "dept_id": current_user.dept_id,
            "department": {
                "id": department.id if department else None,
                "name": department.name if department else None,
                "code": department.code if department else None,
            } if department else None,
            "is_active": current_user.is_active,
            "permission_codes": permission_codes,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /me endpoint: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

