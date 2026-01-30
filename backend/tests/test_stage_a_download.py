"""
Tests for Stage-A document download access control

Run with: pytest backend/tests/test_stage_a_download.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.models.person import Person, PersonStatus
from app.models.document import Document, DocumentCategory, DocumentOwnerDept, DocumentStage, DocumentVisibilityScope
from app.core.security import get_password_hash
from app.core.permissions import PermissionCode
from app.models.role import Permission
from app.services.document_access import can_user_download_document
import uuid


@pytest.fixture(scope="function")
def db():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def ops_role(db: Session):
    """Create OPS_USER role with DOC_STAGEA_DOWNLOAD permission"""
    role = Role(
        name="Operations User",
        code="OPS_USER",
        description="Operations department user",
        is_active=True
    )
    db.add(role)
    db.flush()
    
    # Get or create DOC_STAGEA_DOWNLOAD permission
    perm = db.query(Permission).filter(Permission.code == PermissionCode.DOC_STAGEA_DOWNLOAD.value).first()
    if not perm:
        perm = Permission(
            code=PermissionCode.DOC_STAGEA_DOWNLOAD.value,
            label="Download Stage-A Documents",
            description="Download Stage-A documents from CV Wallet",
            module="documents",
            action="download_stagea"
        )
        db.add(perm)
        db.flush()
    
    role.permissions.append(perm)
    db.commit()
    return role


@pytest.fixture
def ops_user(db: Session, ops_role: Role):
    """Create an OPS user"""
    dept = Department(name="Operations", code="OPS", is_active=True)
    db.add(dept)
    db.flush()
    
    user = User(
        full_name="OPS Test User",
        email="ops_test@test.com",
        password_hash=get_password_hash("test123"),
        dept_id=dept.id,
        role_id=ops_role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def hr_user(db: Session):
    """Create an HR user"""
    dept = Department(name="Human Resources", code="HR", is_active=True)
    db.add(dept)
    db.flush()
    
    role = Role(
        name="HR User",
        code="HR_USER",
        description="HR department user",
        is_active=True
    )
    db.add(role)
    db.flush()
    
    # Add DOC_STAGEA_DOWNLOAD permission
    perm = db.query(Permission).filter(Permission.code == PermissionCode.DOC_STAGEA_DOWNLOAD.value).first()
    if not perm:
        perm = Permission(
            code=PermissionCode.DOC_STAGEA_DOWNLOAD.value,
            label="Download Stage-A Documents",
            description="Download Stage-A documents from CV Wallet",
            module="documents",
            action="download_stagea"
        )
        db.add(perm)
        db.flush()
    
    role.permissions.append(perm)
    db.flush()
    
    user = User(
        full_name="HR Test User",
        email="hr_test@test.com",
        password_hash=get_password_hash("test123"),
        dept_id=dept.id,
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def person(db: Session):
    """Create a test person"""
    person = Person(
        id=uuid.uuid4(),
        full_name="Test Person",
        email="testperson@test.com",
        status=PersonStatus.ACTIVE
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@pytest.fixture
def stage_a_doc_ops(db: Session, person: Person, ops_user: User):
    """Create a Stage-A document uploaded by OPS"""
    doc = Document(
        person_id=person.id,
        stage=DocumentStage.OPERATION,
        owner_dept=DocumentOwnerDept.OPERATIONS,
        doc_category=DocumentCategory.STAGE_A,
        visibility_scope=DocumentVisibilityScope.PUBLIC_ALWAYS,
        doc_name="test_cv.pdf",
        file_key="test/path/test_cv.pdf",
        mime_type="application/pdf",
        size_bytes=1024,
        created_by_user_id=ops_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@pytest.fixture
def stage_a_doc_hr(db: Session, person: Person, hr_user: User):
    """Create a Stage-A document uploaded by HR"""
    doc = Document(
        person_id=person.id,
        stage=DocumentStage.OPERATION,
        owner_dept=DocumentOwnerDept.HR,
        doc_category=DocumentCategory.STAGE_A,
        visibility_scope=DocumentVisibilityScope.PUBLIC_ALWAYS,
        doc_name="test_qualification.pdf",
        file_key="test/path/test_qualification.pdf",
        mime_type="application/pdf",
        size_bytes=2048,
        created_by_user_id=hr_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_ops_user_with_permission_can_download_stage_a(db: Session, ops_user: User, person: Person, stage_a_doc_ops: Document):
    """Test: OPS user with DOC_STAGEA_DOWNLOAD permission can download Stage-A doc"""
    allowed, reason, grant_expires = can_user_download_document(db, ops_user, person, stage_a_doc_ops)
    
    assert allowed is True, f"OPS user should be able to download Stage-A doc. Reason: {reason}"
    assert reason is None, "Should not have denial reason"
    assert grant_expires is None, "Should not require grant"


def test_ops_user_without_permission_cannot_download_stage_a(db: Session, ops_user: User, person: Person, stage_a_doc_hr: Document):
    """Test: OPS user without DOC_STAGEA_DOWNLOAD permission cannot download Stage-A doc if not owner"""
    # Remove permission from role
    ops_role = db.query(Role).filter(Role.id == ops_user.role_id).first()
    perm = db.query(Permission).filter(Permission.code == PermissionCode.DOC_STAGEA_DOWNLOAD.value).first()
    if perm in ops_role.permissions:
        ops_role.permissions.remove(perm)
        db.commit()
    
    allowed, reason, grant_expires = can_user_download_document(db, ops_user, person, stage_a_doc_hr)
    
    assert allowed is False, "OPS user without permission should not be able to download HR-uploaded Stage-A doc"
    assert reason is not None, "Should have denial reason"
    assert "DOC_STAGEA_DOWNLOAD" in reason or "permission" in reason.lower(), f"Reason should mention permission: {reason}"


def test_hr_uploaded_stage_a_downloadable_by_ops_after_active(db: Session, ops_user: User, person: Person, stage_a_doc_hr: Document):
    """Test: HR-uploaded Stage-A doc is still downloadable by OPS after person is ACTIVE"""
    # Ensure person is ACTIVE
    person.status = PersonStatus.ACTIVE
    db.commit()
    
    allowed, reason, grant_expires = can_user_download_document(db, ops_user, person, stage_a_doc_hr)
    
    assert allowed is True, f"OPS user should be able to download HR-uploaded Stage-A doc when person is ACTIVE. Reason: {reason}"
    assert reason is None, "Should not have denial reason"


def test_ops_user_can_download_own_stage_a_without_permission(db: Session, ops_user: User, person: Person, stage_a_doc_ops: Document):
    """Test: OPS user can download Stage-A doc they created even without permission (owner dept bypass)"""
    # Remove permission from role
    ops_role = db.query(Role).filter(Role.id == ops_user.role_id).first()
    perm = db.query(Permission).filter(Permission.code == PermissionCode.DOC_STAGEA_DOWNLOAD.value).first()
    if perm in ops_role.permissions:
        ops_role.permissions.remove(perm)
        db.commit()
    
    allowed, reason, grant_expires = can_user_download_document(db, ops_user, person, stage_a_doc_ops)
    
    assert allowed is True, "OPS user should be able to download Stage-A doc they created (owner dept bypass)"
    assert reason is None, "Should not have denial reason"
