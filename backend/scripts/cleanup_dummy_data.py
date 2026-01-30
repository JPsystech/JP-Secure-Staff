"""
Cleanup script to remove all dummy/test data from the database.
This will delete all persons, documents, tickets, access grants, and audit logs,
but keep the essential structure (departments, roles, users, permissions, companies, policies, templates).

Usage:
    python scripts/cleanup_dummy_data.py          # Interactive mode (asks for confirmation)
    python scripts/cleanup_dummy_data.py --force  # Non-interactive mode (auto-confirms)
"""
import sys
import os
import argparse

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.person import Person
from app.models.document import Document
from app.models.employment import Employment
from app.models.finance_kyc import FinanceKYC
from app.models.rate_plan import RatePlan
from app.models.ticket import Ticket, TicketComment, TicketAttachment
from app.models.access_grant import AccessGrant
from app.models.audit_log import AuditLog

def cleanup_dummy_data(force=False):
    """
    Remove all dummy/test data from the database.
    This deletes:
    - All Persons (and related: documents, employment, finance_kyc, rate_plans)
    - All Documents
    - All Tickets (and related: ticket_comments, ticket_attachments)
    - All Access Grants
    - All Audit Logs
    
    Keeps:
    - Departments
    - Roles
    - Users
    - Permissions
    - Companies (master data)
    - Policies
    - Templates
    """
    db = SessionLocal()
    try:
        print("=" * 60)
        print("CLEANUP DUMMY DATA")
        print("=" * 60)
        print()
        
        # Count records before deletion
        person_count = db.query(Person).count()
        document_count = db.query(Document).count()
        employment_count = db.query(Employment).count()
        finance_kyc_count = db.query(FinanceKYC).count()
        rate_plan_count = db.query(RatePlan).count()
        ticket_count = db.query(Ticket).count()
        ticket_comment_count = db.query(TicketComment).count()
        ticket_attachment_count = db.query(TicketAttachment).count()
        access_grant_count = db.query(AccessGrant).count()
        audit_log_count = db.query(AuditLog).count()
        
        print("Current data counts:")
        print(f"  Persons: {person_count}")
        print(f"  Documents: {document_count}")
        print(f"  Employment records: {employment_count}")
        print(f"  Finance KYC records: {finance_kyc_count}")
        print(f"  Rate Plans: {rate_plan_count}")
        print(f"  Tickets: {ticket_count}")
        print(f"  Ticket Comments: {ticket_comment_count}")
        print(f"  Ticket Attachments: {ticket_attachment_count}")
        print(f"  Access Grants: {access_grant_count}")
        print(f"  Audit Logs: {audit_log_count}")
        print()
        
        # Confirm deletion (unless force flag is set)
        if not force:
            response = input("Are you sure you want to delete ALL this data? (yes/no): ")
            if response.lower() != "yes":
                print("Cleanup cancelled.")
                return
        else:
            print("Force mode: Auto-confirming deletion...")
        
        print()
        print("Starting cleanup...")
        print()
        
        # Delete in order (respecting foreign key constraints)
        
        # 1. Delete Ticket Attachments (references tickets)
        print("Deleting ticket attachments...")
        deleted = db.query(TicketAttachment).delete()
        print(f"  Deleted {deleted} ticket attachments")
        
        # 2. Delete Ticket Comments (references tickets)
        print("Deleting ticket comments...")
        deleted = db.query(TicketComment).delete()
        print(f"  Deleted {deleted} ticket comments")
        
        # 3. Delete Access Grants FIRST (references tickets and persons)
        print("Deleting access grants...")
        deleted = db.query(AccessGrant).delete()
        print(f"  Deleted {deleted} access grants")
        
        # 4. Delete Tickets (references persons, but access grants already deleted)
        print("Deleting tickets...")
        deleted = db.query(Ticket).delete()
        print(f"  Deleted {deleted} tickets")
        
        # 5. Delete Audit Logs (references persons, users, etc.)
        print("Deleting audit logs...")
        deleted = db.query(AuditLog).delete()
        print(f"  Deleted {deleted} audit logs")
        
        # 6. Delete Documents (references persons)
        print("Deleting documents...")
        deleted = db.query(Document).delete()
        print(f"  Deleted {deleted} documents")
        
        # 7. Delete Rate Plans (references persons)
        print("Deleting rate plans...")
        deleted = db.query(RatePlan).delete()
        print(f"  Deleted {deleted} rate plans")
        
        # 8. Delete Finance KYC (references persons)
        print("Deleting finance KYC records...")
        deleted = db.query(FinanceKYC).delete()
        print(f"  Deleted {deleted} finance KYC records")
        
        # 9. Delete Employment (references persons)
        print("Deleting employment records...")
        deleted = db.query(Employment).delete()
        print(f"  Deleted {deleted} employment records")
        
        # 10. Delete Persons (last, as it's referenced by others)
        print("Deleting persons...")
        deleted = db.query(Person).delete()
        print(f"  Deleted {deleted} persons")
        
        # Reset ticket counter if it exists
        print("Resetting ticket counter...")
        try:
            db.execute(text("UPDATE ticket_counter SET last_number = 0 WHERE id = 1"))
            print("  Ticket counter reset to 0")
        except Exception as e:
            print(f"  Note: Could not reset ticket counter (may not exist): {e}")
        
        # Commit all deletions
        db.commit()
        
        print()
        print("=" * 60)
        print("CLEANUP COMPLETE!")
        print("=" * 60)
        print()
        print("All dummy/test data has been removed.")
        print("The following data has been KEPT:")
        print("  - Departments")
        print("  - Roles")
        print("  - Users (admin@jpsecure.com, finance@jpsecure.com, etc.)")
        print("  - Permissions")
        print("  - Companies (master data)")
        print("  - Policies")
        print("  - Templates")
        print()
        print("You can now test from scratch!")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"\nERROR: Cleanup failed: {e}")
        print("All changes have been rolled back.")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup dummy/test data from the database")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt and delete immediately"
    )
    args = parser.parse_args()
    
    cleanup_dummy_data(force=args.force)
