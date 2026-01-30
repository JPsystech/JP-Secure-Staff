from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import io
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.person import Person, PersonStatus
from app.models.employment import Employment
from app.models.finance_kyc import FinanceKYC
from app.models.rate_plan import RatePlan
from app.schemas.person import PersonSummaryResponse
from app.schemas.employment import EmploymentCreate, EmploymentResponse
from app.schemas.finance_kyc import FinanceKYCCreate, FinanceKYCResponse
from app.schemas.rate_plan import RatePlanCreate, RatePlanResponse
from app.schemas.document import DocumentResponse
from app.services.employee_code import generate_employee_code
from app.core.storage import storage_service
from app.core.normalize import normalize_uppercase_fields
from app.models.document import Document, DocumentOwnerDept
from app.services.document_access import enforce_can_download
from app.services.audit_logger import log_audit_event, get_client_ip, get_user_agent
from app.api.v1.dependencies.permissions import require_permission
from app.core.permissions import PermissionCode

router = APIRouter()

@router.get("/inbox", response_model=List[PersonSummaryResponse])
async def get_finance_inbox(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get persons submitted to finance"""
    persons = db.query(Person).filter(
        Person.status == PersonStatus.SUBMITTED_TO_FINANCE
    ).all()
    
    result = []
    for person in persons:
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

@router.post("/persons/{person_id}/assign", response_model=EmploymentResponse)
async def assign_employment(
    person_id: UUID,
    employment_data: EmploymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign employment type and generate employee code"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Generate employee code
    employee_code = generate_employee_code(
        db,
        employment_data.employment_type,
        employment_data.company_id
    )
    
    # Create or update employment
    employment = db.query(Employment).filter(
        Employment.person_id == person_id,
        Employment.is_active == True
    ).first()
    
    if employment:
        employment.employment_type = employment_data.employment_type
        employment.company_id = employment_data.company_id
        employment.employee_code = employee_code
    else:
        employment = Employment(
            person_id=person_id,
            employment_type=employment_data.employment_type,
            company_id=employment_data.company_id,
            employee_code=employee_code,
            is_active=True
        )
        db.add(employment)
    
    db.commit()
    db.refresh(employment)
    return employment

@router.post("/persons/{person_id}/kyc", response_model=FinanceKYCResponse)
async def create_kyc(
    person_id: UUID,
    kyc_data: FinanceKYCCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update finance KYC.
    
    FIXED: Handles empty strings from frontend, converts to None.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"KYC creation/update started for person_id={person_id}")
        
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            logger.error(f"Person not found: {person_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        # Convert empty strings to None and normalize ID-like fields (uppercase)
        kyc_dict = kyc_data.model_dump(exclude_unset=True)
        for key, value in kyc_dict.items():
            if value == '':
                kyc_dict[key] = None
        kyc_dict = normalize_uppercase_fields(kyc_dict)

        kyc = db.query(FinanceKYC).filter(FinanceKYC.person_id == person_id).first()
        
        if kyc:
            # Update existing
            for field, value in kyc_dict.items():
                setattr(kyc, field, value)
            logger.info(f"KYC updated for person_id={person_id}")
        else:
            # Create new
            kyc = FinanceKYC(
                person_id=person_id,
                **kyc_dict
            )
            db.add(kyc)
            logger.info(f"KYC created for person_id={person_id}")
        
        db.commit()
        db.refresh(kyc)
        return kyc
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating/updating KYC: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save KYC: {str(e)}"
        )

@router.post("/persons/{person_id}/rate-plan", response_model=RatePlanResponse)
async def create_rate_plan(
    person_id: UUID,
    rate_plan_data: RatePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create rate plan for person.
    
    FIXED: Handles frontend payload with empty strings converted to None.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Rate plan creation started for person_id={person_id}")
        
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            logger.error(f"Person not found: {person_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        # FIXED: Convert empty strings to None for optional fields
        plan_data = rate_plan_data.model_dump()
        
        # Handle empty strings from frontend
        if plan_data.get('valid_to') == '':
            plan_data['valid_to'] = None
        if plan_data.get('working_day_mode') == '':
            plan_data['working_day_mode'] = None
        if plan_data.get('project_id') == '' or plan_data.get('project_id') == 0:
            plan_data['project_id'] = None
        
        # Validate required fields
        if not plan_data.get('plan_type'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="plan_type is required"
            )
        if not plan_data.get('amount'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="amount is required"
            )
        if not plan_data.get('valid_from'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="valid_from is required"
            )
        
        logger.info(f"Rate plan data: {plan_data}")
        
        rate_plan = RatePlan(
            person_id=person_id,
            **plan_data
        )
        db.add(rate_plan)
        db.commit()
        db.refresh(rate_plan)
        
        logger.info(f"Rate plan created successfully: id={rate_plan.id}")
        
        return rate_plan
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating rate plan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rate plan: {str(e)}"
        )

def _has_required_finance_docs(db: Session, person_id: UUID) -> tuple[bool, list[str]]:
    """Check that person has Aadhaar, PAN, and Cancelled Cheque docs (Finance owner). Returns (ok, missing_list)."""
    docs = db.query(Document).filter(
        Document.person_id == person_id,
        Document.owner_dept == DocumentOwnerDept.FINANCE
    ).all()
    doc_names_lower = [d.doc_name.strip().lower() if d.doc_name else "" for d in docs]
    missing = []
    if not any("aadhaar" in n or "aadhar" in n for n in doc_names_lower):
        missing.append("Aadhaar card document")
    if not any("pan" in n for n in doc_names_lower):
        missing.append("PAN card document")
    if not any("cancelled" in n and ("cheque" in n or "passbook" in n) for n in doc_names_lower):
        missing.append("Cancelled cheque document")
    return (len(missing) == 0, missing)


@router.post("/persons/{person_id}/submit-to-hr", response_model=PersonSummaryResponse)
async def submit_to_hr(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit person to HR. Validates Finance KYC: bank_name and required docs (Aadhaar, PAN, Cancelled Cheque)."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    if person.status != PersonStatus.SUBMITTED_TO_FINANCE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person must be in SUBMITTED_TO_FINANCE status"
        )

    # Validate Finance KYC: bank_name required
    kyc = db.query(FinanceKYC).filter(FinanceKYC.person_id == person_id).first()
    if not kyc or not (kyc.bank_name and kyc.bank_name.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Bank name is required before submitting to HR. Please complete Finance KYC."
        )

    # Validate required documents: Aadhaar, PAN, Cancelled Cheque
    docs_ok, missing_docs = _has_required_finance_docs(db, person_id)
    if not docs_ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required Finance documents: " + ", ".join(missing_docs) + ". Please upload before submitting to HR."
        )
    
    # Access Model: Set status and activated_at when Finance sends to HR
    from datetime import datetime
    from app.services.audit_logger import log_audit_event
    old_status = person.status.value if person.status else None
    person.status = PersonStatus.SENT_TO_HR
    person.activated_at = datetime.utcnow()  # Person becomes visible to all departments
    person.hr_submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(person)
    
    # Audit log: STATUS_CHANGE
    log_audit_event(
        db=db,
        action_type="STATUS_CHANGE",
        entity_type="Person",
        entity_id=str(person.id),
        actor_user_id=current_user.id,
        action_metadata={
            "old_status": old_status,
            "new_status": "SENT_TO_HR",
            "activated_at": person.activated_at.isoformat() if person.activated_at else None,
            "hr_submitted_at": person.hr_submitted_at.isoformat() if person.hr_submitted_at else None
        },
        ip_address=None,
        user_agent=None
    )
    
    # Return summary
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
    
    response = PersonSummaryResponse.from_orm(person)
    response.employee_code = employee_code
    response.company_name = company_name
    return response

@router.post("/persons/{person_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_finance_document(
    person_id: UUID,
    file: UploadFile = File(...),
    doc_name: Optional[str] = Form(None),
    doc_category: Optional[str] = Form("FINANCE_KYC"),  # Default to FINANCE_KYC
    is_mandatory: Optional[str] = Form("false"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload Finance document (KYC or other Finance documents).
    This is a convenience endpoint that calls the main upload_document with Finance stage.
    """
    from app.api.v1.endpoints.persons import upload_document
    
    # Call the main upload endpoint with Finance stage
    return await upload_document(
        person_id=person_id,
        file=file,
        stage="FINANCE",
        doc_name=doc_name or file.filename,
        doc_category=doc_category,
        is_mandatory=is_mandatory,
        db=db,
        current_user=current_user
    )

@router.get("/persons/{person_id}/documents", response_model=List[DocumentResponse])
async def get_finance_documents(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Finance documents for a person"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Get Finance documents
    documents = db.query(Document).filter(
        Document.person_id == person_id,
        Document.owner_dept == DocumentOwnerDept.FINANCE
    ).order_by(Document.created_at.desc()).all()
    
    return documents


@router.get("/documents/{doc_id}/download")
async def download_finance_document(
    doc_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.DOC_FINANCE_DOWNLOAD))
):
    """
    Download a Finance-owned document (FINANCE_KYC, etc.).
    Uses centralized access control.
    Requires DOC_FINANCE_DOWNLOAD permission.
    """
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.owner_dept != DocumentOwnerDept.FINANCE:
        # Only Finance-owned documents are served from this endpoint
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

    try:
        file_data = storage_service.get_file(document.file_key)
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=document.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename=\"{document.doc_name}\"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

