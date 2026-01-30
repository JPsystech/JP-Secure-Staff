import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.department import Department
from app.models.role import Role, Permission
from app.models.master_data import CompanyMaster
from app.models.policy import Policy

def seed_data():
    db = SessionLocal()
    try:
        # Check and create departments
        dept_finance = db.query(Department).filter(Department.code == "FIN").first()
        if not dept_finance:
            dept_finance = Department(name="Finance", code="FIN", is_active=True)
            db.add(dept_finance)
        
        dept_hr = db.query(Department).filter(Department.code == "HR").first()
        if not dept_hr:
            dept_hr = Department(name="Human Resources", code="HR", is_active=True)
            db.add(dept_hr)
        
        dept_ops = db.query(Department).filter(Department.code == "OPS").first()
        if not dept_ops:
            dept_ops = Department(name="Operations", code="OPS", is_active=True)
            db.add(dept_ops)
        
        dept_admin = db.query(Department).filter(Department.code == "ADMIN").first()
        if not dept_admin:
            dept_admin = Department(name="Administration", code="ADMIN", is_active=True)
            db.add(dept_admin)
        
        db.commit()
        db.refresh(dept_finance)
        db.refresh(dept_hr)
        db.refresh(dept_ops)
        db.refresh(dept_admin)
        
        # Check and create roles
        role_master_admin = db.query(Role).filter(Role.code == "MASTER_ADMIN").first()
        if not role_master_admin:
            role_master_admin = Role(
                name="Master Admin",
                code="MASTER_ADMIN",
                description="Full system access",
                is_active=True
            )
            db.add(role_master_admin)
        
        role_finance = db.query(Role).filter(Role.code == "FINANCE_USER").first()
        if not role_finance:
            role_finance = Role(
                name="Finance User",
                code="FINANCE_USER",
                description="Finance department user",
                is_active=True
            )
            db.add(role_finance)
        
        role_hr = db.query(Role).filter(Role.code == "HR_USER").first()
        if not role_hr:
            role_hr = Role(
                name="HR User",
                code="HR_USER",
                description="HR department user",
                is_active=True
            )
            db.add(role_hr)
        
        role_ops = db.query(Role).filter(Role.code == "OPS_USER").first()
        if not role_ops:
            role_ops = Role(
                name="Operations User",
                code="OPS_USER",
                description="Operations department user",
                is_active=True
            )
            db.add(role_ops)
        
        role_sub_admin = db.query(Role).filter(Role.code == "SUB_ADMIN").first()
        if not role_sub_admin:
            role_sub_admin = Role(
                name="Sub-Admin",
                code="SUB_ADMIN",
                description="Admin user with limited access",
                is_active=True
            )
            db.add(role_sub_admin)
        
        db.commit()
        db.refresh(role_master_admin)
        db.refresh(role_finance)
        db.refresh(role_hr)
        db.refresh(role_ops)
        db.refresh(role_sub_admin)
        
        # Create Phase 3 Permissions
        phase3_permissions = [
            ("tickets:create", "tickets", "create"),
            ("tickets:view_my", "tickets", "view_my"),
            ("tickets:view_inbox", "tickets", "view_inbox"),
            ("tickets:comment", "tickets", "comment"),
            ("tickets:update_status", "tickets", "update_status"),
            ("grants:create", "grants", "create"),
            ("grants:revoke", "grants", "revoke"),
            ("audit:view", "audit", "view"),
            ("DOC_VIEW_STAGEA", "documents", "view_stagea"),
            ("DOC_DOWNLOAD_STAGEA", "documents", "download_stagea"),
        ]
        
        for perm_code, module, action in phase3_permissions:
            perm = db.query(Permission).filter(Permission.code == perm_code).first()
            if not perm:
                perm = Permission(code=perm_code, module=module, action=action)
                db.add(perm)
        
        db.commit()
        
        # Assign permissions to roles
        # Master Admin gets all permissions
        master_admin_perms = db.query(Permission).all()
        for perm in master_admin_perms:
            if perm not in role_master_admin.permissions:
                role_master_admin.permissions.append(perm)
        
        # All users can create tickets and view their own
        ticket_create = db.query(Permission).filter(Permission.code == "tickets:create").first()
        ticket_view_my = db.query(Permission).filter(Permission.code == "tickets:view_my").first()
        ticket_comment = db.query(Permission).filter(Permission.code == "tickets:comment").first()
        
        for role in [role_finance, role_hr, role_ops]:
            if ticket_create and ticket_create not in role.permissions:
                role.permissions.append(ticket_create)
            if ticket_view_my and ticket_view_my not in role.permissions:
                role.permissions.append(ticket_view_my)
            if ticket_comment and ticket_comment not in role.permissions:
                role.permissions.append(ticket_comment)
        
        # Finance and HR can view inbox and grant access
        ticket_view_inbox = db.query(Permission).filter(Permission.code == "tickets:view_inbox").first()
        ticket_update_status = db.query(Permission).filter(Permission.code == "tickets:update_status").first()
        grant_create = db.query(Permission).filter(Permission.code == "grants:create").first()
        grant_revoke = db.query(Permission).filter(Permission.code == "grants:revoke").first()
        
        for role in [role_finance, role_hr]:
            if ticket_view_inbox and ticket_view_inbox not in role.permissions:
                role.permissions.append(ticket_view_inbox)
            if ticket_update_status and ticket_update_status not in role.permissions:
                role.permissions.append(ticket_update_status)
            if grant_create and grant_create not in role.permissions:
                role.permissions.append(grant_create)
            if grant_revoke and grant_revoke not in role.permissions:
                role.permissions.append(grant_revoke)
        
        # Only Master Admin can view audit logs
        audit_view = db.query(Permission).filter(Permission.code == "audit:view").first()
        if audit_view and audit_view not in role_master_admin.permissions:
            role_master_admin.permissions.append(audit_view)
        
        db.commit()
        print("Phase 3 permissions created and assigned to roles")
        
        # Check and create users
        master_admin = db.query(User).filter(User.email == "admin@jpsecure.com").first()
        if not master_admin:
            master_admin = User(
                full_name="Master Admin",
                email="admin@jpsecure.com",
                password_hash=get_password_hash("admin123"),
                dept_id=dept_admin.id,
                role_id=role_master_admin.id,
                is_active=True,
            )
            db.add(master_admin)
        
        finance_user = db.query(User).filter(User.email == "finance@jpsecure.com").first()
        if not finance_user:
            finance_user = User(
                full_name="Finance User",
                email="finance@jpsecure.com",
                password_hash=get_password_hash("finance123"),
                dept_id=dept_finance.id,
                role_id=role_finance.id,
                is_active=True,
            )
            db.add(finance_user)
        
        hr_user = db.query(User).filter(User.email == "hr@jpsecure.com").first()
        if not hr_user:
            hr_user = User(
                full_name="HR User",
                email="hr@jpsecure.com",
                password_hash=get_password_hash("hr123"),
                dept_id=dept_hr.id,
                role_id=role_hr.id,
                is_active=True,
            )
            db.add(hr_user)
        
        ops_user = db.query(User).filter(User.email == "ops@jpsecure.com").first()
        if not ops_user:
            ops_user = User(
                full_name="Operations User",
                email="ops@jpsecure.com",
                password_hash=get_password_hash("ops123"),
                dept_id=dept_ops.id,
                role_id=role_ops.id,
                is_active=True,
            )
            db.add(ops_user)
        
        db.commit()
        db.refresh(master_admin)
        
        # Create Akshar company if not exists
        akshar_company = db.query(CompanyMaster).filter(CompanyMaster.short_code == "AC").first()
        if not akshar_company:
            akshar_company = CompanyMaster(
                name="Akshar",
                short_code="AC",
                is_akshar=True
            )
            db.add(akshar_company)
            db.commit()
            db.refresh(akshar_company)
            print(f"Akshar Company created: {akshar_company.name} (ID: {akshar_company.id})")
        else:
            print(f"Akshar Company already exists: {akshar_company.name} (ID: {akshar_company.id})")
        
        # Create default policies if not exists
        download_policy = db.query(Policy).filter(Policy.key == "download_policy_stagea_when_hr_pending").first()
        if not download_policy:
            download_policy = Policy(
                key="download_policy_stagea_when_hr_pending",
                value_json={"value": False},
                updated_by=master_admin.id
            )
            db.add(download_policy)
            db.commit()
            print("Download policy created")
        else:
            print("Download policy already exists")
        
        # Assign DOC_VIEW_STAGEA and DOC_DOWNLOAD_STAGEA to all roles (all authenticated users can view/download Stage-A)
        doc_view_stagea = db.query(Permission).filter(Permission.code == "DOC_VIEW_STAGEA").first()
        doc_download_stagea = db.query(Permission).filter(Permission.code == "DOC_DOWNLOAD_STAGEA").first()
        
        for role in [role_master_admin, role_finance, role_hr, role_ops]:
            if doc_view_stagea and doc_view_stagea not in role.permissions:
                role.permissions.append(doc_view_stagea)
            if doc_download_stagea and doc_download_stagea not in role.permissions:
                role.permissions.append(doc_download_stagea)
        
        db.commit()
        print("Stage-A document permissions assigned to all roles")
        
        print("\nSeed data check completed!")
        print("Master Admin: admin@jpsecure.com / admin123")
        print("Finance: finance@jpsecure.com / finance123")
        print("HR: hr@jpsecure.com / hr123")
        print("Operations: ops@jpsecure.com / ops123")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()

