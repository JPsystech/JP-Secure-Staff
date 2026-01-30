"""
One-time backfill: normalize existing database records to UPPERCASE to match new validation rules.

Tables & columns normalized:
  - Person (persons): name
  - Employment (employments): employee_code
  - FinanceKYC (finance_kyc): aadhaar, pan, bank_name, ifsc

Safe to re-run: only updates rows where value is a string and value != value.upper().
Uses a single transaction; rolls back on any error.

Usage (from project root):
  python backend/scripts/normalize_uppercase_existing_data.py

Usage (from backend dir):
  python scripts/normalize_uppercase_existing_data.py
"""
import sys
import os

# Add backend root to path so "app" is importable
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.person import Person
from app.models.employment import Employment
from app.models.finance_kyc import FinanceKYC


def _needs_upper(val: str | None) -> bool:
    """True if value is a non-empty string and not already uppercase."""
    if val is None or not isinstance(val, str):
        return False
    s = val.strip()
    return len(s) > 0 and s != s.upper()


def normalize_person_name(db: Session) -> int:
    """Normalize Person.name to uppercase. Returns number of rows updated."""
    updated = 0
    for row in db.query(Person).all():
        if _needs_upper(row.name):
            row.name = row.name.strip().upper()
            updated += 1
    return updated


def normalize_employment_employee_code(db: Session) -> int:
    """Normalize Employment.employee_code to uppercase. Returns number of rows updated."""
    updated = 0
    for row in db.query(Employment).all():
        if _needs_upper(row.employee_code):
            row.employee_code = row.employee_code.strip().upper()
            updated += 1
    return updated


def normalize_finance_kyc(db: Session) -> int:
    """Normalize FinanceKYC aadhaar, pan, bank_name, ifsc to uppercase. Returns total rows updated (counted once per row that had at least one change)."""
    updated = 0
    for row in db.query(FinanceKYC).all():
        changed = False
        if _needs_upper(row.aadhaar):
            row.aadhaar = row.aadhaar.strip().upper()
            changed = True
        if _needs_upper(row.pan):
            row.pan = row.pan.strip().upper()
            changed = True
        if _needs_upper(row.bank_name):
            row.bank_name = row.bank_name.strip().upper()
            changed = True
        if _needs_upper(row.ifsc):
            row.ifsc = row.ifsc.strip().upper()
            changed = True
        if changed:
            updated += 1
    return updated


def main() -> None:
    db = SessionLocal()
    try:
        print("=" * 60)
        print("NORMALIZE UPPERCASE EXISTING DATA (one-time backfill)")
        print("=" * 60)

        # Counts before
        person_count = db.query(Person).count()
        employment_count = db.query(Employment).count()
        finance_kyc_count = db.query(FinanceKYC).count()
        print(f"\nBefore: Person rows={person_count}, Employment rows={employment_count}, FinanceKYC rows={finance_kyc_count}")

        u1 = normalize_person_name(db)
        u2 = normalize_employment_employee_code(db)
        u3 = normalize_finance_kyc(db)

        db.commit()
        print("\nCommitted transaction.")

        print("\n--- Records updated per table ---")
        print(f"  Person (name):           {u1}")
        print(f"  Employment (employee_code): {u2}")
        print(f"  FinanceKYC (aadhaar/pan/bank_name/ifsc): {u3}")
        print(f"  Total rows touched:      {u1 + u2 + u3}")
        print("\nDone. CV Wallet, Admin Persons, and Dashboard will show uppercase values.")
    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
