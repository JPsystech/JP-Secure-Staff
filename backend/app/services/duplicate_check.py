"""Duplicate person detection service"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.person import Person
from app.models.employment import Employment
from typing import Optional, Dict, Any
from datetime import date

def check_duplicate(
    db: Session,
    mobile: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
    dob: Optional[date] = None
) -> Optional[Dict[str, Any]]:
    """
    Check for duplicate person by:
    1. Mobile number (exact match)
    2. Email (exact match, if provided)
    3. Name + DOB (exact match, if both provided)
    
    Returns dict with existing_person_id and existing_employee_code if duplicate found
    """
    # Check by mobile
    person = db.query(Person).filter(Person.mobile == mobile).first()
    if person:
        employee_code = _get_employee_code(db, person.id)
        return {
            "existing_person_id": str(person.id),
            "existing_employee_code": employee_code
        }
    
    # Check by email (if provided)
    if email:
        person = db.query(Person).filter(Person.email == email).first()
        if person:
            employee_code = _get_employee_code(db, person.id)
            return {
                "existing_person_id": str(person.id),
                "existing_employee_code": employee_code
            }
    
    # Check by name + DOB (if both provided)
    if name and dob:
        person = db.query(Person).filter(
            and_(Person.name == name, Person.dob == dob)
        ).first()
        if person:
            employee_code = _get_employee_code(db, person.id)
            return {
                "existing_person_id": str(person.id),
                "existing_employee_code": employee_code
            }
    
    return None

def _get_employee_code(db: Session, person_id) -> Optional[str]:
    """Get the employee code for a person"""
    employment = db.query(Employment).filter(
        Employment.person_id == person_id,
        Employment.is_active == True
    ).first()
    return employment.employee_code if employment else None

