"""HR Document Generation Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.person import Person, PersonStatus
from app.models.employment import Employment, EmploymentType
from app.models.finance_kyc import FinanceKYC
from app.models.rate_plan import RatePlan
from app.models.master_data import CompanyMaster
from app.models.template import Template, TemplateRevision, TemplateType, RevisionStatus
from app.models.document import Document, DocumentStage, DocumentCategory, DocumentOwnerDept
from app.models.hr_document_draft import HrDocumentDraft
from app.schemas.document import DocumentResponse
from app.services.template_renderer import render_template
from app.services.pdf_generator import generate_pdf_from_html
from app.services.document_data_builder import build_appointment_data, build_declaration_data
from app.core.storage import storage_service
from app.services.document_access import enforce_can_download
from app.services.audit_logger import log_audit_event, get_client_ip, get_user_agent
from app.api.v1.dependencies.permissions import require_permission
from app.core.permissions import PermissionCode
from pydantic import BaseModel
import uuid
import io

router = APIRouter()

class DocumentGenerationRequest(BaseModel):
    docType: str  # "APPOINTMENT" or "DECLARATION"

class DocumentStatusResponse(BaseModel):
    canGenerate: bool
    templateKeyUsed: str | None = None
    lastGeneratedAt: str | None = None
    lastDocumentId: int | None = None  # For download / send validation
    missingRatePlan: bool = False
    missingKyc: bool = False
    missingEmployment: bool = False
    missingTemplate: bool = False
    missingCompany: bool = False

class DocumentsStatusResponse(BaseModel):
    appointment: DocumentStatusResponse
    declaration: DocumentStatusResponse


class SendHrPackRequest(BaseModel):
    to_email: str | None = None
    cc: list[str] | None = None


class HrPackDocItem(BaseModel):
    id: int
    doc_name: str
    doc_category: str
    file_key: str


class GenerateHrPackResponse(BaseModel):
    documents: list[HrPackDocItem]

def get_template_key_for_appointment(employment_type: EmploymentType) -> TemplateType:
    """Map employment type to template key"""
    if employment_type == EmploymentType.PERMANENT:
        return TemplateType.APPOINTMENT_PERMANENT
    elif employment_type == EmploymentType.FREELANCER:
        return TemplateType.APPOINTMENT_FREELANCER
    elif employment_type == EmploymentType.CONTRACTUAL:
        return TemplateType.APPOINTMENT_CONTRACTUAL
    else:
        return TemplateType.APPOINTMENT_PERMANENT  # Default

def get_active_template_revision(db: Session, template_type: TemplateType) -> TemplateRevision | None:
    """Prefer active template (is_active=true) for this type with published revision; else first template of type with published revision."""
    # 1) Active template for this type
    active_tpl = db.query(Template).filter(
        Template.type == template_type,
        Template.is_active == True
    ).first()
    if active_tpl:
        rev = None
        if active_tpl.active_revision_id:
            rev = db.query(TemplateRevision).filter(
                TemplateRevision.id == active_tpl.active_revision_id,
                TemplateRevision.status == RevisionStatus.PUBLISHED
            ).first()
        if not rev:
            rev = db.query(TemplateRevision).filter(
                TemplateRevision.template_id == active_tpl.id,
                TemplateRevision.status == RevisionStatus.PUBLISHED
            ).order_by(TemplateRevision.created_at.desc()).first()
        if rev:
            return rev
    # 2) Fallback: any template of this type with published revision
    template = db.query(Template).filter(Template.type == template_type).first()
    if not template:
        return None
    if template.active_revision_id:
        active_revision = db.query(TemplateRevision).filter(
            TemplateRevision.id == template.active_revision_id,
            TemplateRevision.status == RevisionStatus.PUBLISHED
        ).first()
        if active_revision:
            return active_revision
    latest_published = db.query(TemplateRevision).filter(
        TemplateRevision.template_id == template.id,
        TemplateRevision.status == RevisionStatus.PUBLISHED
    ).order_by(TemplateRevision.created_at.desc()).first()
    return latest_published


def get_published_template(db: Session, template_type: TemplateType) -> TemplateRevision | None:
    """Get latest published template for given type (uses active template when is_active is set)."""
    return get_active_template_revision(db, template_type)


async def _generate_and_save_hr_document(
    db: Session,
    person_id: UUID,
    doc_type: str,
    current_user: User,
) -> Document:
    """
    Generate PDF for one HR doc (APPOINTMENT or DECLARATION), upload to storage, create Document row, audit.
    Raises HTTPException on validation/template/storage errors.
    """
    from app.models.document import DocumentOwnerDept, DocumentCategory, DocumentVisibilityScope
    import logging
    logger = logging.getLogger(__name__)

    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    employment = db.query(Employment).filter(
        Employment.person_id == person_id,
        Employment.is_active == True,
    ).first()
    if not employment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employment record not found. Please complete Finance processing first.")
    if not employment.employee_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee code not assigned. Please complete Finance processing first.")

    finance_kyc = db.query(FinanceKYC).filter(FinanceKYC.person_id == person_id).first()
    if not finance_kyc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Finance KYC not found. Please complete Finance processing first.")

    company = None
    if employment.company_id:
        company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company not assigned. Please complete Finance processing first.")

    rate_plan = None
    if doc_type.upper() == "APPOINTMENT":
        rate_plan = db.query(RatePlan).filter(RatePlan.person_id == person_id).order_by(RatePlan.created_at.desc()).first()
        if not rate_plan:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rate plan not found. Please complete Finance processing and add rate plan first.")

    if doc_type.upper() == "APPOINTMENT":
        template_type = get_template_key_for_appointment(employment.employment_type)
    elif doc_type.upper() == "DECLARATION":
        template_type = TemplateType.DECLARATION
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid doc_type: {doc_type}. Must be 'appointment' or 'declaration'.")

    template_revision = get_published_template(db, template_type)
    if not template_revision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template not found for {doc_type}. Please contact administrator to set up templates.")

    draft = db.query(HrDocumentDraft).filter(
        HrDocumentDraft.person_id == person_id,
        HrDocumentDraft.doc_type == doc_type.upper()
    ).first()

    if draft and draft.content:
        rendered_html = draft.content
    else:
        if doc_type.upper() == "APPOINTMENT":
            data = build_appointment_data(person, employment, finance_kyc, rate_plan, company, db)
        else:
            data = build_declaration_data(person, employment, finance_kyc, company, db)
        rendered_html = render_template(template_revision.content, data)
    try:
        pdf_bytes = await generate_pdf_from_html(rendered_html)
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation failed: {str(e)}")

    file_key = f"persons/{person_id}/{doc_type.lower()}_{uuid.uuid4()}.pdf"
    doc_name = "Appointment Letter" if doc_type.upper() == "APPOINTMENT" else "Declaration"

    if not storage_service.available:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="File storage is not available")
    try:
        storage_service.upload_file(pdf_bytes, file_key, "application/pdf")
    except Exception as e:
        logger.error(f"Failed to upload document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload document: {str(e)}")

    if doc_type.upper() == "APPOINTMENT":
        doc_category = DocumentCategory.APPOINTMENT
    elif doc_type.upper() == "DECLARATION":
        doc_category = DocumentCategory.DECLARATION
    else:
        doc_category = DocumentCategory.HR_SIGNED

    document = Document(
        person_id=person_id,
        stage=DocumentStage.HR,
        owner_dept=DocumentOwnerDept.HR,
        doc_category=doc_category,
        visibility_scope=DocumentVisibilityScope.PRIVATE,
        doc_name=doc_name,
        file_key=file_key,
        mime_type="application/pdf",
        size_bytes=len(pdf_bytes),
        is_mandatory=True,
        created_by_user_id=current_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    action_type = "HR_DECLARATION_GENERATED" if doc_category == DocumentCategory.DECLARATION else "APPOINTMENT_GENERATED"
    log_audit_event(
        db=db,
        action_type=action_type,
        entity_type="Person",
        entity_id=str(person_id),
        actor_user_id=current_user.id,
        action_metadata={"doc_id": document.id, "doc_name": doc_name, "doc_category": doc_category.value},
        ip_address=None,
        user_agent=None,
    )
    return document


@router.get("/persons/{person_id}/documents", response_model=DocumentsStatusResponse)
async def get_document_status(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document generation status for a person"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Check if finance is completed (has employee code)
    employment = db.query(Employment).filter(
        Employment.person_id == person_id,
        Employment.is_active == True
    ).first()
    
    # Check all prerequisites
    has_employment = employment is not None
    has_employee_code = employment and employment.employee_code
    has_finance_kyc = db.query(FinanceKYC).filter(FinanceKYC.person_id == person_id).first() is not None
    has_rate_plan = db.query(RatePlan).filter(RatePlan.person_id == person_id).order_by(RatePlan.created_at.desc()).first() is not None
    has_company = employment and employment.company_id and db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first() is not None
    
    # Check appointment template availability
    appointment_template_type = None
    appointment_template = None
    if employment:
        appointment_template_type = get_template_key_for_appointment(employment.employment_type)
        appointment_template = get_published_template(db, appointment_template_type)
    
    # Check declaration template availability
    declaration_template = get_published_template(db, TemplateType.DECLARATION)
    
    # Get last generated documents (by doc_category)
    last_appointment = db.query(Document).filter(
        Document.person_id == person_id,
        Document.doc_category == DocumentCategory.APPOINTMENT
    ).order_by(Document.created_at.desc()).first()
    
    last_declaration = db.query(Document).filter(
        Document.person_id == person_id,
        Document.doc_category == DocumentCategory.DECLARATION
    ).order_by(Document.created_at.desc()).first()
    
    # Appointment prerequisites
    appointment_can_generate = (
        has_employment and 
        has_employee_code and 
        has_finance_kyc and 
        has_rate_plan and 
        has_company and 
        appointment_template is not None
    )
    
    # Declaration prerequisites (no rate plan needed)
    declaration_can_generate = (
        has_employment and 
        has_employee_code and 
        has_finance_kyc and 
        has_company and 
        declaration_template is not None
    )
    
    return DocumentsStatusResponse(
        appointment=DocumentStatusResponse(
            canGenerate=appointment_can_generate,
            templateKeyUsed=appointment_template_type.value if appointment_template_type else None,
            lastGeneratedAt=last_appointment.created_at.isoformat() if last_appointment else None,
            lastDocumentId=last_appointment.id if last_appointment else None,
            missingRatePlan=not has_rate_plan,
            missingKyc=not has_finance_kyc,
            missingEmployment=not has_employment,
            missingTemplate=appointment_template is None,
            missingCompany=not has_company
        ),
        declaration=DocumentStatusResponse(
            canGenerate=declaration_can_generate,
            templateKeyUsed=TemplateType.DECLARATION.value if declaration_template else None,
            lastGeneratedAt=last_declaration.created_at.isoformat() if last_declaration else None,
            lastDocumentId=last_declaration.id if last_declaration else None,
            missingRatePlan=False,  # Declaration doesn't need rate plan
            missingKyc=not has_finance_kyc,
            missingEmployment=not has_employment,
            missingTemplate=declaration_template is None,
            missingCompany=not has_company
        )
    )


class DraftContentBody(BaseModel):
    content: str


@router.get("/persons/{person_id}/draft/{doc_type}")
async def get_draft(
    person_id: UUID,
    doc_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.DOC_UPLOAD_HR))
):
    """Get HR-edited draft content for this person and doc type (APPOINTMENT/DECLARATION). Returns 404 if no draft."""
    if doc_type.upper() not in ("APPOINTMENT", "DECLARATION"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doc_type must be APPOINTMENT or DECLARATION")
    draft = db.query(HrDocumentDraft).filter(
        HrDocumentDraft.person_id == person_id,
        HrDocumentDraft.doc_type == doc_type.upper()
    ).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No draft found")
    return {"content": draft.content}


@router.put("/persons/{person_id}/draft/{doc_type}")
async def save_draft(
    person_id: UUID,
    doc_type: str,
    body: DraftContentBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.DOC_UPLOAD_HR))
):
    """Save HR-edited content as draft for this person and doc type. Creates or updates. Does not overwrite base template."""
    if doc_type.upper() not in ("APPOINTMENT", "DECLARATION"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doc_type must be APPOINTMENT or DECLARATION")
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    draft = db.query(HrDocumentDraft).filter(
        HrDocumentDraft.person_id == person_id,
        HrDocumentDraft.doc_type == doc_type.upper()
    ).first()
    if draft:
        draft.content = body.content
        draft.created_by_user_id = current_user.id
    else:
        draft = HrDocumentDraft(
            person_id=person_id,
            doc_type=doc_type.upper(),
            content=body.content,
            created_by_user_id=current_user.id
        )
        db.add(draft)
    db.commit()
    db.refresh(draft)
    return {"id": draft.id, "saved": True}


@router.post("/persons/{person_id}/generate")
async def generate_document(
    person_id: UUID,
    request: DocumentGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate appointment letter or declaration PDF"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Get employment
    employment = db.query(Employment).filter(
        Employment.person_id == person_id,
        Employment.is_active == True
    ).first()
    
    if not employment or not employment.employee_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finance processing not completed. Employee code is required."
        )
    
    # Get finance KYC
    finance_kyc = db.query(FinanceKYC).filter(FinanceKYC.person_id == person_id).first()
    if not finance_kyc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finance KYC not found"
        )
    
    # Get company
    company = None
    if employment.company_id:
        company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company not assigned"
        )
    
    # Get rate plan for appointment
    rate_plan = None
    if request.docType == "APPOINTMENT":
        rate_plan = db.query(RatePlan).filter(
            RatePlan.person_id == person_id
        ).order_by(RatePlan.created_at.desc()).first()
    
    # Determine template type
    if request.docType == "APPOINTMENT":
        template_type = get_template_key_for_appointment(employment.employment_type)
    elif request.docType == "DECLARATION":
        template_type = TemplateType.DECLARATION
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid docType: {request.docType}"
        )
    
    # Get published template
    template_revision = get_published_template(db, template_type)
    if not template_revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No published template found for {template_type.value}"
        )
    
    # Build data
    if request.docType == "APPOINTMENT":
        if not rate_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rate plan not found"
            )
        data = build_appointment_data(person, employment, finance_kyc, rate_plan, company, db)
    else:
        data = build_declaration_data(person, employment, finance_kyc, company, db)
    
    # Render template
    try:
        rendered_html = render_template(template_revision.content, data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template rendering failed: {str(e)}"
        )
    
    # Generate PDF
    try:
        pdf_bytes = await generate_pdf_from_html(rendered_html)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}"
        )
    
    # Upload to storage
    file_key = f"persons/{person_id}/{request.docType.lower()}_{uuid.uuid4()}.pdf"
    doc_name = "Appointment Letter" if request.docType == "APPOINTMENT" else "Declaration"
    
    if not storage_service.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage (MinIO) is not available"
        )
    
    try:
        storage_service.upload_file(pdf_bytes, file_key, "application/pdf")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )
    
    # Save document record
    from app.models.document import DocumentOwnerDept, DocumentCategory, DocumentVisibilityScope
    # Determine category from docType
    if request.docType == "APPOINTMENT":
        doc_category = DocumentCategory.APPOINTMENT
    elif request.docType == "DECLARATION":
        doc_category = DocumentCategory.DECLARATION
    else:
        doc_category = DocumentCategory.HR_SIGNED  # Fallback
    
    document = Document(
        person_id=person_id,
        stage=DocumentStage.HR,
        owner_dept=DocumentOwnerDept.HR,  # Access Model: HR owns HR documents
        doc_category=doc_category,
        visibility_scope=DocumentVisibilityScope.PRIVATE,  # Access Model: HR docs are private by default
        doc_name=doc_name,
        file_key=file_key,
        mime_type="application/pdf",
        size_bytes=len(pdf_bytes),
        is_mandatory=True,
        created_by_user_id=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Return PDF as download
    filename = f"{doc_name.replace(' ', '_')}_{employment.employee_code or person.name.replace(' ', '_')}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.get("/persons/{person_id}/preview/{doc_type}")
async def preview_document(
    person_id: UUID,
    doc_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview rendered HTML (for testing)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        employment = db.query(Employment).filter(
            Employment.person_id == person_id,
            Employment.is_active == True
        ).first()
        
        # Check prerequisites and collect missing items
        missing_items = []
        
        employment = db.query(Employment).filter(
            Employment.person_id == person_id,
            Employment.is_active == True
        ).first()
        
        if not employment:
            missing_items.append("Employment record")
        elif not employment.employee_code:
            missing_items.append("Employee code")
        
        finance_kyc = db.query(FinanceKYC).filter(FinanceKYC.person_id == person_id).first()
        if not finance_kyc:
            missing_items.append("Finance KYC")
        
        company = None
        if employment and employment.company_id:
            company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
        if not company:
            missing_items.append("Company assignment")
        
        # Check rate plan for appointment
        rate_plan = None
        if doc_type.upper() == "APPOINTMENT":
            rate_plan = db.query(RatePlan).filter(RatePlan.person_id == person_id).order_by(RatePlan.created_at.desc()).first()
            if not rate_plan:
                missing_items.append("Rate Plan")
        
        # If prerequisites missing, return 422 with structured message
        if missing_items:
            logger.warning(f"Missing prerequisites for preview: {missing_items}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot preview. Missing: {', '.join(missing_items)}. Please complete Finance processing first."
            )
        
        # Determine template type
        if doc_type.upper() == "APPOINTMENT":
            template_type = get_template_key_for_appointment(employment.employment_type)
            data = build_appointment_data(person, employment, finance_kyc, rate_plan, company, db)
        elif doc_type.upper() == "DECLARATION":
            template_type = TemplateType.DECLARATION
            data = build_declaration_data(person, employment, finance_kyc, company, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid doc_type: {doc_type}. Must be 'appointment' or 'declaration'"
            )
        
        template_revision = get_published_template(db, template_type)
        if not template_revision:
            logger.warning(f"Template not found for type={template_type.value}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found for {doc_type}. Please contact administrator to set up templates."
            )
        
        rendered_html = render_template(template_revision.content, data)
        
        return HTMLResponse(content=rendered_html)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in preview_document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )

@router.get("/persons/{person_id}/download/appointment")
async def download_appointment_pdf(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.DOC_HR_DOWNLOAD))
):
    """
    Download system-generated Appointment Letter PDF.
    Generates PDF on-the-fly from template and returns as streaming response.
    Does not save to database (use publish endpoint to save).
    
    IMPORTANT: This endpoint is separate from CV Wallet download.
    Requires DOC_HR_DOWNLOAD permission.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        # Access control: Only HR and Master Admin can download appointment letters
        from app.services.document_access import is_master_admin
        from app.models.department import Department
        
        is_hr_user = False
        if current_user.dept_id:
            user_dept = db.query(Department).filter(Department.id == current_user.dept_id).first()
            if user_dept:
                dept_name = str(user_dept.name if hasattr(user_dept, 'name') else user_dept).upper()
                is_hr_user = "HR" in dept_name or "HUMAN RESOURCES" in dept_name
        
        if not is_master_admin(current_user, db) and not is_hr_user:
            log_audit_event(
                db=db,
                action_type="DOC_DOWNLOAD_BLOCKED",
                entity_type="Document",
                entity_id=None,
                actor_user_id=current_user.id,
                action_metadata={
                    "person_id": str(person.id),
                    "doc_type": "APPOINTMENT",
                    "block_reason": "Only HR and Master Admin can download appointment letters"
                },
                ip_address=None,
                user_agent=None
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only HR and Master Admin can download appointment letters"
            )
        
        # Get employment
        employment = db.query(Employment).filter(
            Employment.person_id == person_id,
            Employment.is_active == True
        ).first()
        
        if not employment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employment record not found. Please complete Finance processing first."
            )
        
        if not employment.employee_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee code not assigned. Please complete Finance processing first."
            )
        
        # Get finance KYC
        finance_kyc = db.query(FinanceKYC).filter(FinanceKYC.person_id == person_id).first()
        if not finance_kyc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Finance KYC not found. Please complete Finance processing first."
            )
        
        # Get company
        company = None
        if employment.company_id:
            company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company not assigned. Please complete Finance processing first."
            )
        
        # Get rate plan (required for appointment)
        rate_plan = db.query(RatePlan).filter(
            RatePlan.person_id == person_id
        ).order_by(RatePlan.created_at.desc()).first()
        
        if not rate_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rate plan not found. Please complete Finance processing and add rate plan first."
            )
        
        # Determine template type
        template_type = get_template_key_for_appointment(employment.employment_type)
        
        # Get published template
        template_revision = get_published_template(db, template_type)
        if not template_revision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found for appointment letter. Please contact administrator to set up templates."
            )
        
        # Build data
        data = build_appointment_data(person, employment, finance_kyc, rate_plan, company, db)
        
        # Render template
        rendered_html = render_template(template_revision.content, data)
        
        # Generate PDF
        pdf_bytes = await generate_pdf_from_html(rendered_html)
        
        # Return as streaming response
        filename = f"Appointment_Letter_{employment.employee_code or person.name.replace(' ', '_')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download_appointment_pdf: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate appointment letter PDF: {str(e)}"
        )

