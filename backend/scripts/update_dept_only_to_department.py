"""
Update DEPT_ONLY to DEPARTMENT in documents table.

Run this script AFTER running the migration that adds DEPARTMENT enum value.
This script can be run safely multiple times (idempotent).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.document import Document

def update_dept_only_to_department():
    """Update any DEPT_ONLY values to DEPARTMENT"""
    db = SessionLocal()
    try:
        # Check if any documents have DEPT_ONLY
        dept_only_docs = db.query(Document).filter(
            Document.visibility_scope == 'DEPT_ONLY'
        ).all()
        
        if not dept_only_docs:
            print("No documents with DEPT_ONLY found. Nothing to update.")
            return
        
        print(f"Found {len(dept_only_docs)} documents with DEPT_ONLY. Updating to DEPARTMENT...")
        
        # Update to DEPARTMENT
        from app.models.document import DocumentVisibilityScope
        updated_count = 0
        for doc in dept_only_docs:
            try:
                doc.visibility_scope = DocumentVisibilityScope.DEPARTMENT
                updated_count += 1
            except ValueError as e:
                print(f"Warning: Could not update document {doc.id}: {e}")
        
        db.commit()
        print(f"Successfully updated {updated_count} documents from DEPT_ONLY to DEPARTMENT.")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating documents: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_dept_only_to_department()
