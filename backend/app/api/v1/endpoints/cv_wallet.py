"""CV Wallet API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import io
import mimetypes
import logging
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.person import Person, PersonStatus
from app.models.document import Document, DocumentStage, DocumentCategory, DocumentOwnerDept
from app.models.policy import Policy
from app.models.rate_plan import RatePlan, PlanType
from app.schemas.person import PersonSummaryResponse
from app.schemas.document import DocumentResponse, StageADocumentResponse, StageADocumentsListResponse
from app.services.permission_checker import user_has_permission
from app.services.document_access import is_master_admin, evaluate_document_access
from app.core.storage import storage_service
from app.services.document_access import can_user_view_document, can_user_download_document, get_visible_documents_for_user, enforce_can_download
from app.services.audit_logger import log_audit_event, get_client_ip, get_user_agent
from app.api.v1.dependencies.permissions import require_permission
from app.core.permissions import PermissionCode

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[PersonSummaryResponse])
async def get_cv_wallet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get CV Wallet - list of persons visible to all departments.
    
    Returns persons where status in {SENT_TO_HR, ACTIVE, HR_COMPLETED}
    plus persons created by current user (for drafts).
    """
    # Get persons visible in CV Wallet (after finance submission)
    visible_statuses = [PersonStatus.SENT_TO_HR, PersonStatus.ACTIVE]
    
    query = db.query(Person).filter(
        Person.status.in_(visible_statuses)
    )
    
    # Also include persons created by current user (for drafts)
    if current_user.id:
        query = query.union(
            db.query(Person).filter(Person.created_by_user_id == current_user.id)
        )
    
    persons = query.all()
    
    result = []
    for person in persons:
        # Load employment for employee_code
        from app.models.employment import Employment
        employment = db.query(Employment).filter(Employment.person_id == person.id).first()
        
        # Load company
        company_name = None
        if employment and employment.company_id:
            from app.models.master_data import CompanyMaster
            company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
            company_name = company.name if company else None

        # Load latest rate plan (prefer latest by created_at)
        rate_plan = db.query(RatePlan).filter(
            RatePlan.person_id == person.id
        ).order_by(RatePlan.created_at.desc()).first()

        rate_value = None
        rate_label = None
        rate_display = None
        if rate_plan:
            # Convert Decimal to float for JSON
            try:
                rate_value = float(rate_plan.amount)
            except Exception:
                rate_value = None

            if rate_plan.plan_type == PlanType.MANDAY:
                rate_label = "Man-day"
                rate_display = f"{rate_value:.0f}/day" if rate_value is not None else None
            elif rate_plan.plan_type == PlanType.MANMONTH:
                rate_label = "Man-month"
                rate_display = f"{rate_value:.0f}/month" if rate_value is not None else None
            elif rate_plan.plan_type == PlanType.MONTHLY_SALARY:
                rate_label = "Monthly Salary"
                rate_display = f"{rate_value:.0f}/month" if rate_value is not None else None
            else:
                rate_label = rate_plan.plan_type.value if hasattr(rate_plan.plan_type, "value") else str(rate_plan.plan_type)
                rate_display = str(rate_value) if rate_value is not None else None
        
        response = PersonSummaryResponse.model_validate(person)
        response.employee_code = employment.employee_code if employment else None
        response.company_name = company_name
        response.rate_value = rate_value
        response.rate_label = rate_label
        response.rate_display = rate_display
        result.append(response)
    
    return result