@router.post("/persons/{person_id}/publish/{doc_type}", response_model=DocumentResponse)
async def publish_document(
    person_id: UUID,
    doc_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.DOC_UPLOAD_HR))
):
    """
    Generate PDF, upload to storage, and create Document record.
    This is the "publish" endpoint that saves the document to DB.
    Requires DOC_UPLOAD_HR permission.
    """
    try:
        document = await _generate_and_save_hr_document(db, person_id, doc_type, current_user)
        return document
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in publish_document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish document: {str(e)}"
        )


@router.post("/persons/{person_id}/generate-hr-pack", response_model=GenerateHrPackResponse)
async def generate_hr_pack(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.DOC_UPLOAD_HR))
):
    """
    Generate both Appointment Letter and Declaration PDFs, save to storage and DB.
    Returns list of created/updated documents. Audit: HR_PACK_GENERATED.
    """
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    docs: list[Document] = []
    try:
        doc_app = await _generate_and_save_hr_document(db, person_id, "APPOINTMENT", current_user)
        docs.append(doc_app)
        doc_dec = await _generate_and_save_hr_document(db, person_id, "DECLARATION", current_user)
        docs.append(doc_dec)
    except HTTPException:
        raise

    log_audit_event(
        db=db,
        action_type="HR_PACK_GENERATED",
        entity_type="Person",
        entity_id=str(person_id),
        actor_user_id=current_user.id,
        action_metadata={
            "doc_ids": [d.id for d in docs],
            "doc_names": [d.doc_name for d in docs],
        },
        ip_address=None,
        user_agent=None,
    )

    return GenerateHrPackResponse(
        documents=[
            HrPackDocItem(id=d.id, doc_name=d.doc_name, doc_category=d.doc_category.value, file_key=d.file_key)
            for d in docs
        ]
    )


