"""Build data object for document templates from Person and related models"""
from typing import Dict, Any
from datetime import datetime, date
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.person import Person
from app.models.employment import Employment, EmploymentType
from app.models.finance_kyc import FinanceKYC
from app.models.rate_plan import RatePlan
from app.models.master_data import CompanyMaster
from app.models.policy import Policy
import json

def build_appointment_data(
    person: Person,
    employment: Employment,
    finance_kyc: FinanceKYC,
    rate_plan: RatePlan,
    company: CompanyMaster,
    db: Session
) -> Dict[str, Any]:
    """
    Build data object for appointment letter template.
    
    Returns dictionary with keys: company, letter, job, policy, person
    """
    # Get company details from Policy or use defaults
    company_policy = db.query(Policy).filter(Policy.key == "company_details").first()
    company_details = {}
    if company_policy:
        company_details = company_policy.value_json
    
    # Get policy details
    policy_data = db.query(Policy).filter(Policy.key == "appointment_policy").first()
    policy_details = {}
    if policy_data:
        policy_details = policy_data.value_json
    
    # Format dates
    today = datetime.now().date()
    letter_date = today.strftime("%d-%m-%Y")
    employee_sign_date = today.strftime("%d-%m-%Y")
    
    # Reference number (using employee code or person ID)
    reference_no = employment.employee_code or f"REF-{person.id.hex[:8].upper()}"
    
    # Build job details based on employment type
    job_title = "Employee"  # Default, can be enhanced
    probation_months = policy_details.get("probationMonths", 3)
    probation_extension_months = policy_details.get("probationExtensionMonths", 3)
    acceptance_deadline = policy_details.get("acceptanceDeadline", "7 days")
    reporting_address = policy_details.get("reportingAddress", "As per company policy")
    reporting_date = rate_plan.valid_from.strftime("%d-%m-%Y") if rate_plan and rate_plan.valid_from else today.strftime("%d-%m-%Y")
    initial_posting_location = person.location or "As per company policy"
    
    # Salary details
    salary_during_probation = f"{rate_plan.amount:,.2f}" if rate_plan else "0.00"
    salary_after_probation = salary_during_probation  # Can be enhanced
    
    # Office timings
    office_start_time = policy_details.get("officeStartTime", "09:00 AM")
    office_end_time = policy_details.get("officeEndTime", "06:00 PM")
    weekly_off = policy_details.get("weeklyOff", "Sunday")
    break_start = policy_details.get("breakStart", "01:00 PM")
    break_end = policy_details.get("breakEnd", "02:00 PM")
    
    # Other policy details
    post_termination_months = policy_details.get("postTerminationMonths", 6)
    jurisdiction_city = policy_details.get("jurisdictionCity", "Mumbai")
    jurisdiction_state = policy_details.get("jurisdictionState", "Maharashtra")
    notice_days = policy_details.get("noticeDays", 30)
    
    # Company details
    company_name = company.name if company else company_details.get("name", "Company Name")
    company_tagline = company_details.get("tagline", "")
    company_logo_url = company_details.get("logoUrl", "")
    company_hr_email = company_details.get("hrEmail", "hr@company.com")
    company_hr_phones = company_details.get("hrPhones", "+91-XXXXXXXXXX")
    company_website = company_details.get("website", "https://www.company.com")
    
    data = {
        "company": {
            "name": company_name,
            "tagline": company_tagline,
            "logoUrl": company_logo_url,
            "hrEmail": company_hr_email,
            "hrPhones": company_hr_phones,
            "website": company_website
        },
        "letter": {
            "referenceNo": reference_no,
            "date": letter_date,
            "subject": f"Appointment Letter - {person.name}",
            "employeeSignDate": employee_sign_date
        },
        "job": {
            "title": job_title,
            "probationMonths": probation_months,
            "probationExtensionMonths": probation_extension_months,
            "acceptanceDeadline": acceptance_deadline,
            "reportingAddress": reporting_address,
            "reportingDate": reporting_date,
            "initialPostingLocation": initial_posting_location,
            "salaryDuringProbation": salary_during_probation,
            "salaryAfterProbation": salary_after_probation
        },
        "policy": {
            "officeStartTime": office_start_time,
            "officeEndTime": office_end_time,
            "weeklyOff": weekly_off,
            "breakStart": break_start,
            "breakEnd": break_end,
            "postTerminationMonths": post_termination_months,
            "jurisdictionCity": jurisdiction_city,
            "jurisdictionState": jurisdiction_state,
            "noticeDays": notice_days
        },
        "person": {
            "name": person.name,
            "mobile": person.mobile,
            "email": person.email or "",
            "dob": person.dob.strftime("%d-%m-%Y") if person.dob else "",
            "location": person.location or "",
            "stream": person.stream.value if person.stream else "",
            "education": person.education.value if person.education else ""
        }
    }
    
    return data

def build_declaration_data(
    person: Person,
    employment: Employment,
    finance_kyc: FinanceKYC,
    company: CompanyMaster,
    db: Session
) -> Dict[str, Any]:
    """
    Build data object for declaration template (ACS format).
    Includes PERSON_NAME, PERSON_NAME_UPPER, EMP_CODE, TODAY_DATE_DDMMYYYY, ACS_WITNESS_NAME.
    """
    company_policy = db.query(Policy).filter(Policy.key == "company_details").first()
    company_details = {}
    if company_policy and company_policy.value_json and isinstance(company_policy.value_json, dict):
        company_details = company_policy.value_json
    witness_policy = db.query(Policy).filter(Policy.key == "declaration_witness_name").first()
    acs_witness_name = "MR. KRUNAL SHAH"
    if witness_policy and witness_policy.value_json:
        if isinstance(witness_policy.value_json, dict) and witness_policy.value_json.get("name"):
            acs_witness_name = witness_policy.value_json["name"]
        elif isinstance(witness_policy.value_json, str):
            acs_witness_name = witness_policy.value_json

    today = datetime.now().date()
    declaration_date = today.strftime("%d-%m-%Y")
    emp_code = employment.employee_code if employment else None
    ref_no = emp_code or f"REF-{person.id.hex[:8].upper()}"
    company_name = company.name if company else company_details.get("name", "Akshar Consultancy Service (ACS)")

    data = {
        "company": {
            "name": company_name,
            "tagline": company_details.get("tagline", ""),
            "logoUrl": company_details.get("logoUrl", ""),
            "hrEmail": company_details.get("hrEmail", "hr@company.com"),
            "website": company_details.get("website", "https://www.aksharconsultancy.in")
        },
        "letter": {
            "date": declaration_date,
            "referenceNo": ref_no,
            "todayDateDDMMYYYY": declaration_date,
            "acsWitnessName": acs_witness_name,
        },
        "person": {
            "name": person.name,
            "name_upper": (person.name or "").upper(),
            "mobile": person.mobile or "",
            "email": person.email or "",
            "dob": person.dob.strftime("%d-%m-%Y") if person.dob else "",
            "aadhaar": finance_kyc.aadhaar if finance_kyc and finance_kyc.aadhaar else "",
            "pan": finance_kyc.pan if finance_kyc and finance_kyc.pan else "",
            "emp_code": emp_code or ref_no,
        }
    }
    return data

