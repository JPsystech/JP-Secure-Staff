"""Access Grant Service"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from app.models.access_grant import AccessGrant, GrantScopeType
from app.models.document import Document, DocumentStage, DocumentOwnerDept, DocumentCategory
from app.models.person import Person

def create_access_grant(
    db: Session,
    ticket_id: Optional[UUID],
    person_id: UUID,
    granted_by_user_id: int,
    granted_to_user_id: int,
    granted_by_dept_id: int,
    scope_type: GrantScopeType,
    scope_value: str,  # documentId (UUID string) OR categoryKey (e.g., "HR_SIGNED_DOCS", "FINANCE_KYC_DOCS")
    expires_in_hours: int = 8
) -> AccessGrant:
    """
    Create an access grant for documents.
    Default expiry is 8 hours from now.
    
    Args:
        scope_value: For DOCUMENTS scope, this is a document UUID string.
                     For CATEGORY scope, this is a category key like "HR_SIGNED_DOCS", "FINANCE_KYC_DOCS".
    """
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    grant = AccessGrant(
        ticket_id=ticket_id,
        person_id=person_id,
        granted_by_user_id=granted_by_user_id,
        granted_by_dept_id=granted_by_dept_id,
        granted_to_user_id=granted_to_user_id,
        scope_type=scope_type,
        scope_value=scope_value,
        expires_at=expires_at
    )
    
    db.add(grant)
    db.commit()
    db.refresh(grant)
    
    return grant

def get_active_grants_for_user(
    db: Session,
    user_id: int,
    person_id: Optional[UUID] = None
) -> List[AccessGrant]:
    """
    Get all active (non-expired, non-revoked) grants for a user.
    Optionally filter by person_id.
    """
    now = datetime.utcnow()
    
    query = db.query(AccessGrant).filter(
        AccessGrant.granted_to_user_id == user_id,
        AccessGrant.expires_at > now,
        AccessGrant.revoked_at.is_(None)
    )
    
    if person_id:
        query = query.filter(AccessGrant.person_id == person_id)
    
    return query.all()

def check_document_access(
    db: Session,
    user_id: int,
    document: Document
) -> bool:
    """
    Check if user has access to a document.
    
    Rules:
    - Stage-A (OPERATION) docs are always accessible
    - Finance/HR docs: Users from owning department can always access their own docs
    - Finance/HR docs: Other users require active grant
    """
    # Stage-A documents are always accessible
    if document.owner_dept == DocumentOwnerDept.OPERATIONS and document.doc_category == DocumentCategory.STAGE_A:
        return True
    
    # Check if user belongs to the document's owning department
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.dept_id and document.owner_dept:
        # Get user's department
        from app.models.department import Department
        user_dept = db.query(Department).filter(Department.id == user.dept_id).first()
        if user_dept:
            # Map department name to DocumentOwnerDept enum
            dept_name_upper = user_dept.name.upper()
            if (dept_name_upper == 'FINANCE' and document.owner_dept == DocumentOwnerDept.FINANCE) or \
               (dept_name_upper == 'HR' and document.owner_dept == DocumentOwnerDept.HR) or \
               (dept_name_upper == 'OPERATIONS' and document.owner_dept == DocumentOwnerDept.OPERATIONS):
                # User belongs to the owning department - they can access their own docs
                return True
    
    # Check for active grants (for users from other departments)
    now = datetime.utcnow()
    grants = db.query(AccessGrant).filter(
        AccessGrant.granted_to_user_id == user_id,
        AccessGrant.person_id == document.person_id,
        AccessGrant.expires_at > now,
        AccessGrant.revoked_at.is_(None)
    ).all()
    
    for grant in grants:
        if grant.scope_type == GrantScopeType.DOCUMENTS:
            # scope_value is a document UUID string
            if grant.scope_value == str(document.id):
                return True
        elif grant.scope_type == GrantScopeType.CATEGORY:
            # scope_value is a category key like "HR_SIGNED_DOCS", "FINANCE_KYC_DOCS"
            if document.doc_category:
                doc_cat_str = document.doc_category.value if hasattr(document.doc_category, 'value') else str(document.doc_category)
                # Map category enum to scope_value format
                category_map = {
                    "HR_SIGNED": "HR_SIGNED_DOCS",
                    "FINANCE_KYC": "FINANCE_KYC_DOCS",
                    "APPOINTMENT": "APPOINTMENT",
                    "ID_CARD": "ID_CARD"
                }
                expected_scope = category_map.get(doc_cat_str, doc_cat_str)
                if grant.scope_value == expected_scope or grant.scope_value == doc_cat_str:
                    return True
    
    return False

def get_accessible_documents(
    db: Session,
    user_id: int,
    person_id: UUID
) -> List[Document]:
    """
    Get all documents accessible to a user for a person.
    """
    all_docs = db.query(Document).filter(Document.person_id == person_id).all()
    
    accessible = []
    for doc in all_docs:
        if check_document_access(db, user_id, doc):
            accessible.append(doc)
    
    return accessible

