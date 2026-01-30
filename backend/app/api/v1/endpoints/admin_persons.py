"""
Admin Person Viewer (Step-14): read-only list/detail/documents for Master Admin.
All persons across departments; no created_dept_id restriction.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.dependencies.permissions import require_permission
from app.models.user import User
from app.models.person import Person, PersonStatus
from app.models.document import Document, DocumentStage, DocumentCategory, DocumentOwnerDept, DocumentVisibilityScope
from app.models.department import Department
from app.models.employment import Employment
from app.models.rate_plan import RatePlan
from app.core.permissions import PermissionCode

router = APIRouter()


@router.get("/", response_model=List[dict])
async def admin_list_persons(
    search: Optional[str] = Query(None, description="Search by name, email, or employee code"),
    dept_id: Optional[int] = Query(None, description="Filter by created_dept_id"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.ADMIN_PERSON_VIEW_ALL)),
):
    """
    List all persons (global; ignores created_dept_id restriction).
    Supports search (name/email/emp_code) and optional dept_id filter.
    """
    query = db.query(Person)
    if dept_id is not None:
        query = query.filter(Person.created_dept_id == dept_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        emp_person_ids = [
            r[0] for r in db.query(Employment.person_id).filter(
                Employment.is_active == True,
                Employment.employee_code.ilike(term),
            ).distinct().all()
        ]
        conditions = [Person.name.ilike(term), Person.email.ilike(term)]
        if emp_person_ids:
            conditions.append(Person.id.in_(emp_person_ids))
        query = query.filter(or_(*conditions))
    query = query.order_by(Person.created_at.desc())
    persons = query.offset(skip).limit(limit).all()

    result = []
    for person in persons:
        employment = (
            db.query(Employment)
            .filter(Employment.person_id == person.id, Employment.is_active == True)
            .first()
        )
        dept = None
        if person.created_dept_id:
            dept = db.query(Department).filter(Department.id == person.created_dept_id).first()
        result.append({
            "id": str(person.id),
            "name": person.name,
            "email": person.email or None,
            "employee_code": employment.employee_code if employment else None,
            "department_id": person.created_dept_id,
            "department_name": dept.name if dept else None,
            "status": person.status.value if person.status else None,
            "created_at": person.created_at.isoformat() if person.created_at else None,
        })
    return result


@router.get("/{person_id}", response_model=dict)
async def admin_get_person(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.ADMIN_PERSON_VIEW_ALL)),
):
    """Get person detail (same shape as normal person detail; read-only)."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    employment = (
        db.query(Employment)
        .filter(Employment.person_id == person_id, Employment.is_active == True)
        .first()
    )
    employee_code = employment.employee_code if employment else None
    company_name = None
    employment_type = None
    if employment:
        if employment.company_id:
            from app.models.master_data import CompanyMaster
            company = db.query(CompanyMaster).filter(CompanyMaster.id == employment.company_id).first()
            company_name = company.name if company else None
        employment_type = employment.employment_type.value if employment.employment_type else None

    rate_plan = (
        db.query(RatePlan)
        .filter(RatePlan.person_id == person_id)
        .order_by(RatePlan.created_at.desc())
        .first()
    )
    rate_value = None
    rate_label = None
    rate_display = None
    if rate_plan:
        try:
            rate_value = float(rate_plan.amount)
        except Exception:
            rate_value = None
        from app.models.rate_plan import PlanType
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
            rate_label = getattr(rate_plan.plan_type, "value", str(rate_plan.plan_type))
            rate_display = str(rate_value) if rate_value is not None else None

    dept = None
    if person.created_dept_id:
        dept = db.query(Department).filter(Department.id == person.created_dept_id).first()

    return {
        "id": str(person.id),
        "name": person.name,
        "mobile": person.mobile,
        "alt_mobile": person.alt_mobile,
        "email": person.email,
        "dob": person.dob.isoformat() if person.dob else None,
        "stream": person.stream.value if person.stream else None,
        "stream_other": person.stream_other,
        "education": person.education.value if person.education else None,
        "education_other": person.education_other,
        "location": person.location,
        "status": person.status.value if person.status else None,
        "created_by_user_id": person.created_by_user_id,
        "created_at": person.created_at.isoformat() if person.created_at else None,
        "updated_at": person.updated_at.isoformat() if person.updated_at else None,
        "intake_dept": person.intake_dept.value if person.intake_dept else None,
        "employee_code": employee_code,
        "company_name": company_name,
        "employment_type": employment_type,
        "rate_value": rate_value,
        "rate_label": rate_label,
        "rate_display": rate_display,
        "department_id": person.created_dept_id,
        "department_name": dept.name if dept else None,
    }


@router.get("/{person_id}/documents", response_model=dict)
async def admin_get_person_documents(
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.ADMIN_PERSON_VIEW_ALL)),
):
    """Return ALL documents for the person (Stage-A + HR + Finance + any category)."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    docs = db.query(Document).filter(Document.person_id == person_id).order_by(Document.created_at.desc()).all()
    items = []
    for doc in docs:
        owner_dept = doc.owner_dept.value if doc.owner_dept else (doc.stage.value if doc.stage else None)
        doc_category = doc.doc_category.value if doc.doc_category else None
        items.append({
            "id": doc.id,
            "filename": doc.doc_name,
            "doc_name": doc.doc_name,
            "doc_type": doc_category,
            "doc_category": doc_category,
            "stage": doc.stage.value if doc.stage else None,
            "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
            "uploaded_by_dept": owner_dept,
            "expires_at": None,
            "status": "available",
            "mime_type": doc.mime_type,
            "size_bytes": doc.size_bytes,
        })
    return {"items": items}
