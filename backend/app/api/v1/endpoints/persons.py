from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.person import Person, PersonStatus, IntakeDept
from app.models.document import Document, DocumentStage, DocumentCategory, DocumentOwnerDept, DocumentVisibilityScope
from app.schemas.person import PersonCreate, PersonResponse, PersonSummaryResponse, DuplicateResponse
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.duplicate_check import check_duplicate
from app.core.storage import storage_service
from app.core.normalize import normalize_uppercase_fields
from app.services.document_access import can_user_download_document, is_stage_a_document, get_active_grant_expiry
from datetime import date
from pydantic import BaseModel

router = APIRouter()

@router.get("/", response_model=List[PersonSummaryResponse])
async def get_persons(
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    status: Optional[PersonStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get persons with optional filters"""
    query = db.query(Person)
    
    if created_by is not None:
        query = query.filter(Person.created_by_user_id == created_by)
    
    if status:
        query = query.filter(Person.status == status)
    
    persons = query.order_by(Person.created_at.desc()).limit(limit).all()
    
    result = []
    for person in persons:
        from app.models.employment import Employment, EmploymentType
        from app.models.rate_plan import RatePlan, PlanType
        
        employment = db.query(Employment).filter(
            Employment.person_id == person.id,
            Employment.is_active == True
        ).first()
        
        employee_code = employment.employee_code if employment else None
        company_name = None
        employment_type = None
        if employment:
            if employment.company_id:
                from app.models.master_data import CompanyMaster
                company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
                company_name = company.name if company else None
            employment_type = employment.employment_type.value if employment.employment_type else None
        
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
        response.employee_code = employee_code
        response.company_name = company_name
        response.employment_type = employment_type
        response.rate_value = rate_value
        response.rate_label = rate_label
        response.rate_display = rate_display
        result.append(response)
    
    return result

@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    person: PersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new person with duplicate check"""
    # Check for duplicates
    duplicate = check_duplicate(
        db,
        mobile=person.mobile,
        email=person.email,
        name=person.name,
        dob=person.dob
    )
    
    if duplicate:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "message": "Duplicate person found",
                "existing_person_id": duplicate["existing_person_id"],
                "existing_employee_code": duplicate["existing_employee_code"]
            }
        )
    
    # Normalize ID-like fields (uppercase) for consistency
    person_dict = normalize_uppercase_fields(person.model_dump())

    # Access Model: Set created_dept_id and intake_dept when creating person
    intake_dept_value = None
    try:
        # Derive intake_dept from user's department name (if available)
        from app.models.department import Department
        if current_user.dept_id:
            dept = db.query(Department).filter(Department.id == current_user.dept_id).first()
            if dept and dept.name:
                dept_name = dept.name.upper()
                if "OPERATIONS" in dept_name or "OPERATION" in dept_name or dept_name == "OPS":
                    intake_dept_value = IntakeDept.OPERATION
                elif "HR" in dept_name or "HUMAN RESOURCES" in dept_name:
                    intake_dept_value = IntakeDept.HR
    except Exception:
        # If anything goes wrong, fall back to None for intake_dept
        intake_dept_value = None

    db_person = Person(
        **person_dict,
        status=PersonStatus.DRAFT,
        created_by_user_id=current_user.id,
        created_dept_id=current_user.dept_id,  # Track which dept created the person
        intake_dept=intake_dept_value
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person

@router.get("/{person_id}", response_model=PersonSummaryResponse)
async def get_person(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get person profile summary"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Get employee code, employment type, and rate plan if exists
    from app.models.employment import Employment, EmploymentType
    from app.models.rate_plan import RatePlan, PlanType
    
    employment = db.query(Employment).filter(
        Employment.person_id == person_id,
        Employment.is_active == True
    ).first()
    
    employee_code = employment.employee_code if employment else None
    company_name = None
    employment_type = None
    if employment:
        if employment.company_id:
            from app.models.master_data import CompanyMaster
            company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
            company_name = company.name if company else None
        employment_type = employment.employment_type.value if employment.employment_type else None
    
    # Load latest rate plan
    rate_plan = db.query(RatePlan).filter(
        RatePlan.person_id == person_id
    ).order_by(RatePlan.created_at.desc()).first()
    
    rate_value = None
    rate_label = None
    rate_display = None
    if rate_plan:
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
    response.employee_code = employee_code
    response.company_name = company_name
    response.employment_type = employment_type
    response.rate_value = rate_value
    response.rate_label = rate_label
    response.rate_display = rate_display
    return response

@router.get("/{person_id}/documents")
async def get_person_documents(
    person_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category: STAGE_A, FINANCE_KYC, HR_SIGNED, etc."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get documents for a person.
    
    FIXED: Returns {items: []} format, never crashes.
    Returns empty array on error or when no documents found.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[GET-DOCS] Getting documents for person_id={person_id}, category={category}")
        
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            logger.warning(f"[GET-DOCS] Person not found: {person_id}")
            return {"items": []}
        
        # Query documents
        query = db.query(Document).filter(Document.person_id == person_id)
        
        # Filter by category if provided
        if category:
            from app.models.document import DocumentCategory
            try:
                doc_category = DocumentCategory(category.upper())
                query = query.filter(Document.doc_category == doc_category)
            except ValueError:
                logger.warning(f"[GET-DOCS] Invalid category: {category}, ignoring filter")
        
        all_documents = query.all()
        logger.info(f"[GET-DOCS] Found {len(all_documents)} documents for person_id={person_id}")
        
        # Map stage to owner_dept and visibility_scope for backward compatibility
        from app.models.document import DocumentVisibilityScope, DocumentOwnerDept, DocumentCategory
        for doc in all_documents:
            if not doc.owner_dept and doc.stage:
                # Map stage to owner_dept
                if doc.stage == DocumentStage.OPERATION:
                    doc.owner_dept = DocumentOwnerDept.OPERATIONS
                    if not doc.doc_category:
                        doc.doc_category = DocumentCategory.STAGE_A
                    if not doc.visibility_scope:
                        doc.visibility_scope = DocumentVisibilityScope.PUBLIC_AFTER_FINANCE
                elif doc.stage == DocumentStage.FINANCE:
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
        
        # Return in {items: []} format for frontend compatibility
        logger.info(f"[GET-DOCS] Returning {len(all_documents)} documents")
        return {"items": all_documents}
        
    except HTTPException:
        # Re-raise HTTP exceptions (404, 403, etc.)
        raise
    except Exception as e:
        logger.error(f"[GET-DOCS] Error getting documents: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return empty array instead of crashing
        return {"items": []}

@router.post("/{person_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    person_id: UUID,
    file: UploadFile = File(...),
    # Frontend sends these fields
    stage: Optional[str] = Form(None),  # OPERATION, FINANCE, HR
    doc_name: Optional[str] = Form(None),  # Document name from frontend
    doc_category: Optional[str] = Form(None),  # Document category (STAGE_A, FINANCE_KYC, HR_SIGNED, etc.)
    is_mandatory: Optional[str] = Form(None),  # "true" or "false" as string
    # Optional fields for future use
    doc_type_id: Optional[int] = Form(None),  # Optional: document type ID
    doc_name_id: Optional[int] = Form(None),  # Optional: document name ID for dynamic certificates
    issue_date: Optional[str] = Form(None),  # Optional: issue date (YYYY-MM-DD)
    expiry_date: Optional[str] = Form(None),  # Optional: expiry date (YYYY-MM-DD)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document for a person (Stage-A documents).
    
    FIXED: Accepts multipart/form-data with optional fields.
    - file: required UploadFile
    - doc_type_id: optional (for future use with document_types table)
    - doc_name_id: optional (for dynamic certificates)
    - issue_date: optional (YYYY-MM-DD)
    - expiry_date: optional (YYYY-MM-DD)
    """
    import logging
    import traceback
    from datetime import datetime as dt
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Document upload started for person_id={person_id}, filename={file.filename}")
        
        # Validate person exists
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            logger.error(f"Person not found: {person_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        # Validate document_type if provided (for future use)
        doc_type_name = None
        if doc_type_id:
            from app.models.master_data import DocumentNameMaster
            doc_type = db.query(DocumentNameMaster).filter(DocumentNameMaster.id == doc_type_id).first()
            if doc_type:
                doc_type_name = doc_type.name
            # Note: We don't fail if doc_type_id doesn't exist - it's optional
        
        # Read file data
        file_data = await file.read()
        logger.info(f"File read: {len(file_data)} bytes")
        
        if len(file_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Generate file key (path in MinIO)
        import uuid
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_id = uuid.uuid4()
        file_key = f"persons/{person_id}/{unique_id}.{file_extension}"
        
        # Use frontend-provided values or defaults
        doc_name_value = doc_name or file.filename or "Document"
        mime_type_value = file.content_type or "application/octet-stream"
        size_bytes_value = len(file_data)
        is_mandatory_value = is_mandatory and is_mandatory.lower() == "true"
        
        # Determine stage from form data or default to OPERATION
        document_stage = DocumentStage.OPERATION
        if stage:
            try:
                document_stage = DocumentStage(stage.upper())
            except ValueError:
                logger.warning(f"Invalid stage: {stage}, using OPERATION")
        
        # ENFORCE UPLOAD PERMISSIONS: Department-based restrictions
        from app.models.document import DocumentOwnerDept, DocumentCategory, DocumentVisibilityScope
        from app.models.department import Department
        from app.models.role import Role
        
        # Get user's department
        user_dept = None
        if current_user.dept_id:
            user_dept = db.query(Department).filter(Department.id == current_user.dept_id).first()
        
        user_dept_name = user_dept.name.upper() if user_dept else None

        # Get user's role code (OPS_USER, HR_USER, FINANCE_USER, MASTER_ADMIN, etc.)
        user_role_code = None
        if current_user.role_id:
            role = db.query(Role).filter(Role.id == current_user.role_id).first()
            if role and role.code:
                user_role_code = role.code
        
        # Determine expected category and owner based on stage
        if document_stage == DocumentStage.OPERATION:
            # Stage-A intake documents (CV packet) - can be uploaded by Operations and HR
            expected_category = DocumentCategory.STAGE_A
            expected_owner = DocumentOwnerDept.OPERATIONS
            allowed_depts = ["OPERATIONS", "HR", "HUMAN RESOURCES"]
        elif document_stage == DocumentStage.FINANCE:
            expected_category = DocumentCategory.FINANCE_KYC
            expected_owner = DocumentOwnerDept.FINANCE
            allowed_depts = ["FINANCE"]
        elif document_stage == DocumentStage.HR:
            # HR can upload HR_SIGNED, APPOINTMENT, DECLARATION, ID_CARD
            # We'll check this after determining category
            expected_owner = DocumentOwnerDept.HR
            allowed_depts = ["HR", "HUMAN RESOURCES"]
        else:
            expected_category = DocumentCategory.STAGE_A
            expected_owner = DocumentOwnerDept.OPERATIONS
            allowed_depts = ["OPERATIONS"]
        
        # Check if user's department/role is allowed to upload this stage
        if document_stage == DocumentStage.OPERATION:
            # For Stage-A intake, allow by department OR by role (OPS_USER, HR_USER, MASTER_ADMIN)
            allowed_roles_for_stage_a = ["OPS_USER", "HR_USER", "MASTER_ADMIN"]
            if (user_dept_name not in allowed_depts) and (user_role_code not in allowed_roles_for_stage_a):
                logger.warning(f"Permission denied: User from {user_dept_name} with role {user_role_code} attempted to upload OPERATION document")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Users from {user_dept_name or 'unknown'} department cannot upload OPERATION documents. Only OPERATIONS, HR, HUMAN RESOURCES users can upload this type."
                )
        else:
            if user_dept_name not in allowed_depts:
                logger.warning(f"Permission denied: User from {user_dept_name} attempted to upload {document_stage.value} document")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Users from {user_dept_name or 'unknown'} department cannot upload {document_stage.value} documents. Only {', '.join(allowed_depts)} users can upload this type."
                )
        
        logger.info(f"Generated file_key: {file_key}, size: {size_bytes_value} bytes")
        
        # Save file to storage (MinIO or local filesystem fallback)
        # storage_service is always available (falls back to local storage)
        try:
            storage_service.upload_file(
                file_data,
                file_key,
                mime_type_value
            )
            logger.info(f"File uploaded to storage: {file_key} (storage type: {'MinIO' if hasattr(storage_service, 'client') and storage_service.client else 'Local'})")
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document to storage: {str(e)}"
            )
        
        # Verify file exists after upload
        if not storage_service.file_exists(file_key):
            logger.error(f"File upload verification failed: {file_key}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File upload failed: file not found after upload"
            )
        
        # Parse optional dates
        issue_date_parsed = None
        expiry_date_parsed = None
        if issue_date:
            try:
                issue_date_parsed = dt.strptime(issue_date, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Invalid issue_date format: {issue_date}")
        if expiry_date:
            try:
                expiry_date_parsed = dt.strptime(expiry_date, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Invalid expiry_date format: {expiry_date}")
        
        # Save document record to DB
        # (DocumentOwnerDept, DocumentCategory, DocumentVisibilityScope already imported above)
        
        # Determine category and owner based on stage (already validated permissions above)
        # NOTE: For Stage-A (OPERATION stage) we always force STAGE_A category to avoid misuse
        intended_doc_category = None
        if doc_category:
            try:
                intended_doc_category = DocumentCategory(doc_category.upper())
            except ValueError:
                logger.warning(f"Invalid doc_category: {doc_category}, will determine from stage")
        
        if document_stage == DocumentStage.OPERATION:
            # Stage-A intake: FORCE STAGE_A category regardless of incoming value
            # This ensures CV, Qualification Certificate, and other certificates uploaded during Stage-A intake
            # are always treated as Stage-A documents, regardless of who uploaded them (OPS or HR)
            doc_category = DocumentCategory.STAGE_A
            
            # Also check doc_name to catch any Stage-A documents that might have wrong stage
            # CV, Qualification Certificate, and Certificate documents should always be STAGE_A
            doc_name_lower = doc_name_value.lower() if doc_name_value else ""
            stage_a_doc_names = ["cv", "qualification", "certificate", "qualification certificate"]
            if any(name in doc_name_lower for name in stage_a_doc_names):
                doc_category = DocumentCategory.STAGE_A
                # If stage was not OPERATION but doc_name indicates Stage-A, log warning
                if document_stage != DocumentStage.OPERATION:
                    logger.warning(f"Document '{doc_name_value}' has stage {document_stage} but name indicates Stage-A. Forcing STAGE_A category.")
            
            # Set owner_dept based on who uploaded it (OPS or HR) for auditing purposes
            # IMPORTANT: owner_dept should NOT block access - Stage-A docs are accessible to all departments
            if user_dept_name and ("HR" in user_dept_name or "HUMAN RESOURCES" in user_dept_name):
                owner_dept = DocumentOwnerDept.HR
            else:
                owner_dept = DocumentOwnerDept.OPERATIONS
            
            # Stage-A documents must be viewable by ALL internal departments
            # Use PUBLIC_ALWAYS for Stage-A (or STAGE_A if we want to be explicit)
            visibility_scope = DocumentVisibilityScope.PUBLIC_ALWAYS
        elif document_stage == DocumentStage.FINANCE:
            doc_category = intended_doc_category or DocumentCategory.FINANCE_KYC
            owner_dept = DocumentOwnerDept.FINANCE
            visibility_scope = DocumentVisibilityScope.PRIVATE
        elif document_stage == DocumentStage.HR:
            # For HR, use provided doc_category or infer from doc_name
            if intended_doc_category:
                doc_category = intended_doc_category
            else:
                # Infer from doc_name if not provided
                doc_name_lower = doc_name_value.lower()
                if "appointment" in doc_name_lower:
                    doc_category = DocumentCategory.APPOINTMENT
                elif "declaration" in doc_name_lower:
                    doc_category = DocumentCategory.DECLARATION
                elif "id card" in doc_name_lower or "idcard" in doc_name_lower:
                    doc_category = DocumentCategory.ID_CARD
                else:
                    doc_category = DocumentCategory.HR_SIGNED
            
            # Validate HR category is allowed
            allowed_hr_categories = [DocumentCategory.APPOINTMENT, DocumentCategory.DECLARATION, 
                                   DocumentCategory.HR_SIGNED, DocumentCategory.ID_CARD, DocumentCategory.OTHER]
            if doc_category not in allowed_hr_categories:
                logger.warning(f"HR upload with invalid category: {doc_category}, defaulting to HR_SIGNED")
                doc_category = DocumentCategory.HR_SIGNED
            
            owner_dept = DocumentOwnerDept.HR
            visibility_scope = DocumentVisibilityScope.PRIVATE
        else:
            # Default to STAGE_A for unknown stages
            doc_category = DocumentCategory.STAGE_A
            owner_dept = DocumentOwnerDept.OPERATIONS
            visibility_scope = DocumentVisibilityScope.PUBLIC_AFTER_FINANCE
        
        # Get public URL for the file
        file_url = storage_service.get_public_url(file_key) if hasattr(storage_service, 'get_public_url') else f"/api/v1/files/{file_key}"
        
        db_document = Document(
            person_id=person_id,
            stage=document_stage,
            owner_dept=owner_dept,
            doc_category=doc_category,
            visibility_scope=visibility_scope,
            doc_name=doc_name_value,
            file_key=file_key,
            mime_type=mime_type_value,
            size_bytes=size_bytes_value,
            is_mandatory=is_mandatory_value,
            created_by_user_id=current_user.id
        )
        
        logger.info(f"[UPLOAD] Creating document record: person_id={person_id}, doc_name={doc_name_value}, doc_category={doc_category.value}, owner_dept={owner_dept.value}, file_key={file_key}")
        
        db.add(db_document)
        db.flush()  # Get doc_id without committing
        logger.info(f"[UPLOAD] Document record created in DB: id={db_document.id}, doc_category={db_document.doc_category}, owner_dept={db_document.owner_dept}, file_key={db_document.file_key}")
        
        # Commit transaction
        db.commit()
        db.refresh(db_document)
        
        # Verify the document was saved correctly
        verify_doc = db.query(Document).filter(Document.id == db_document.id).first()
        if verify_doc:
            logger.info(f"[UPLOAD] Verification: doc_id={verify_doc.id}, doc_category={verify_doc.doc_category}, owner_dept={verify_doc.owner_dept}, file_key={verify_doc.file_key}")
        else:
            logger.error(f"[UPLOAD] CRITICAL: Document {db_document.id} not found after commit!")
        
        logger.info(f"[UPLOAD] Document upload completed successfully: doc_id={db_document.id}, file_key={file_key}")
        
        # Audit log
        from app.services.audit_logger import log_audit_event
        log_audit_event(
            db=db,
            action_type="UPLOAD_DOC",
            entity_type="Document",
            entity_id=str(db_document.id),
            actor_user_id=current_user.id,
            action_metadata={
                "person_id": str(person_id),
                "doc_name": doc_name_value,
                "file_key": file_key,
                "file_size": size_bytes_value,
                "doc_type_id": doc_type_id,
                "doc_type_name": doc_type_name
            },
            ip_address=None,
            user_agent=None
        )
        
        return db_document
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in document upload: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.get("/{person_id}/documents/access-summary")
async def get_document_access_summary(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get document access summary for a person.
    
    Returns access information for Stage-A, Finance, and HR document buckets.
    Used by UI to show badges/indicators for document availability and grant status.
    
    Returns:
    {
        "stageA": {"available": true},
        "finance": {"available": boolean, "needsGrant": boolean, "grantExpiresAt": string|null},
        "hr": {"available": boolean, "needsGrant": boolean, "grantExpiresAt": string|null}
    }
    """
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Get all documents for this person
    all_documents = db.query(Document).filter(Document.person_id == person_id).all()
    
    # Stage-A documents: always available to all authenticated users
    stage_a_docs = [doc for doc in all_documents if is_stage_a_document(doc)]
    stage_a_available = len(stage_a_docs) > 0
    
    # Finance documents
    finance_docs = [
        doc for doc in all_documents
        if (doc.owner_dept == DocumentOwnerDept.FINANCE or
            doc.doc_category == DocumentCategory.FINANCE_KYC or
            doc.stage == DocumentStage.FINANCE)
        and not is_stage_a_document(doc)
    ]
    
    finance_available = False
    finance_needs_grant = False
    finance_grant_expires_at = None
    
    if finance_docs:
        # Check if user can download at least one Finance document
        for doc in finance_docs:
            allowed, _, grant_expires = can_user_download_document(db, current_user, person, doc)
            if allowed:
                finance_available = True
                if grant_expires:
                    finance_needs_grant = True
                    finance_grant_expires_at = grant_expires.isoformat() if grant_expires else None
                    break  # Use the first grant expiry found
            elif not finance_needs_grant:
                # If access denied and not via grant, user needs a grant
                finance_needs_grant = True
    
    # HR documents
    hr_docs = [
        doc for doc in all_documents
        if (doc.owner_dept == DocumentOwnerDept.HR or
            doc.doc_category in [DocumentCategory.APPOINTMENT, DocumentCategory.DECLARATION, DocumentCategory.HR_SIGNED] or
            doc.stage == DocumentStage.HR)
        and not is_stage_a_document(doc)
    ]
    
    hr_available = False
    hr_needs_grant = False
    hr_grant_expires_at = None
    
    if hr_docs:
        # Check if user can download at least one HR document
        for doc in hr_docs:
            allowed, _, grant_expires = can_user_download_document(db, current_user, person, doc)
            if allowed:
                hr_available = True
                if grant_expires:
                    hr_needs_grant = True
                    hr_grant_expires_at = grant_expires.isoformat() if grant_expires else None
                    break  # Use the first grant expiry found
            elif not hr_needs_grant:
                # If access denied and not via grant, user needs a grant
                hr_needs_grant = True
    
    return {
        "stageA": {
            "available": stage_a_available
        },
        "finance": {
            "available": finance_available,
            "needsGrant": finance_needs_grant,
            "grantExpiresAt": finance_grant_expires_at
        },
        "hr": {
            "available": hr_available,
            "needsGrant": hr_needs_grant,
            "grantExpiresAt": hr_grant_expires_at
        }
    }

@router.post("/{person_id}/submit-to-finance", response_model=PersonResponse)
async def submit_to_finance(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit person to finance.
    
    This endpoint can be called by:
    - Operation users (when creating Stage-A profile via Operation intake)
    - HR users (when creating Stage-A profile via HR intake)
    - Master Admin
    
    Transitions person status: DRAFT -> SUBMITTED_TO_FINANCE
    """
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    if person.status != PersonStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person must be in DRAFT status, current status: {person.status}"
        )
    
    # Access Model: Set status and finance_submitted_at
    # Both Operation and HR intake flows submit to Finance the same way
    from datetime import datetime
    person.status = PersonStatus.SUBMITTED_TO_FINANCE
    person.finance_submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(person)
    
    # Audit log: STATUS_CHANGE
    from app.services.audit_logger import log_audit_event
    from app.models.department import Department
    
    # Log which department submitted
    submitted_by_dept = None
    if current_user.dept_id:
        dept = db.query(Department).filter(Department.id == current_user.dept_id).first()
        if dept:
            submitted_by_dept = dept.name
    
    log_audit_event(
        db=db,
        action_type="STATUS_CHANGE",
        entity_type="Person",
        entity_id=str(person.id),
        actor_user_id=current_user.id,
        action_metadata={
            "old_status": "DRAFT",
            "new_status": "SUBMITTED_TO_FINANCE",
            "finance_submitted_at": person.finance_submitted_at.isoformat() if person.finance_submitted_at else None,
            "submitted_by_dept": submitted_by_dept,
            "intake_dept": person.intake_dept.value if hasattr(person, 'intake_dept') and person.intake_dept else None
        },
        ip_address=None,
        user_agent=None
    )
    
    return person
