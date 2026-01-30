from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyResponse
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[PolicyResponse])
async def get_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all policies"""
    policies = db.query(Policy).all()
    return policies

@router.get("/{policy_key}", response_model=PolicyResponse)
async def get_policy(
    policy_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific policy by key"""
    policy = db.query(Policy).filter(Policy.key == policy_key).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    return policy

@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new policy"""
    existing = db.query(Policy).filter(Policy.key == policy.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy key already exists"
        )
    
    db_policy = Policy(
        key=policy.key,
        value_json=policy.value_json,
        updated_by=current_user.id
    )
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy

@router.patch("/{policy_key}", response_model=PolicyResponse)
async def update_policy(
    policy_key: str,
    policy_update: PolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a policy"""
    db_policy = db.query(Policy).filter(Policy.key == policy_key).first()
    if not db_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    if policy_update.value_json is not None:
        db_policy.value_json = policy_update.value_json
        db_policy.updated_by = current_user.id
    
    db.commit()
    db.refresh(db_policy)
    return db_policy

