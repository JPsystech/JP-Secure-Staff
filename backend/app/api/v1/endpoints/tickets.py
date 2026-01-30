"""Ticket API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.ticket import Ticket, TicketComment, TicketAttachment, TicketStatus
from app.models.department import Department
from app.models.person import Person
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketResponse, TicketSummaryResponse,
    TicketCommentCreate, TicketCommentResponse, TicketAttachmentResponse
)
from app.services.ticket_number import generate_ticket_number
from app.services.ticket_assignment import assign_ticket_to_user
from app.services.audit_logger import log_audit_event, get_client_ip, get_user_agent
from app.core.storage import storage_service
import uuid

router = APIRouter()

def can_view_ticket(ticket: Ticket, user: User) -> bool:
    """Check if user can view ticket"""
    return (
        ticket.created_by_user_id == user.id or
        ticket.to_dept_id == user.dept_id or
        ticket.assigned_to_user_id == user.id
    )

def can_modify_ticket(ticket: Ticket, user: User) -> bool:
    """Check if user can modify ticket"""
    return (
        ticket.to_dept_id == user.dept_id or
        ticket.assigned_to_user_id == user.id
    )

@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ticket"""
    try:
        # Validate user has a department
        if not current_user.dept_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be assigned to a department to create tickets"
            )
        
        # Validate to_dept_id exists
        to_dept = db.query(Department).filter(Department.id == ticket_data.to_dept_id).first()
        if not to_dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target department with ID {ticket_data.to_dept_id} not found"
            )
        
        # Generate ticket number
        ticket_no = generate_ticket_number(db)
        
        # Create ticket
        ticket = Ticket(
            ticket_no=ticket_no,
            from_dept_id=current_user.dept_id,
            to_dept_id=ticket_data.to_dept_id,
            created_by_user_id=current_user.id,
            person_id=ticket_data.person_id,
            category=ticket_data.category,
            priority=ticket_data.priority,
            subject=ticket_data.subject,
            description=ticket_data.description
        )
        
        db.add(ticket)
        db.flush()
        
        # Auto-assign if possible
        assigned_user = assign_ticket_to_user(db, ticket)
        if assigned_user:
            ticket.assigned_to_user_id = assigned_user.id
        
        db.commit()
        db.refresh(ticket)
        
        # Load related data
        from_dept = db.query(Department).filter(Department.id == ticket.from_dept_id).first()
        creator = db.query(User).filter(User.id == ticket.created_by_user_id).first()
        person = db.query(Person).filter(Person.id == ticket.person_id).first() if ticket.person_id else None
        
        # Audit log
        log_audit_event(
            db=db,
            action_type="TICKET_CREATED",
            entity_type="Ticket",
            entity_id=str(ticket.id),
            actor_user_id=current_user.id,
            action_metadata={
                "ticket_no": ticket_no,
                "to_dept_id": ticket_data.to_dept_id,
                "category": ticket_data.category.value,
                "priority": ticket_data.priority.value
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        response = TicketResponse.model_validate(ticket)
        response.from_dept_name = from_dept.name if from_dept else None
        response.to_dept_name = to_dept.name if to_dept else None
        response.creator_name = creator.full_name if creator else None
        response.person_name = person.name if person else None
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Error creating ticket: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ticket: {str(e)}"
        )

@router.get("/", response_model=List[TicketSummaryResponse])
async def get_tickets(
    scope: str = "my",  # "my" or "inbox"
    status_filter: Optional[TicketStatus] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    dept_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tickets - my tickets or department inbox"""
    query = db.query(Ticket)
    
    if scope == "my":
        query = query.filter(Ticket.created_by_user_id == current_user.id)
    elif scope == "inbox":
        query = query.filter(
            (Ticket.to_dept_id == current_user.dept_id) |
            (Ticket.assigned_to_user_id == current_user.id)
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid scope. Use 'my' or 'inbox'")
    
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if dept_id:
        query = query.filter(Ticket.from_dept_id == dept_id)
    
    tickets = query.order_by(Ticket.updated_at.desc()).all()
    
    result = []
    for ticket in tickets:
        from_dept = db.query(Department).filter(Department.id == ticket.from_dept_id).first()
        to_dept = db.query(Department).filter(Department.id == ticket.to_dept_id).first()
        creator = db.query(User).filter(User.id == ticket.created_by_user_id).first()
        assigned = db.query(User).filter(User.id == ticket.assigned_to_user_id).first() if ticket.assigned_to_user_id else None
        person = db.query(Person).filter(Person.id == ticket.person_id).first() if ticket.person_id else None
        
        response = TicketSummaryResponse.model_validate(ticket)
        response.from_dept_name = from_dept.name if from_dept else None
        response.to_dept_name = to_dept.name if to_dept else None
        response.creator_name = creator.full_name if creator else None
        response.assigned_to_name = assigned.full_name if assigned else None
        response.person_name = person.name if person else None
        result.append(response)
    
    return result

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ticket details"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not can_view_ticket(ticket, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
    
    # Load related data
    from_dept = db.query(Department).filter(Department.id == ticket.from_dept_id).first()
    to_dept = db.query(Department).filter(Department.id == ticket.to_dept_id).first()
    creator = db.query(User).filter(User.id == ticket.created_by_user_id).first()
    assigned = db.query(User).filter(User.id == ticket.assigned_to_user_id).first() if ticket.assigned_to_user_id else None
    person = db.query(Person).filter(Person.id == ticket.person_id).first() if ticket.person_id else None
    
    # Load comments
    comments = db.query(TicketComment).filter(TicketComment.ticket_id == ticket_id).order_by(TicketComment.created_at).all()
    comment_responses = []
    for comment in comments:
        author = db.query(User).filter(User.id == comment.author_user_id).first()
        cr = TicketCommentResponse.model_validate(comment)
        cr.author_name = author.full_name if author else None
        comment_responses.append(cr)
    
    # Load attachments
    attachments = db.query(TicketAttachment).filter(TicketAttachment.ticket_id == ticket_id).order_by(TicketAttachment.created_at).all()
    
    response = TicketResponse.model_validate(ticket)
    response.from_dept_name = from_dept.name if from_dept else None
    response.to_dept_name = to_dept.name if to_dept else None
    response.creator_name = creator.full_name if creator else None
    response.assigned_to_name = assigned.full_name if assigned else None
    response.person_name = person.name if person else None
    response.comments = comment_responses
    response.attachments = [TicketAttachmentResponse.model_validate(a) for a in attachments]
    
    return response

@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    ticket_update: TicketUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ticket (status, assignment, priority)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not can_modify_ticket(ticket, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to modify this ticket")
    
    # Update fields
    if ticket_update.status:
        ticket.status = ticket_update.status
        if ticket_update.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            from datetime import datetime
            ticket.closed_at = datetime.utcnow()
    
    if ticket_update.assigned_to_user_id is not None:
        # Verify user is in target department
        assigned_user = db.query(User).filter(User.id == ticket_update.assigned_to_user_id).first()
        if not assigned_user or assigned_user.dept_id != ticket.to_dept_id:
            raise HTTPException(status_code=400, detail="Assigned user must be in target department")
        ticket.assigned_to_user_id = ticket_update.assigned_to_user_id
    
    if ticket_update.priority:
        ticket.priority = ticket_update.priority
    
    db.commit()
    db.refresh(ticket)
    
    # Audit log
    log_audit_event(
        db=db,
        action_type="TICKET_STATUS_CHANGED" if ticket_update.status else "TICKET_ASSIGNED" if ticket_update.assigned_to_user_id else "TICKET_UPDATED",
        entity_type="Ticket",
        entity_id=str(ticket.id),
        actor_user_id=current_user.id,
        action_metadata=ticket_update.model_dump(exclude_unset=True),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Return updated ticket
    return await get_ticket(ticket_id, db, current_user)

@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: UUID,
    comment_data: TicketCommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add comment to ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not can_view_ticket(ticket, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to comment on this ticket")
    
    comment = TicketComment(
        ticket_id=ticket_id,
        author_user_id=current_user.id,
        message=comment_data.message
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Audit log
    log_audit_event(
        db=db,
        action_type="TICKET_COMMENT_ADDED",
        entity_type="Ticket",
        entity_id=str(ticket_id),
        actor_user_id=current_user.id,
        action_metadata={"comment_id": str(comment.id)},
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    author = db.query(User).filter(User.id == comment.author_user_id).first()
    response = TicketCommentResponse.model_validate(comment)
    response.author_name = author.full_name if author else None
    
    return response

@router.post("/{ticket_id}/attachments", response_model=TicketAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    ticket_id: UUID,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload attachment to ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not can_view_ticket(ticket, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to attach files to this ticket")
    
    if not storage_service.available:
        raise HTTPException(status_code=503, detail="File storage unavailable")
    
    # Read file
    file_content = await file.read()
    file_key = f"tickets/{ticket_id}/{uuid.uuid4()}_{file.filename}"
    
    # Upload to storage
    storage_service.upload_file(file_content, file_key, file.content_type or "application/octet-stream")
    
    # Save attachment record
    attachment = TicketAttachment(
        ticket_id=ticket_id,
        uploaded_by_user_id=current_user.id,
        file_name=file.filename,
        file_key=file_key,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(file_content)
    )
    
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
    # Audit log
    log_audit_event(
        db=db,
        action_type="TICKET_ATTACHMENT_UPLOADED",
        entity_type="Ticket",
        entity_id=str(ticket_id),
        actor_user_id=current_user.id,
        action_metadata={"attachment_id": str(attachment.id), "file_name": file.filename},
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None
    )
    
    return TicketAttachmentResponse.model_validate(attachment)

