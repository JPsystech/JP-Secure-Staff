from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.dependencies.permissions import require_permission
from app.core.permissions import PermissionCode
from app.models.user import User
from app.models.person import Person, PersonStatus
from app.models.document import Document, DocumentStage
from app.schemas.person import PersonSummaryResponse
from app.core.storage import storage_service
from app.core.email_config import AUTO_SEND_ID_CARD
from app.services.email_automation import send_id_card_email
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

router = APIRouter()

@router.get("/inbox", response_model=List[PersonSummaryResponse])
async def get_hr_inbox(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get persons sent to HR"""
    persons = db.query(Person).filter(
        Person.status == PersonStatus.SENT_TO_HR
    ).all()
    
    result = []
    for person in persons:
        from app.models.employment import Employment
        employment = db.query(Employment).filter(
            Employment.person_id == person.id,
            Employment.is_active == True
        ).first()
        
        employee_code = employment.employee_code if employment else None
        company_name = None
        if employment and employment.company_id:
            from app.models.master_data import CompanyMaster
            company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
            company_name = company.name if company else None
        
        response = PersonSummaryResponse.model_validate(person)
        response.employee_code = employee_code
        response.company_name = company_name
        result.append(response)
    
    return result

@router.post("/persons/{person_id}/generate-declaration")
async def generate_declaration(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate declaration PDF"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Simple declaration content
    p.drawString(100, height - 100, "DECLARATION")
    p.drawString(100, height - 130, f"I, {person.name}, hereby declare that...")
    p.drawString(100, height - 160, f"Date: {person.created_at.strftime('%Y-%m-%d') if person.created_at else ''}")
    p.save()
    
    buffer.seek(0)
    pdf_data = buffer.read()
    
    # Upload to MinIO (if available)
    import uuid
    file_key = f"persons/{person_id}/declaration_{uuid.uuid4()}.pdf"
    
    if not storage_service.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage (MinIO) is not available. Please start MinIO server to generate documents."
        )
    
    try:
        storage_service.upload_file(pdf_data, file_key, "application/pdf")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )
    
    # Save document record
    from app.models.document import DocumentOwnerDept, DocumentCategory, DocumentVisibilityScope
    document = Document(
        person_id=person_id,
        stage=DocumentStage.HR,
        owner_dept=DocumentOwnerDept.HR,  # Access Model: HR owns HR documents
        doc_category=DocumentCategory.HR_SIGNED,
        visibility_scope=DocumentVisibilityScope.PRIVATE,  # Access Model: HR docs are private by default
        doc_name="Declaration",
        file_key=file_key,
        mime_type="application/pdf",
        size_bytes=len(pdf_data),
        is_mandatory=True,
        created_by_user_id=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return {"file_key": file_key, "document_id": document.id}

@router.post("/persons/{person_id}/generate-appointment")
async def generate_appointment(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate appointment letter draft (returns editable text)"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    from app.models.employment import Employment
    employment = db.query(Employment).filter(
        Employment.person_id == person_id,
        Employment.is_active == True
    ).first()
    
    # Generate draft text
    draft_text = f"""
APPOINTMENT LETTER

Date: {person.created_at.strftime('%d-%m-%Y') if person.created_at else '[DATE]'}

Dear {person.name},

We are pleased to offer you the position of [POSITION] on {employment.employment_type.value if employment else '[TYPE]'} basis.

Employee Code: {employment.employee_code if employment else '[CODE]'}

[Additional terms and conditions...]

Please sign and return this letter to confirm your acceptance.

Yours sincerely,
[Company Name]
"""
    
    return {"draft_text": draft_text.strip()}

@router.patch("/persons/{person_id}/appointment")
async def save_appointment(
    person_id: UUID,
    appointment_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save edited appointment letter"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    appointment_text = appointment_data.get("appointment_text", "")
    
    # Convert text to PDF and save
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    y = height - 100
    lines = appointment_text.split('\n')
    for line in lines[:50]:  # Limit to 50 lines
        if y < 100:
            p.showPage()
            y = height - 100
        p.drawString(100, y, line[:80])  # Limit line length
        y -= 20
    
    p.save()
    buffer.seek(0)
    pdf_data = buffer.read()
    
    # Upload to MinIO (if available)
    import uuid
    file_key = f"persons/{person_id}/appointment_{uuid.uuid4()}.pdf"
    
    if not storage_service.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage (MinIO) is not available. Please start MinIO server to save documents."
        )
    
    try:
        storage_service.upload_file(pdf_data, file_key, "application/pdf")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )
    
    # Save document
    from app.models.document import DocumentOwnerDept, DocumentCategory, DocumentVisibilityScope
    document = Document(
        person_id=person_id,
        stage=DocumentStage.HR,
        owner_dept=DocumentOwnerDept.HR,  # Access Model: HR owns HR documents
        doc_category=DocumentCategory.APPOINTMENT,
        visibility_scope=DocumentVisibilityScope.PRIVATE,  # Access Model: HR docs are private by default
        doc_name="Appointment Letter",
        file_key=file_key,
        mime_type="application/pdf",
        size_bytes=len(pdf_data),
        is_mandatory=True,
        created_by_user_id=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return {"file_key": file_key, "document_id": document.id}

@router.post("/persons/{person_id}/upload-signed")
async def upload_signed_docs(
    person_id: UUID,
    declaration_file_key: str,
    appointment_file_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark signed documents as uploaded"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Update document records or create new ones
    # This is a simplified version - in production, you'd upload actual files
    return {"message": "Signed documents recorded"}

@router.post("/persons/{person_id}/mark-active", response_model=PersonSummaryResponse)
async def mark_active(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark person as active"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    if person.status != PersonStatus.SENT_TO_HR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person must be in SENT_TO_HR status"
        )

    person.status = PersonStatus.ACTIVE
    db.commit()
    db.refresh(person)

    # Auto-send ID card email when moving to ACTIVE (guarded by AUTO_SEND_ID_CARD)
    if AUTO_SEND_ID_CARD:
        try:
            send_id_card_email(db, person, skip_if_already_sent=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Auto send ID card failed: %s", e)
    
    # Return summary
    from app.models.employment import Employment
    employment = db.query(Employment).filter(
        Employment.person_id == person_id,
        Employment.is_active == True
    ).first()
    
    employee_code = employment.employee_code if employment else None
    company_name = None
    if employment and employment.company_id:
        from app.models.master_data import CompanyMaster
        company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
        company_name = company.name if company else None
    
    response = PersonSummaryResponse.model_validate(person)
    response.employee_code = employee_code
    response.company_name = company_name
    return response


@router.post("/persons/{person_id}/send-id-card")
async def send_id_card(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.HR_IDCARD_SEND)),
):
    """
    Generate ID card PDF, send to person email, log in EmailLog + audit.
    Requires HR_IDCARD_SEND permission.
    """
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    if not person.email or not person.email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person has no email; cannot send ID card"
        )
    email_log = send_id_card_email(db, person, skip_if_already_sent=False)
    return {
        "message": "ID card email sent",
        "email_log_id": str(email_log.id),
        "status": email_log.status,
    }

