"""
Seed Sub-Admin role if it doesn't exist

This script ensures the Sub-Admin role exists in the database.
Run this after seed_data.py or if Sub-Admin role is missing.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.role import Role
from app.core.permissions import PermissionCode
from app.models.role import Permission

def seed_sub_admin_role():
    """Create Sub-Admin role if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if Sub-Admin role exists
        sub_admin = db.query(Role).filter(Role.code == "SUB_ADMIN").first()
        
        if sub_admin:
            print(f"Sub-Admin role already exists: {sub_admin.name} (ID: {sub_admin.id})")
            return sub_admin
        
        # Create Sub-Admin role
        sub_admin = Role(
            name="Sub-Admin",
            code="SUB_ADMIN",
            description="Admin user with limited access",
            is_active=True
        )
        db.add(sub_admin)
        db.commit()
        db.refresh(sub_admin)
        
        print(f"Sub-Admin role created: {sub_admin.name} (ID: {sub_admin.id})")
        
        # Assign default permissions (limited admin access)
        default_perms = [
            PermissionCode.DOC_STAGEA_VIEW,
            PermissionCode.DOC_STAGEA_DOWNLOAD,
            PermissionCode.DOC_FINANCE_VIEW,
            PermissionCode.DOC_HR_VIEW,
            PermissionCode.TICKET_VIEW,
            PermissionCode.TEMPLATE_VIEW,
            PermissionCode.AUDIT_VIEW,
        ]
        
        perms = db.query(Permission).filter(
            Permission.code.in_([p.value for p in default_perms])
        ).all()
        
        sub_admin.permissions = perms
        db.commit()
        
        print(f"Assigned {len(perms)} default permissions to Sub-Admin")
        print("Note: ROLE_MANAGE, USER_MANAGE, DEPARTMENT_MANAGE are NOT included by default.")
        print("      Assign these via /admin/roles-permissions if needed.")
        
        return sub_admin
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding Sub-Admin role: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_sub_admin_role()
