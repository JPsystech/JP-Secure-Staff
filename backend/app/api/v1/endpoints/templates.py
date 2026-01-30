from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.models.template import Template, TemplateRevision, TemplateType, RevisionStatus
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateRevisionCreate, TemplateRevisionResponse
)
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.person import Person
from app.models.employment import Employment
from app.models.finance_kyc import FinanceKYC
from app.models.rate_plan import RatePlan
from app.models.master_data import CompanyMaster
from app.services.template_renderer import render_template
from app.services.document_data_builder import build_appointment_data, build_declaration_data

router = APIRouter()

@router.get("/", response_model=List[TemplateResponse])
async def get_templates(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all templates. Optional query: type=DECLARATION|APPOINTMENT_PERMANENT|... to filter by template type."""
    from sqlalchemy.orm import joinedload
    query = db.query(Template).options(joinedload(Template.revisions))
    if type:
        try:
            template_type = TemplateType(type.strip().upper()) if type.strip() else None
            if template_type:
                query = query.filter(Template.type == template_type)
        except ValueError:
            pass  # Invalid enum value: return all
    templates = query.all()
    return templates

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific template by ID"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template

@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new template (name optional). Only one active per type; new template starts inactive."""
    db_template = Template(type=template.type, name=template.name, is_active=False)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update template name (and optionally other fields)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    if body.name is not None:
        template.name = body.name
    db.commit()
    db.refresh(template)
    return template


@router.post("/{template_id}/activate", response_model=TemplateResponse)
async def activate_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set this template as active for its type. Deactivates all other templates of the same type."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    for t in db.query(Template).filter(Template.type == template.type).all():
        t.is_active = (t.id == template_id)
    db.commit()
    db.refresh(template)
    return template

@router.post("/{template_id}/revisions", response_model=TemplateRevisionResponse, status_code=status.HTTP_201_CREATED)
async def create_revision(
    template_id: int,
    revision: TemplateRevisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new template revision"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    db_revision = TemplateRevision(
        template_id=template_id,
        version=revision.version,
        content=revision.content,
        status=revision.status,
        created_by=current_user.id
    )
    db.add(db_revision)
    db.commit()
    db.refresh(db_revision)
    return db_revision

@router.post("/{template_id}/publish/{revision_id}", response_model=TemplateResponse)
async def publish_revision(
    template_id: int,
    revision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publish a template revision (set as active)"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    revision = db.query(TemplateRevision).filter(
        TemplateRevision.id == revision_id,
        TemplateRevision.template_id == template_id
    ).first()
    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision not found"
        )
    
    # Update revision status
    revision.status = RevisionStatus.PUBLISHED
    
    # Set as active revision
    template.active_revision_id = revision_id
    
    db.commit()
    db.refresh(template)
    return template

@router.post("/{template_id}/test-render")
async def test_render_template(
    template_id: int,
    person_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test render a template with sample or real person data"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Get active or latest published revision
    revision = None
    if template.active_revision_id:
        revision = db.query(TemplateRevision).filter(
            TemplateRevision.id == template.active_revision_id
        ).first()
    
    if not revision:
        revision = db.query(TemplateRevision).filter(
            TemplateRevision.template_id == template_id
        ).order_by(TemplateRevision.created_at.desc()).first()
    
    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No template revision found"
        )
    
    # Build data
    if person_id:
        # Use real person data
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        employment = db.query(Employment).filter(
            Employment.person_id == person_id,
            Employment.is_active == True
        ).first()
        
        if not employment:
            raise HTTPException(status_code=400, detail="Employment not found")
        
        finance_kyc = db.query(FinanceKYC).filter(FinanceKYC.person_id == person_id).first()
        company = None
        if employment.company_id:
            company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
        
        if template.type in [TemplateType.APPOINTMENT_PERMANENT, TemplateType.APPOINTMENT_FREELANCER, TemplateType.APPOINTMENT_CONTRACTUAL]:
            rate_plan = db.query(RatePlan).filter(RatePlan.person_id == person_id).order_by(RatePlan.created_at.desc()).first()
            if not rate_plan:
                raise HTTPException(status_code=400, detail="Rate plan not found")
            data = build_appointment_data(person, employment, finance_kyc, rate_plan, company, db)
        else:
            data = build_declaration_data(person, employment, finance_kyc, company, db)
    else:
        # Use sample data
        from datetime import date, datetime
        data = {
            "company": {
                "name": "Sample Company",
                "tagline": "Your Trusted Partner",
                "logoUrl": "",
                "hrEmail": "hr@sample.com",
                "hrPhones": "+91-1234567890",
                "website": "https://www.sample.com"
            },
            "letter": {
                "referenceNo": "REF-123456",
                "date": datetime.now().date().strftime("%d-%m-%Y"),
                "subject": "Appointment Letter - Sample Person",
                "employeeSignDate": datetime.now().date().strftime("%d-%m-%Y")
            },
            "job": {
                "title": "Software Engineer",
                "probationMonths": 3,
                "probationExtensionMonths": 3,
                "acceptanceDeadline": "7 days",
                "reportingAddress": "123 Main St, City",
                "reportingDate": datetime.now().date().strftime("%d-%m-%Y"),
                "initialPostingLocation": "Mumbai",
                "salaryDuringProbation": "50,000.00",
                "salaryAfterProbation": "60,000.00"
            },
            "policy": {
                "officeStartTime": "09:00 AM",
                "officeEndTime": "06:00 PM",
                "weeklyOff": "Sunday",
                "breakStart": "01:00 PM",
                "breakEnd": "02:00 PM",
                "postTerminationMonths": 6,
                "jurisdictionCity": "Mumbai",
                "jurisdictionState": "Maharashtra",
                "noticeDays": 30
            },
            "person": {
                "name": "Sample Person",
                "mobile": "+91-9876543210",
                "email": "sample@example.com",
                "dob": "01-01-1990",
                "location": "Mumbai",
                "stream": "MECH",
                "education": "DEGREE"
            }
        }
    
    # Render
    try:
        rendered_html = render_template(revision.content, data)
        return HTMLResponse(content=rendered_html)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template rendering failed: {str(e)}"
        )

