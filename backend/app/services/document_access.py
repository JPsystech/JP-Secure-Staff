"""
Centralized Document Access Control Service
Implements RBAC + ABAC for document visibility and downloads
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from enum import Enum
from app.models.user import User
from app.models.person import Person, PersonStatus
from app.models.document import Document, DocumentStage, DocumentOwnerDept, DocumentVisibilityScope, DocumentCategory
from app.models.access_grant import AccessGrant, GrantScopeType
from app.models.role import Role


class AccessReason(str, Enum):
    """Reason codes for document access decisions"""
    STAGE_A_PUBLIC = "STAGE_A_PUBLIC"  # Stage-A document, publicly accessible
    OWNER_DEPT = "OWNER_DEPT"  # User's dept matches document owner dept
    ADMIN = "ADMIN"  # Master Admin access
    GRANTED = "GRANTED"  # Access via active grant
    NEEDS_GRANT = "NEEDS_GRANT"  # Access requires grant (Finance/HR docs for other depts)
    EXPIRED = "EXPIRED"  # Grant expired
    FORBIDDEN = "FORBIDDEN"  # Access denied


def is_master_admin(user: User, db: Session) -> bool:
    """Check if user is Master Admin"""
    if not user.role_id:
        return False
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return role and role.code == "MASTER_ADMIN"


def is_stage_a_document(document: Document) -> bool:
    """
    Helper function to check if a document is a Stage-A document.
    Stage-A documents are always downloadable by ALL departments.
    
    Checks:
    - doc_category == STAGE_A
    - stage == OPERATION (Stage-A)
    - visibility_scope == STAGE_A or PUBLIC_ALWAYS
    """
    # Primary check: doc_category == STAGE_A
    if document.doc_category == DocumentCategory.STAGE_A:
        return True
    
    # Check stage == OPERATION (Stage-A)
    if document.stage == DocumentStage.OPERATION:
        return True
    
    # Check visibility_scope = STAGE_A or PUBLIC_ALWAYS (used for Stage-A)
    if document.visibility_scope in [DocumentVisibilityScope.STAGE_A, DocumentVisibilityScope.PUBLIC_ALWAYS]:
        return True
    
    return False


def is_owner_dept(user: User, document: Document, db: Session) -> bool:
    """
    Helper function to check if user's department matches document's owner_dept.
    HR can download HR docs, Finance can download Finance docs, etc.
    """
    if not user.dept_id or not document.owner_dept:
        return False
    
    from app.models.department import Department
    user_dept = db.query(Department).filter(Department.id == user.dept_id).first()
    if not user_dept:
        return False
    
    # Normalize department names for comparison
    user_dept_name = str(user_dept.name if hasattr(user_dept, 'name') else user_dept).upper()
    doc_dept_value = str(document.owner_dept.value if hasattr(document.owner_dept, 'value') else document.owner_dept).upper()
    
    # Direct enum value match
    if doc_dept_value == "HR" and ("HR" in user_dept_name or "HUMAN RESOURCES" in user_dept_name):
        return True
    if doc_dept_value == "FINANCE" and "FINANCE" in user_dept_name:
        return True
    if doc_dept_value == "OPERATIONS" and ("OPERATIONS" in user_dept_name or "OPS" in user_dept_name or "OPERATION" in user_dept_name):
        return True
    
    return False


def has_valid_grant(db: Session, user: User, person: Person, document: Document) -> bool:
    """
    Helper function to check if user has a valid (non-expired, non-revoked) AccessGrant
    for this document or document category.
    
    Returns True if:
    - Grant scope includes this document_id, OR
    - Grant scope includes this doc_category, OR
    - Grant scope is ALL_FOR_PERSON (if supported)
    """
    now = datetime.utcnow()
    grants = db.query(AccessGrant).filter(
        AccessGrant.granted_to_user_id == user.id,
        AccessGrant.person_id == person.id,
        AccessGrant.expires_at > now,
        AccessGrant.revoked_at.is_(None)
    ).all()
    
    for grant in grants:
        if grant.scope_type == GrantScopeType.DOCUMENTS:
            # Check if document ID matches grant scope_value
            if grant.scope_value == str(document.id):
                return True
        elif grant.scope_type == GrantScopeType.CATEGORY:
            # Check if document category matches grant scope_value
            if document.doc_category:
                doc_cat_str = document.doc_category.value if hasattr(document.doc_category, 'value') else str(document.doc_category)
                # Map category values to grant scope values
                category_map = {
                    "HR_SIGNED": "HR_SIGNED_DOCS",
                    "FINANCE_KYC": "FINANCE_KYC_DOCS",
                    "APPOINTMENT": "APPOINTMENT",
                    "DECLARATION": "HR_SIGNED_DOCS",  # Declaration is HR_SIGNED category
                    "ID_CARD": "ID_CARD"
                }
                expected_scope = category_map.get(doc_cat_str, doc_cat_str)
                # Check both mapped and direct values
                if grant.scope_value == expected_scope or grant.scope_value == doc_cat_str:
                    return True
    
    return False


def can_user_view_document(
    db: Session,
    user: User,
    person: Person,
    document: Document
) -> bool:
    """
    Centralized function to check if user can VIEW a document.
    
    ENTERPRISE ACCESS POLICY (checked in order, first match wins):
    
    A) MASTER_ADMIN role -> ALWAYS ALLOW
    
    B) Stage-A documents:
       - doc_category == STAGE_A OR stage == OPERATION OR visibility_scope == STAGE_A/PUBLIC_ALWAYS
       => Any authenticated user can view/download (all departments)
    
    C) Finance documents:
       - owner_dept == FINANCE OR doc_category in FINANCE_KYC OR stage == FINANCE
       => Allowed only if:
          - Requester is FINANCE dept OR
          - MASTER_ADMIN OR
          - Has active grant
    
    D) HR documents:
       - owner_dept == HR OR doc_category in APPOINTMENT/DECLARATION/HR_SIGNED OR stage == HR
       => Allowed only if:
          - Requester is HR dept OR
          - MASTER_ADMIN OR
          - Has active grant
    
    E) Grants:
       - If user has valid (not expired) access grant for this person_id and either:
         * grant scope includes this document_id, OR
         * grant scope includes this doc_category, OR
         * grant scope is ALL_FOR_PERSON
       => allowed
    
    F) If none match => DENY
    
    Note: After person becomes ACTIVE, access rules remain the same:
    - Stage-A docs: downloadable by all roles
    - Finance docs: Finance + Admin only (unless grant)
    - HR docs: HR + Admin only (unless grant)
    """
    # Rule A: Master Admin can always view
    if is_master_admin(user, db):
        return True
    
    # Rule B: Stage-A documents
    if is_stage_a_document(document):
        # Owner dept can always view Stage-A they created
        if is_owner_dept(user, document, db):
            return True
        
        # Check if user has DOC_STAGEA_VIEW permission
        from app.services.permission_checker import user_has_permission
        from app.core.permissions import PermissionCode
        has_stagea_permission = user_has_permission(db, user, PermissionCode.DOC_STAGEA_VIEW.value)
        if has_stagea_permission:
            return True
        
        # No permission, deny
        return False
    
    # Rule C: Check if user's department matches document's owner department
    # HR can download HR docs, Finance can download Finance docs, Ops can download Ops docs
    if is_owner_dept(user, document, db):
        return True
    
    # Rule D: Check for active access grants
    if has_valid_grant(db, user, person, document):
        return True
    
    # Rule E: Default - Deny access
    return False


def evaluate_document_access(
    db: Session,
    user: User,
    person: Person,
    document: Document,
    request=None
) -> dict:
    """
    Evaluate document access and return detailed information for UI badges.
    Returns dict with: can_download, reason, grant_expires_at, visibility_label.
    
    This function must never raise exceptions - it always returns a valid dict.
    
    Access Rules (checked in order):
    1. Master Admin always can_download
    2. Stage-A docs always can_download for all departments
    3. Doc owner department can_download
    4. If active access grant exists, can_download with grant_expires_at
    5. Else needs grant (can_download false)
    
    Returns:
    {
        "can_download": bool,
        "reason": str,  # AccessReason enum value
        "grant_expires_at": str | None,  # ISO datetime string
        "visibility_label": str  # For UI display
    }
    """
    try:
        from app.services.permission_checker import user_has_permission
        from app.core.permissions import PermissionCode
        
        # Rule 1: Master Admin can always download
        if is_master_admin(user, db):
            return {
                "can_download": True,
                "reason": AccessReason.ADMIN.value,
                "grant_expires_at": None,
                "visibility_label": "Available (Admin)"
            }
        
        # Rule 2: Stage-A docs always can_download for all departments
        if is_stage_a_document(document):
            # Owner dept can always download Stage-A they created
            if is_owner_dept(user, document, db):
                return {
                    "can_download": True,
                    "reason": AccessReason.OWNER_DEPT.value,
                    "grant_expires_at": None,
                    "visibility_label": "Available"
                }
            
            # Check if user has DOC_STAGEA_DOWNLOAD permission
            try:
                has_stagea_permission = user_has_permission(db, user, PermissionCode.DOC_STAGEA_DOWNLOAD.value)
                if has_stagea_permission:
                    return {
                        "can_download": True,
                        "reason": AccessReason.STAGE_A_PUBLIC.value,
                        "grant_expires_at": None,
                        "visibility_label": "Available"
                    }
            except Exception:
                # If permission check fails, still allow (defensive)
                pass
            
            # Stage-A is public, allow download
            return {
                "can_download": True,
                "reason": AccessReason.STAGE_A_PUBLIC.value,
                "grant_expires_at": None,
                "visibility_label": "Available"
            }
        
        # Rule 3: Doc owner department can_download
        if is_owner_dept(user, document, db):
            return {
                "can_download": True,
                "reason": AccessReason.OWNER_DEPT.value,
                "grant_expires_at": None,
                "visibility_label": "Available"
            }
        
        # Rule 4: Check for active access grants
        grant_expires_at = get_active_grant_expiry(db, user, person, document)
        if grant_expires_at:
            # Format expiry time for display
            now = datetime.utcnow()
            try:
                time_remaining = grant_expires_at - now
                hours_remaining = int(time_remaining.total_seconds() / 3600)
                minutes_remaining = int((time_remaining.total_seconds() % 3600) / 60)
                
                if hours_remaining > 0:
                    expiry_label = f"Expires in {hours_remaining}h {minutes_remaining}m"
                else:
                    expiry_label = f"Expires in {minutes_remaining}m"
            except Exception:
                expiry_label = "Expires soon"
            
            return {
                "can_download": True,
                "reason": AccessReason.GRANTED.value,
                "grant_expires_at": grant_expires_at.isoformat() if grant_expires_at else None,
                "visibility_label": expiry_label
            }
        
        # Rule 5: Else needs grant (can_download false)
        if document.owner_dept == DocumentOwnerDept.FINANCE:
            return {
                "can_download": False,
                "reason": AccessReason.NEEDS_GRANT.value,
                "grant_expires_at": None,
                "visibility_label": "Locked (Request Access)"
            }
        elif document.owner_dept == DocumentOwnerDept.HR:
            return {
                "can_download": False,
                "reason": AccessReason.NEEDS_GRANT.value,
                "grant_expires_at": None,
                "visibility_label": "Locked (Request Access)"
            }
        else:
            return {
                "can_download": False,
                "reason": AccessReason.FORBIDDEN.value,
                "grant_expires_at": None,
                "visibility_label": "Locked"
            }
    
    except Exception as e:
        # Defensive: function must never raise, always return valid dict
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in evaluate_document_access: {e}", exc_info=True)
        return {
            "can_download": False,
            "reason": AccessReason.FORBIDDEN.value,
            "grant_expires_at": None,
            "visibility_label": "Locked"
        }


def can_user_download_document(
    db: Session,
    user: User,
    person: Person,
    document: Document
) -> tuple[bool, Optional[str], Optional[datetime]]:
    """
    Centralized function to check if user can DOWNLOAD a document.
    Returns (allowed: bool, reason: str | None, grant_expires_at: datetime | None)
    
    This is a wrapper around evaluate_document_access for backward compatibility.
    """
    access_info = evaluate_document_access(db, user, person, document)
    grant_expires_at = None
    if access_info["grant_expires_at"]:
        try:
            from datetime import datetime
            # Handle ISO format with or without timezone
            expiry_str = access_info["grant_expires_at"]
            if expiry_str.endswith('Z'):
                expiry_str = expiry_str.replace('Z', '+00:00')
            grant_expires_at = datetime.fromisoformat(expiry_str)
        except (ValueError, AttributeError):
            grant_expires_at = None
    
    return (
        access_info["can_download"],
        access_info["reason"] if not access_info["can_download"] else None,
        grant_expires_at
    )


def get_active_grant_expiry(
    db: Session,
    user: User,
    person: Person,
    document: Document
) -> Optional[datetime]:
    """
    Get the expiration time of the active grant that enables access to this document.
    Returns None if no active grant exists.
    """
    now = datetime.utcnow()
    grants = db.query(AccessGrant).filter(
        AccessGrant.granted_to_user_id == user.id,
        AccessGrant.person_id == person.id,
        AccessGrant.expires_at > now,
        AccessGrant.revoked_at.is_(None)
    ).all()
    
    for grant in grants:
        if grant.scope_type == GrantScopeType.DOCUMENTS:
            if grant.scope_value == str(document.id):
                return grant.expires_at
        elif grant.scope_type == GrantScopeType.CATEGORY:
            if document.doc_category:
                doc_cat_str = document.doc_category.value if hasattr(document.doc_category, 'value') else str(document.doc_category)
                category_map = {
                    "HR_SIGNED": "HR_SIGNED_DOCS",
                    "FINANCE_KYC": "FINANCE_KYC_DOCS",
                    "APPOINTMENT": "APPOINTMENT",
                    "DECLARATION": "HR_SIGNED_DOCS",
                    "ID_CARD": "ID_CARD"
                }
                expected_scope = category_map.get(doc_cat_str, doc_cat_str)
                if grant.scope_value == expected_scope or grant.scope_value == doc_cat_str:
                    return grant.expires_at
    
    return None


def enforce_can_download(
    db: Session,
    user: User,
    person: Person,
    document: Document,
    request=None
) -> tuple[Optional[str], Optional[datetime]]:
    """
    Enforce document download access. Raises HTTPException 403 if access denied.
    Returns (reason, grant_expires_at) if access granted, otherwise raises exception.
    
    This is the single source of truth for download enforcement.
    All download endpoints should call this function.
    """
    from fastapi import HTTPException, status
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Defensive import: audit logging should never break downloads
    try:
        from app.services.audit_logger import log_audit_event, get_client_ip, get_user_agent
    except ImportError as e:
        logger.warning(f"Failed to import audit_logger: {e}. Audit logging will be skipped.")
        # Create no-op functions if import fails
        def log_audit_event(*args, **kwargs):
            pass
        def get_client_ip(request):
            return None
        def get_user_agent(request):
            return None
    
    allowed, reason, grant_expires_at = can_user_download_document(db, user, person, document)
    
    if not allowed:
        # Log denied access attempt (defensive: don't fail if audit logging fails)
        try:
            log_audit_event(
                db=db,
                action_type="DOC_DOWNLOAD_DENIED",
                entity_type="Document",
                entity_id=str(document.id),
                actor_user_id=user.id,
                action_metadata={
                    "person_id": str(person.id),
                    "doc_name": document.doc_name,
                    "owner_dept": document.owner_dept.value if document.owner_dept else None,
                    "doc_category": document.doc_category.value if document.doc_category else None,
                    "stage": document.stage.value if document.stage else None,
                    "denial_reason": reason
                },
                ip_address=get_client_ip(request) if request else None,
                user_agent=get_user_agent(request) if request else None
            )
        except Exception as e:
            logger.warning(f"Failed to log audit event for denied download: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason or "Document access denied. Request access via ticket."
        )
    
    # Log successful access (if not Stage-A, as Stage-A is always allowed)
    # Defensive: don't fail if audit logging fails
    if not is_stage_a_document(document):
        try:
            log_audit_event(
                db=db,
                action_type="DOC_DOWNLOAD",
                entity_type="Document",
                entity_id=str(document.id),
                actor_user_id=user.id,
                action_metadata={
                    "person_id": str(person.id),
                    "doc_name": document.doc_name,
                    "owner_dept": document.owner_dept.value if document.owner_dept else None,
                    "doc_category": document.doc_category.value if document.doc_category else None,
                    "access_via": "grant" if grant_expires_at else "owner_dept" if is_owner_dept(user, document, db) else "admin"
                },
                ip_address=get_client_ip(request) if request else None,
                user_agent=get_user_agent(request) if request else None
            )
        except Exception as e:
            logger.warning(f"Failed to log audit event for successful download: {e}")
    
    return (reason, grant_expires_at)


def get_visible_documents_for_user(
    db: Session,
    user: User,
    person: Person
) -> list[Document]:
    """
    Get all documents visible to a user for a specific person.
    Returns filtered list based on access control rules.
    """
    all_documents = db.query(Document).filter(Document.person_id == person.id).all()
    
    visible_docs = []
    for doc in all_documents:
        if can_user_view_document(db, user, person, doc):
            visible_docs.append(doc)
    
    return visible_docs

