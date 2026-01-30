"""
Smoke tests for HR pack: generate-hr-pack and send-hr-pack.

- Validates that send-hr-pack returns 400 with clear message when Appointment or Declaration is missing.
- Uses existing DB; creates minimal test user/person with unique identifiers.

Run: pytest backend/tests/test_hr_pack.py -v
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.models.person import Person, PersonStatus
from app.models.document import Document, DocumentCategory, DocumentOwnerDept, DocumentStage
from app.core.security import get_password_hash, create_access_token
from app.core.permissions import PermissionCode
from app.models.role import Permission


@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_permissions(db):
    for code in [PermissionCode.DOC_UPLOAD_HR.value, PermissionCode.HR_IDCARD_SEND.value]:
        p = db.query(Permission).filter(Permission.code == code).first()
        if not p:
            p = Permission(code=code, label=code, description="", module="documents", action="")
            db.add(p)
    db.commit()


@pytest.fixture
def hr_user(db):
    _ensure_permissions(db)
    dept = db.query(Department).filter(Department.code == "HR").first()
    if not dept:
        dept = Department(name="HR", code="HR", is_active=True)
        db.add(dept)
        db.flush()
    role = db.query(Role).filter(Role.code == "HR_USER").first()
    if not role:
        role = Role(name="HR User", code="HR_USER", description="HR", is_active=True)
        db.add(role)
        db.flush()
        for code in [PermissionCode.DOC_UPLOAD_HR.value, PermissionCode.HR_IDCARD_SEND.value]:
            perm = db.query(Permission).filter(Permission.code == code).first()
            if perm:
                role.permissions.append(perm)
        db.flush()
    user = db.query(User).filter(User.email == "hr_test_hr_pack@test.com").first()
    if not user:
        user = User(
            full_name="HR Test Pack",
            email="hr_test_hr_pack@test.com",
            password_hash=get_password_hash("test123"),
            dept_id=dept.id,
            role_id=role.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def person_with_email_no_docs(db, hr_user):
    """Person with email but no Appointment/Declaration documents."""
    p = Person(
        id=uuid4(),
        name="Test Person",
        mobile="9876543210",
        email="person@example.com",
        status=PersonStatus.SENT_TO_HR,
        created_by_user_id=hr_user.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def client_with_auth(hr_user):
    token = create_access_token(data={"sub": hr_user.email})
    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


def test_send_hr_pack_returns_400_when_appointment_missing(client_with_auth, person_with_email_no_docs):
    """Send HR pack must return 400 with clear message when Appointment or Declaration is missing."""
    person_id = str(person_with_email_no_docs.id)
    r = client_with_auth.post(
        f"/api/v1/hr/persons/{person_id}/send-hr-pack",
        json={},
    )
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
    detail = data["detail"]
    assert "Generate" in detail or "Missing" in detail
    assert "Appointment" in detail or "Declaration" in detail


def test_send_hr_pack_returns_400_when_declaration_missing(
    db, hr_user, client_with_auth, person_with_email_no_docs
):
    """When only Appointment exists, send-hr-pack must return 400 and mention Declaration missing."""
    person_id = person_with_email_no_docs.id
    # Add only Appointment doc (no Declaration)
    doc = Document(
        person_id=person_id,
        stage=DocumentStage.HR,
        owner_dept=DocumentOwnerDept.HR,
        doc_category=DocumentCategory.APPOINTMENT,
        doc_name="Appointment Letter",
        file_key=f"persons/{person_id}/appointment_test.pdf",
        mime_type="application/pdf",
        size_bytes=0,
        is_mandatory=True,
        created_by_user_id=hr_user.id,
    )
    db.add(doc)
    db.commit()

    r = client_with_auth.post(
        f"/api/v1/hr/persons/{person_id}/send-hr-pack",
        json={},
    )
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
    assert "Declaration" in data["detail"] or "Missing" in data["detail"]