@router.get("/persons/{person_id}/stage-a-docs", response_model=StageADocumentsListResponse)
async def get_stage_a_documents(
    person_id: UUID,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Stage-A documents for a person (CV Wallet).
    
    Returns ONLY documents where doc_category == STAGE_A.
    Includes can_download boolean based on permission and policy.
    """
    logger.info(f"[STAGE-A-DOCS] Fetch request: person_id={person_id}, user_id={current_user.id}, dept_id={current_user.dept_id}")
    
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    logger.info(f"[STAGE-A-DOCS] Person found: id={person.id}, status={person.status.value if person.status else None}, created_dept_id={person.created_dept_id if hasattr(person, 'created_dept_id') else None}")
    
    # Check permission to view Stage-A docs
    can_view_permission = user_has_permission(db, current_user, "DOC_VIEW_STAGEA")
    can_download_permission = user_has_permission(db, current_user, "DOC_DOWNLOAD_STAGEA")
    
    # Check if user is in owning department
    is_owning_dept = False
    if hasattr(person, 'created_dept_id') and person.created_dept_id and current_user.dept_id:
        is_owning_dept = person.created_dept_id == current_user.dept_id
    
    # Get policy for download when HR pending
    download_policy = db.query(Policy).filter(Policy.key == "download_policy_stagea_when_hr_pending").first()
    allow_download_when_hr_pending = False
    if download_policy and download_policy.value_json:
        allow_download_when_hr_pending = download_policy.value_json.get("value", False)
    
    # Query Stage-A documents
    # IMPORTANT: Fetch STRICTLY by doc_category == STAGE_A (not by stage or owner_dept)
    # This ensures HR-uploaded Stage-A docs are treated exactly like OPS-uploaded Stage-A docs
    # Stage-A docs uploaded by HR must appear in CV Wallet just like OPS uploads
    all_stage_a = db.query(Document).filter(
        Document.person_id == person_id,
        Document.doc_category == DocumentCategory.STAGE_A
    ).all()
    
    logger.info(f"[STAGE-A-DOCS] Found {len(all_stage_a)} documents with doc_category == STAGE_A (regardless of owner_dept or stage)")
    
    result = []
    for doc in all_stage_a:
        # Step-7: Use evaluate_document_access for detailed access information
        access_info = evaluate_document_access(db, current_user, person, doc)
        
        # Get doc_type_name from DocumentNameMaster if linked (not in current model, can be None)
        doc_type_name = None
        
        # Generate download URL
        download_url = f"/api/v1/cv-wallet/documents/{doc.id}/download"
        
        result.append(StageADocumentResponse(
            id=doc.id,
            filename=doc.doc_name,  # Primary field name per spec
            file_name=doc.doc_name,  # Keep for backward compatibility
            doc_type=doc_type_name,
            doc_type_name=doc_type_name,  # Keep for backward compatibility
            doc_category=doc.doc_category.value if doc.doc_category else None,
            doc_name=doc.doc_name,  # Can be same as file_name
            issue_date=None,  # Not in current model
            expiry_date=None,  # Not in current model
            uploaded_at=doc.created_at,
            download_url=download_url,
            file_key=doc.file_key,
            can_download=access_info["can_download"],
            download_block_reason=access_info["visibility_label"] if not access_info["can_download"] else None,  # Backward compatibility
            reason=access_info["reason"],
            grant_expires_at=access_info["grant_expires_at"],
            visibility_label=access_info["visibility_label"],
            owner_dept=doc.owner_dept.value if doc.owner_dept else None
        ))
    
    logger.info(f"[STAGE-A-DOCS] Returning {len(result)} Stage-A documents for person_id={person_id}")
    
    # Return in {items: [...]} format for frontend compatibility
    return {"items": result}

@router.get("/persons/{person_id}/documents", response_model=List[DocumentResponse])
async def get_person_documents(
    person_id: UUID,
    scope: str = Query("cv_wallet", description="Scope: cv_wallet returns all docs, frontend handles access UI"),
    include_locked: bool = Query(True, description="Include locked Finance/HR docs for UI display"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get documents for a person (with access grant checks).
    
    NOTE: This endpoint is for general document access (Finance/HR docs with grants).
    For CV Wallet Stage-A docs, use /cv-wallet/persons/{person_id}/stage-a-docs instead.
    """
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # FIXED: Get all documents EXCEPT Stage-A (Stage-A should use dedicated endpoint)
    # This endpoint is for Finance/HR documents with grant logic
    all_documents = db.query(Document).filter(
        Document.person_id == person_id,
        Document.doc_category != DocumentCategory.STAGE_A  # Exclude Stage-A docs
    ).all()
    
    # Map stage to owner_dept and visibility_scope for backward compatibility
    from app.models.document import DocumentVisibilityScope
    for doc in all_documents:
        if not doc.owner_dept and doc.stage:
            # Map stage to owner_dept
            if doc.stage == DocumentStage.FINANCE:
                doc.owner_dept = DocumentOwnerDept.FINANCE
                if not doc.doc_category:
                    doc.doc_category = DocumentCategory.FINANCE_KYC
                if not doc.visibility_scope:
                    doc.visibility_scope = DocumentVisibilityScope.PRIVATE
            elif doc.stage == DocumentStage.HR:
                doc.owner_dept = DocumentOwnerDept.HR
                if not doc.doc_category:
                    if "appointment" in doc.doc_name.lower():
                        doc.doc_category = DocumentCategory.APPOINTMENT
                    elif "declaration" in doc.doc_name.lower():
                        doc.doc_category = DocumentCategory.HR_SIGNED
                    else:
                        doc.doc_category = DocumentCategory.HR_SIGNED
                if not doc.visibility_scope:
                    doc.visibility_scope = DocumentVisibilityScope.PRIVATE
    
    # If include_locked is True, return all documents (frontend will show locked ones)
    # Otherwise, return only accessible documents using centralized access control
    if include_locked:
        # Return all documents - frontend will handle showing locked state
        return all_documents
    else:
        # Access Model: Use centralized access control function (for Finance/HR docs)
        accessible_docs = []
        for doc in all_documents:
            if can_user_view_document(db, current_user, person, doc):
                accessible_docs.append(doc)
        return accessible_docs

@router.get("/persons/{person_id}/finance-hr-docs")
async def get_finance_hr_documents(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Finance/HR documents for a person (for grant dialog).
    Returns documents grouped by category with access information.
    Only returns documents where owner_dept is FINANCE or HR.
    Step-7: Includes can_download, reason, grant_expires_at, visibility_label for each document.
    """
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Get all Finance/HR documents (exclude Stage-A)
    # Filter by owner_dept in (FINANCE, HR)
    all_documents = db.query(Document).filter(
        Document.person_id == person_id,
        Document.doc_category != DocumentCategory.STAGE_A,
        Document.owner_dept.in_([DocumentOwnerDept.FINANCE, DocumentOwnerDept.HR])
    ).all()
    
    # Step-7: Use evaluate_document_access for detailed access information
    # Group by category
    categories: dict = {}
    for doc in all_documents:
        category = doc.doc_category.value if doc.doc_category else "OTHER"
        if category not in categories:
            categories[category] = []
        
        # Evaluate access for this document
        access_info = evaluate_document_access(db, current_user, person, doc)
        
        categories[category].append({
            "id": doc.id,
            "doc_name": doc.doc_name,
            "doc_category": category,
            "owner_dept": doc.owner_dept.value if doc.owner_dept else None,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            # Step-7: Enhanced access information
            "can_download": access_info["can_download"],
            "reason": access_info["reason"],
            "grant_expires_at": access_info["grant_expires_at"],
            "visibility_label": access_info["visibility_label"]
        })
    
    return {
        "categories": categories,
        "total_count": len(all_documents)
    }

@router.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.DOC_STAGEA_DOWNLOAD))
):
    """
    Download a document from CV Wallet (unified endpoint).
    
    - Stage-A, Finance, and HR documents are all downloaded via this endpoint.
    - Actual access is enforced by centralized access control (enforce_can_download),
      which applies department ownership + AccessGrant rules.
    - Requires DOC_STAGEA_DOWNLOAD permission to use CV Wallet downloads.
    """
    # DIAGNOSTIC LOGGING: Log user, role, and permission status
    from app.models.role import Role
    from app.services.permission_checker import user_has_permission
    role = db.query(Role).filter(Role.id == current_user.role_id).first() if current_user.role_id else None
    has_permission = user_has_permission(db, current_user, PermissionCode.DOC_STAGEA_DOWNLOAD.value)
    
    logger.info(f"[CV-WALLET-DOWNLOAD] User: {current_user.id}, Role ID: {current_user.role_id}, Role: {role.name if role else 'None'}, Has DOC_STAGEA_DOWNLOAD: {has_permission}")
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    person = db.query(Person).filter(Person.id == document.person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # DIAGNOSTIC LOGGING: Log document properties
    logger.info(
        "[CV-WALLET-DOWNLOAD] Document: %s, doc_category: %s, stage: %s, owner_dept: %s, "
        "visibility_scope: %s, person_status: %s",
        document.id,
        document.doc_category.value if document.doc_category else None,
        document.stage.value if document.stage else None,
        document.owner_dept.value if document.owner_dept else None,
        document.visibility_scope.value if document.visibility_scope else None,
        person.status.value if person.status else None,
    )
    
    # Unified CV Wallet download: rely on centralized access control
    # This will raise HTTPException 403 if access denied (including GRANT_EXPIRED, NEED_GRANT, etc.)
    from app.services.document_access import enforce_can_download
    # NOTE: enforce_can_download returns (reason, grant_expires_at) on success
    download_reason, grant_expires_at = enforce_can_download(db, current_user, person, document, request)
    
    # FIXED: Use storage service (MinIO or local) to get file
    # storage_service is always available (falls back to local storage)
    
    # Check if file exists
    try:
        file_exists = storage_service.file_exists(document.file_key)
        if not file_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found on disk: {document.file_key}"
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check file existence: {str(e)}"
        )
    
    # Get file from storage service
    try:
        file_data = storage_service.get_file(document.file_key)
        
        # For audit metadata, derive simple Stage-A flag (not used for access control)
        is_stage_a = document.doc_category == DocumentCategory.STAGE_A
        
        # Audit log successful download
        log_audit_event(
            db=db,
            action_type="DOC_DOWNLOADED",
            entity_type="Document",
            entity_id=str(document.id),
            actor_user_id=current_user.id,
            action_metadata={
                "person_id": str(person.id),
                "doc_name": document.doc_name,
                "doc_category": document.doc_category.value if document.doc_category else None,
                "is_stage_a": is_stage_a,
                "person_status": person.status.value if person.status else None,
                "file_key": document.file_key,
                "file_exists": True
            },
            ip_address=get_client_ip(request) if request else None,
            user_agent=get_user_agent(request) if request else None
        )
        
        # FIXED: Use inline for PDF preview, attachment for download
        content_disposition = "inline" if document.mime_type == "application/pdf" else "attachment"
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=document.mime_type,
            headers={
                "Content-Disposition": f'{content_disposition}; filename="{document.doc_name}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )
