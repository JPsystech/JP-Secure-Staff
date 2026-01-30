"""
Assign default permissions to roles

This script assigns permissions to existing roles based on their function.
Run this after permission seeder has run.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.role import Role, Permission
from app.core.permissions import PermissionCode

def assign_default_permissions():
    """Assign default permissions to roles"""
    db = SessionLocal()
    try:
        # Get roles
        master_admin = db.query(Role).filter(Role.code == "MASTER_ADMIN").first()
        finance_role = db.query(Role).filter(Role.code == "FINANCE_USER").first()
        hr_role = db.query(Role).filter(Role.code == "HR_USER").first()
        ops_role = db.query(Role).filter(Role.code == "OPS_USER").first()
        sub_admin_role = db.query(Role).filter(Role.code == "SUB_ADMIN").first()
        
        # Master Admin gets ALL permissions
        if master_admin:
            all_permissions = db.query(Permission).all()
            master_admin.permissions = all_permissions
            print(f"Assigned {len(all_permissions)} permissions to MASTER_ADMIN")
        
        # Finance User permissions
        if finance_role:
            finance_perms = [
                PermissionCode.DOC_STAGEA_VIEW,
                PermissionCode.DOC_STAGEA_DOWNLOAD,
                PermissionCode.DOC_FINANCE_VIEW,
                PermissionCode.DOC_FINANCE_DOWNLOAD,
                PermissionCode.DOC_UPLOAD_FINANCE,
                PermissionCode.TICKET_CREATE,
                PermissionCode.TICKET_VIEW,
                PermissionCode.GRANT_CREATE,
                PermissionCode.GRANT_REVOKE,
            ]
            perms = db.query(Permission).filter(
                Permission.code.in_([p.value for p in finance_perms])
            ).all()
            finance_role.permissions = perms
            print(f"Assigned {len(perms)} permissions to FINANCE_USER")
        
        # HR User permissions
        if hr_role:
            hr_perms = [
                PermissionCode.DOC_STAGEA_VIEW,
                PermissionCode.DOC_STAGEA_DOWNLOAD,
                PermissionCode.DOC_UPLOAD_STAGEA,
                PermissionCode.DOC_HR_VIEW,
                PermissionCode.DOC_HR_DOWNLOAD,
                PermissionCode.DOC_UPLOAD_HR,
                PermissionCode.TICKET_CREATE,
                PermissionCode.TICKET_VIEW,
                PermissionCode.GRANT_CREATE,
                PermissionCode.GRANT_REVOKE,
                PermissionCode.TEMPLATE_VIEW,
            ]
            perms = db.query(Permission).filter(
                Permission.code.in_([p.value for p in hr_perms])
            ).all()
            hr_role.permissions = perms
            print(f"Assigned {len(perms)} permissions to HR_USER")
        
        # Operations User permissions
        if ops_role:
            ops_perms = [
                PermissionCode.DOC_STAGEA_VIEW,
                PermissionCode.DOC_STAGEA_DOWNLOAD,
                PermissionCode.DOC_UPLOAD_STAGEA,
                PermissionCode.TICKET_CREATE,
                PermissionCode.TICKET_VIEW,
            ]
            perms = db.query(Permission).filter(
                Permission.code.in_([p.value for p in ops_perms])
            ).all()
            ops_role.permissions = perms
            print(f"Assigned {len(perms)} permissions to OPS_USER")
        
        # Sub-Admin permissions (limited admin access)
        if sub_admin_role:
            sub_admin_perms = [
                PermissionCode.DOC_STAGEA_VIEW,
                PermissionCode.DOC_STAGEA_DOWNLOAD,
                PermissionCode.DOC_FINANCE_VIEW,
                PermissionCode.DOC_HR_VIEW,
                PermissionCode.TICKET_VIEW,
                PermissionCode.TEMPLATE_VIEW,
                PermissionCode.AUDIT_VIEW,
                # Note: ROLE_MANAGE, USER_MANAGE, DEPARTMENT_MANAGE are NOT included by default
                # Admin must explicitly assign these if needed
            ]
            perms = db.query(Permission).filter(
                Permission.code.in_([p.value for p in sub_admin_perms])
            ).all()
            sub_admin_role.permissions = perms
            print(f"Assigned {len(perms)} permissions to SUB_ADMIN")
        
        db.commit()
        print("\nDefault permissions assigned successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error assigning permissions: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    assign_default_permissions()
