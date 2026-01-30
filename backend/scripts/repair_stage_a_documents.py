"""
Repair script to fix Stage-A documents with wrong category.

This script:
1. Finds documents with doc_name in [CV, Qualification Certificate, Certificate] 
   that were created during intake (stage == OPERATION)
2. If doc_category is null or wrong, sets it to STAGE_A
3. Ensures HR-uploaded Stage-A docs are treated exactly like OPS-uploaded Stage-A docs
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.document import Document, DocumentCategory, DocumentStage, DocumentOwnerDept, DocumentVisibilityScope
from app.models.person import Person, PersonStatus

def repair_stage_a_documents():
    """Repair Stage-A documents with wrong or missing category"""
    db: Session = SessionLocal()
    
    try:
        # Find documents that should be Stage-A but have wrong category
        # Criteria:
        # 1. doc_name contains CV, Qualification, or Certificate
        # 2. stage == OPERATION (intake stage)
        # 3. doc_category is null or not STAGE_A
        
        stage_a_doc_names = ["cv", "qualification", "certificate"]
        
        # Get all OPERATION stage documents
        operation_docs = db.query(Document).filter(
            Document.stage == DocumentStage.OPERATION
        ).all()
        
        print(f"Found {len(operation_docs)} documents with OPERATION stage")
        
        repaired_count = 0
        for doc in operation_docs:
            doc_name_lower = doc.doc_name.lower() if doc.doc_name else ""
            
            # Check if doc_name indicates Stage-A document
            is_stage_a_doc = any(name in doc_name_lower for name in stage_a_doc_names)
            
            # Check if category needs fixing
            needs_repair = False
            if is_stage_a_doc:
                if doc.doc_category is None:
                    needs_repair = True
                    reason = "missing category"
                elif doc.doc_category != DocumentCategory.STAGE_A:
                    needs_repair = True
                    reason = f"wrong category ({doc.doc_category.value})"
            
            if needs_repair:
                old_category = doc.doc_category.value if doc.doc_category else "None"
                doc.doc_category = DocumentCategory.STAGE_A
                doc.visibility_scope = DocumentVisibilityScope.PUBLIC_ALWAYS
                
                # Keep owner_dept as is (HR or OPERATIONS) for auditing
                # But ensure it's set if missing
                if not doc.owner_dept:
                    # Try to infer from creator's department
                    from app.models.user import User
                    creator = db.query(User).filter(User.id == doc.created_by_user_id).first()
                    if creator and creator.dept_id:
                        from app.models.department import Department
                        dept = db.query(Department).filter(Department.id == creator.dept_id).first()
                        if dept:
                            dept_name_upper = dept.name.upper()
                            if "HR" in dept_name_upper or "HUMAN RESOURCES" in dept_name_upper:
                                doc.owner_dept = DocumentOwnerDept.HR
                            elif "FINANCE" in dept_name_upper:
                                doc.owner_dept = DocumentOwnerDept.FINANCE
                            else:
                                doc.owner_dept = DocumentOwnerDept.OPERATIONS
                        else:
                            doc.owner_dept = DocumentOwnerDept.OPERATIONS
                    else:
                        doc.owner_dept = DocumentOwnerDept.OPERATIONS
                
                db.add(doc)
                repaired_count += 1
                print(f"  ✓ Repaired doc_id={doc.id}, doc_name='{doc.doc_name}': {old_category} → STAGE_A ({reason})")
        
        if repaired_count > 0:
            db.commit()
            print(f"\n✅ Successfully repaired {repaired_count} Stage-A documents")
        else:
            print("\n✅ No documents needed repair")
        
        # Also check for documents with STAGE_A category but wrong stage
        # (shouldn't happen, but let's be thorough)
        stage_a_docs = db.query(Document).filter(
            Document.doc_category == DocumentCategory.STAGE_A
        ).all()
        
        wrong_stage_count = 0
        for doc in stage_a_docs:
            if doc.stage != DocumentStage.OPERATION:
                # Stage-A docs should have OPERATION stage
                # But we don't change stage here as it might be intentional
                # Just log for awareness
                wrong_stage_count += 1
                print(f"  ⚠ Doc_id={doc.id} has STAGE_A category but stage={doc.stage.value} (expected OPERATION)")
        
        if wrong_stage_count > 0:
            print(f"\n⚠ Found {wrong_stage_count} documents with STAGE_A category but non-OPERATION stage")
            print("   (These are left as-is; stage may be intentional)")
        
        # Summary
        total_stage_a = len(stage_a_docs)
        print(f"\n📊 Summary:")
        print(f"   Total Stage-A documents (doc_category == STAGE_A): {total_stage_a}")
        print(f"   Repaired documents: {repaired_count}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    from app.models.document import DocumentVisibilityScope
    exit(repair_stage_a_documents())
