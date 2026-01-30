"""
Verify OPS user has DOC_STAGEA_DOWNLOAD permission

Run this script to diagnose permission assignment issues.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.role import Role, Permission
from app.models.user import User
from app.core.permissions import PermissionCode
from app.services.permission_checker import user_has_permission

def verify_ops_permissions():
    """Verify OPS role has DOC_STAGEA_DOWNLOAD permission"""
    db = SessionLocal()
    try:
        # Get OPS role
        ops_role = db.query(Role).filter(Role.code == "OPS_USER").first()
        if not ops_role:
            print("ERROR: OPS_USER role not found!")
            return
        
        print(f"OPS_USER role found: ID={ops_role.id}, Name={ops_role.name}")
        
        # Get DOC_STAGEA_DOWNLOAD permission
        stagea_download_perm = db.query(Permission).filter(
            Permission.code == PermissionCode.DOC_STAGEA_DOWNLOAD.value
        ).first()
        
        if not stagea_download_perm:
            print("ERROR: DOC_STAGEA_DOWNLOAD permission not found in database!")
            print("Run permission seeder first: permissions are auto-seeded on startup")
            return
        
        print(f"DOC_STAGEA_DOWNLOAD permission found: ID={stagea_download_perm.id}, Code={stagea_download_perm.code}")
        
        # Check if OPS role has this permission
        has_permission = stagea_download_perm in ops_role.permissions
        print(f"OPS_USER has DOC_STAGEA_DOWNLOAD: {has_permission}")
        
        if not has_permission:
            print("\nFIXING: Assigning DOC_STAGEA_DOWNLOAD to OPS_USER...")
            ops_role.permissions.append(stagea_download_perm)
            db.commit()
            print("✓ DOC_STAGEA_DOWNLOAD assigned to OPS_USER")
        else:
            print("✓ OPS_USER already has DOC_STAGEA_DOWNLOAD permission")
        
        # Check all OPS users
        ops_users = db.query(User).join(Role).filter(Role.code == "OPS_USER").all()
        print(f"\nFound {len(ops_users)} OPS users:")
        for user in ops_users:
            has_perm = user_has_permission(db, user, PermissionCode.DOC_STAGEA_DOWNLOAD.value)
            print(f"  User {user.id} ({user.email}): Has DOC_STAGEA_DOWNLOAD = {has_perm}")
        
        # List all permissions for OPS role
        print(f"\nAll permissions for OPS_USER role ({len(ops_role.permissions)} total):")
        for perm in sorted(ops_role.permissions, key=lambda p: p.code):
            print(f"  - {perm.code}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    verify_ops_permissions()
