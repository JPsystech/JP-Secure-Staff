"""Employee code generation service"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.employment import EmploymentType
from app.models.master_data import CompanyMaster

def generate_employee_code(
    db: Session,
    employment_type: EmploymentType,
    company_id: int
) -> str:
    """Generate unique employee code based on employment type and company"""
    company = db.query(CompanyMaster).filter(CompanyMaster.id == company_id).first()
    if not company:
        raise ValueError("Company not found")
    
    is_akshar = company.is_akshar
    
    if is_akshar:
        # Akshar company codes
        if employment_type == EmploymentType.PERMANENT:
            prefix = "ACP"
        elif employment_type == EmploymentType.FREELANCER:
            prefix = "ACF"
        elif employment_type == EmploymentType.CONTRACTUAL:
            prefix = "ACM"
        else:
            prefix = "ACX"
    else:
        # Other companies use short_code
        prefix = company.short_code
    
    # Get next sequence number for this prefix
    sequence_name = f"emp_code_{prefix.lower()}_seq"
    
    # Create sequence if it doesn't exist
    try:
        db.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {sequence_name}"))
        db.commit()
    except Exception:
        db.rollback()
        # Sequence might already exist, continue
    
    # Get next value from sequence
    result = db.execute(text(f"SELECT nextval('{sequence_name}')"))
    next_num = result.scalar()
    
    # Format: PREFIX-001, PREFIX-002, etc.
    return f"{prefix}-{next_num:03d}"

