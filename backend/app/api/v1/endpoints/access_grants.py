"""Access Grant API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.ticket import Ticket
from app.models.access_grant import AccessGrant
from app.models.document import Document, DocumentOwnerDept
from app.schemas.access_grant import AccessGrantCreate, AccessGrantResponse
from app.services.access_grant import create_access_grant, get_active_grants_for_user
from app.services.audit_logger import log_audit_event, get_client_ip, get_user_agent

router = APIRouter()

@router.post("/", response_model=AccessGrantResponse, status_code=status.HTTP_201_CREATED)
async def create_grant(
    grant_data: AccessGrantCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create access grant (only target dept users can grant)"""
    # Verify ticket exists and user has permission
    if grant_data.ticket_id:
        ticket = db.query(Ticket).filter(Ticket.id == grant_data.ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Only target dept users can grant access
        if ticket.to_dept_id != current_user.dept_id:
            raise HTTPException(status_code=403, detail="Only target department users can grant access")
    
    # Verify person exists
    from app.models.person import Person
    person = db.query(Person).filter(Person.id == grant_data.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Verify granted_to_user exists
    granted_to_user = db.query(User).filter(User.id == grant_data.granted_to_user_id).first()
    if not granted_to_user:
        raise HTTPException(status_code=404, detail="Granted to user not found")
    
    # Validate scope_value
    if not grant_data.scope_value:
        raise HTTPException(status_code=400, detail="scope_value is required")
    
    # Check max expiry (8 hours for normal users, unlimited for master admin)
    max_hours = 8
    # TODO: Check if user is master admin
    if grant_data.expires_in_hours > max_hours:
        raise HTTPException(status_code=400, detail=f"Maximum expiry is {max_hours} hours")
    
    # Create grant
    grant = create_access_grant(
        db=db,
        ticket_id=grant_data.ticket_id,
        person_id=grant_data.person_id,
        granted_by_user_id=current_user.id,
        granted_to_user_id=grant_data.granted_to_user_id,
        granted_by_dept_id=current_user.dept_id,
        scope_type=grant_data.scope_type,
        scope_value=grant_data.scope_value,
        expires_in_hours=grant_data.expires_in_hours
    )
    
    # Auto-update ticket status to RESOLVED if ticket exists
    if grant_data.ticket_id:
        ticket = db.query(Ticket).filter(Ticket.id == grant_data.ticket_id).first()
        if ticket and ticket.status.value in ["OPEN", "IN_PROGRESS", "WAITING"]:
            from app.models.ticket import TicketStatus
            ticket.status = TicketStatus.RESOLVED
            db.commit()
    
    # Load related data
    granted_by = db.query(User).filter(User.id == grant.granted_by_user_id).first()
    granted_to = db.query(User).filter(User.id == grant.granted_to_user_id).first()
    person = db.query(Person).filter(Person.id == grant.person_id).first()
    
    # Audit log
    log_audit_event(
        db=db,
        action_type="GRANT_CREATED",
        entity_type="AccessGrant",
        entity_id=str(grant.id),
        actor_user_id=current_user.id,
        action_metadata={
            "ticket_id": str(grant_data.ticket_id) if grant_data.ticket_id else None,
            "person_id": str(grant_data.person_id),
            "granted_to_user_id": grant_data.granted_to_user_id,
            "scope_type": grant_data.scope_type.value,
            "scope_value": grant_data.scope_value,
            "expires_in_hours": grant_data.expires_in_hours
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    response = AccessGrantResponse.model_validate(grant)
    response.granted_by_name = granted_by.full_name if granted_by else None
    response.granted_to_name = granted_to.full_name if granted_to else None
    response.person_name = person.name if person else None
    
    return response

@router.get("/active", response_model=List[AccessGrantResponse])
async def get_active_grants(
    person_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active grants for current user"""
    grants = get_active_grants_for_user(db, current_user.id, person_id)
    
    result = []
    for grant in grants:
        granted_by = db.query(User).filter(User.id == grant.granted_by_user_id).first()
        granted_to = db.query(User).filter(User.id == grant.granted_to_user_id).first()
        from app.models.person import Person
        person = db.query(Person).filter(Person.id == grant.person_id).first()
        
        response = AccessGrantResponse.model_validate(grant)
        response.granted_by_name = granted_by.full_name if granted_by else None
        response.granted_to_name = granted_to.full_name if granted_to else None
        response.person_name = person.name if person else None
        result.append(response)
    
    return result

@router.get("/my", response_model=List[AccessGrantResponse])
async def get_my_grants(
    person_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alias for /active"""
    return await get_active_grants(person_id, db, current_user)

@router.post("/{grant_id}/revoke", response_model=AccessGrantResponse)
async def revoke_grant(
    grant_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke an access grant"""
    grant = db.query(AccessGrant).filter(AccessGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")
    
    # Only the granting department or master admin can revoke
    if grant.granted_by_dept_id != current_user.dept_id:
        # TODO: Check if user is master admin
        raise HTTPException(status_code=403, detail="Not authorized to revoke this grant")
    
    if grant.revoked_at:
        raise HTTPException(status_code=400, detail="Grant already revoked")
    
    from datetime import datetime
    grant.revoked_at = datetime.utcnow()
    db.commit()
    db.refresh(grant)
    
    # Audit log
    log_audit_event(
        db=db,
        action_type="GRANT_REVOKED",
        entity_type="AccessGrant",
        entity_id=str(grant.id),
        actor_user_id=current_user.id,
        action_metadata={
            "grant_id": str(grant.id),
            "person_id": str(grant.person_id)
        },
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    granted_by = db.query(User).filter(User.id == grant.granted_by_user_id).first()
    granted_to = db.query(User).filter(User.id == grant.granted_to_user_id).first()
    from app.models.person import Person
    person = db.query(Person).filter(Person.id == grant.person_id).first()
    
    response = AccessGrantResponse.model_validate(grant)
    response.granted_by_name = granted_by.full_name if granted_by else None
    response.granted_to_name = granted_to.full_name if granted_to else None
    response.person_name = person.name if person else None
    
    return response

@router.post("/cleanup/expire", status_code=status.HTTP_200_OK)
async def expire_grants(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Expire grants that have passed their expiry time.
    This can be called manually or by a cron job.
    """
    from datetime import datetime
    
    now = datetime.utcnow()
    
    # Find expired grants that haven't been revoked
    expired_grants = db.query(AccessGrant).filter(
        AccessGrant.expires_at <= now,
        AccessGrant.revoked_at.is_(None)
    ).all()
    
    expired_count = 0
    for grant in expired_grants:
        grant.revoked_at = now
        expired_count += 1
        
        # Audit log for each expired grant
        log_audit_event(
            db=db,
            action_type="GRANT_EXPIRED",
            entity_type="AccessGrant",
            entity_id=str(grant.id),
            actor_user_id=None,  # System action
            action_metadata={
                "grant_id": str(grant.id),
                "person_id": str(grant.person_id),
                "expired_at": now.isoformat()
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
    
    db.commit()
    
    return {
        "message": f"Expired {expired_count} grant(s)",
        "expired_count": expired_count
    }