@router.post("/persons/{person_id}/send-hr-pack")
async def send_hr_pack(
    person_id: UUID,
    body: SendHrPackRequest | None = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.HR_IDCARD_SEND))
):
    """
    Send Appointment and Declaration PDFs to the person's email as attachments.
    Hard validation: both documents must exist; otherwise 400 with clear message.
    Audit: HR_PACK_SENT.
    """
    from app.services.email_sender import send_email

    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    to_email = (body and body.to_email and body.to_email.strip()) or (person.email and person.email.strip())
    if not to_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipient email. Provide to_email or ensure person has email."
        )

    appointment_doc = (
        db.query(Document)
        .filter(
            Document.person_id == person_id,
            Document.doc_category == DocumentCategory.APPOINTMENT,
        )
        .order_by(Document.created_at.desc())
        .first()
    )
    declaration_doc = (
        db.query(Document)
        .filter(
            Document.person_id == person_id,
            Document.doc_category == DocumentCategory.DECLARATION,
        )
        .order_by(Document.created_at.desc())
        .first()
    )

    missing = []
    if not appointment_doc:
        missing.append("Appointment")
    if not declaration_doc:
        missing.append("Declaration")
    if missing:
        msg = "Generate Appointment & Declaration first. Missing: " + ", ".join(missing) + "."
        import logging
        logging.getLogger(__name__).warning(f"[send-hr-pack] person_id={person_id} blocked: {msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    try:
        app_bytes = storage_service.get_file(appointment_doc.file_key)
        dec_bytes = storage_service.get_file(declaration_doc.file_key)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to fetch HR docs from storage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read document files from storage.",
        )

    from datetime import datetime
    date_str = datetime.now().strftime("%d-%m-%Y")
    app_filename = f"Appointment_Letter_{person.name.replace(' ', '_')}_{date_str}.pdf"
    dec_filename = f"Declaration_{person.name.replace(' ', '_')}_{date_str}.pdf"

    subject = f"Appointment & Declaration – {person.name}"
    html_body = f"""
    <p>Dear {person.name},</p>
    <p>Please find attached your Appointment Letter and Declaration.</p>
    <p>Person ID: {person_id}</p>
    <p>Best regards,<br/>HR Team</p>
    """
    text_body = f"Dear {person.name},\n\nPlease find attached your Appointment Letter and Declaration.\nPerson ID: {person_id}\n\nBest regards,\nHR Team"

    send_email(
        db=db,
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        cc=body.cc if body else None,
        attachments=[
            (app_filename, app_bytes, "application/pdf"),
            (dec_filename, dec_bytes, "application/pdf"),
        ],
        template_key="hr_pack",
        entity_type="Person",
        entity_id=str(person_id),
        log_metadata={"doc_ids": [appointment_doc.id, declaration_doc.id]},
    )

    log_audit_event(
        db=db,
        action_type="HR_DOC_SENT",
        entity_type="Person",
        entity_id=str(person_id),
        actor_user_id=current_user.id,
        action_metadata={
            "to_email": to_email,
            "doc_ids": [appointment_doc.id, declaration_doc.id],
        },
        ip_address=None,
        user_agent=None,
    )

    return {"sent": True}


@router.get("/documents/{doc_id}/download")
async def download_hr_document(
    doc_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.DOC_HR_DOWNLOAD))
):
    """
    Download an HR-owned document (Appointment, Declaration, HR_SIGNED, etc.).
    Uses centralized access control.
    Requires DOC_HR_DOWNLOAD permission.
    """
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.owner_dept != DocumentOwnerDept.HR:
        # Only HR-owned documents are served from this endpoint
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Locked. Request access."
        )

    person = db.query(Person).filter(Person.id == document.person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    # Use centralized access control (single source of truth)
    # This will raise HTTPException 403 if access denied
    from app.services.document_access import enforce_can_download
    enforce_can_download(db, current_user, person, document, request)

    # Download from storage
    try:
        file_exists = storage_service.file_exists(document.file_key)
        if not file_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found on disk: {document.file_key}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check file existence: {str(e)}"
        )

    log_audit_event(
        db=db,
        action_type="DOC_DOWNLOADED",
        entity_type="Document",
        entity_id=str(document.id),
        actor_user_id=current_user.id,
        action_metadata={"person_id": str(document.person_id), "doc_name": document.doc_name},
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
    )

    try:
        file_data = storage_service.get_file(document.file_key)
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=document.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document.doc_name}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

