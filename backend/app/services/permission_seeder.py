"""
Permission Seeder

Idempotently seeds permissions from PermissionCode enum into the database.
Runs on application startup.
"""
import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.role import Permission
from app.core.permissions import PermissionCode, get_all_permission_codes, get_permission_metadata

logger = logging.getLogger(__name__)


def seed_permissions():
    """
    Seed permissions from PermissionCode enum into database.
    This is idempotent - only missing permissions are added.
    """
    db = SessionLocal()
    try:
        all_codes = get_all_permission_codes()
        seeded_count = 0
        updated_count = 0
        
        for code in all_codes:
            label, description, module, action = get_permission_metadata(code)
            
            # Check if permission already exists
            existing = db.query(Permission).filter(Permission.code == code.value).first()
            
            if existing:
                # Update label and description if they're missing or different
                needs_update = False
                if existing.label != label:
                    existing.label = label
                    needs_update = True
                if existing.description != description:
                    existing.description = description
                    needs_update = True
                if existing.module != module:
                    existing.module = module
                    needs_update = True
                if existing.action != action:
                    existing.action = action
                    needs_update = True
                
                if needs_update:
                    db.add(existing)
                    updated_count += 1
            else:
                # Create new permission
                new_permission = Permission(
                    code=code.value,
                    label=label,
                    description=description,
                    module=module,
                    action=action
                )
                db.add(new_permission)
                seeded_count += 1
        
        db.commit()

        # Ensure Master Admin role has all permissions (including any newly seeded)
        from app.models.role import Role
        master_admin = db.query(Role).filter(Role.code == "MASTER_ADMIN").first()
        if master_admin:
            all_permissions = db.query(Permission).all()
            existing_codes = {p.code for p in master_admin.permissions}
            for perm in all_permissions:
                if perm.code not in existing_codes:
                    master_admin.permissions.append(perm)
                    existing_codes.add(perm.code)
            db.commit()
        
        if seeded_count > 0:
            logger.info(f"[PERMISSION_SEEDER] Seeded {seeded_count} new permissions")
        if updated_count > 0:
            logger.info(f"[PERMISSION_SEEDER] Updated {updated_count} existing permissions")
        if seeded_count == 0 and updated_count == 0:
            logger.info("[PERMISSION_SEEDER] All permissions are up to date")
        
        return seeded_count, updated_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"[PERMISSION_SEEDER] Error seeding permissions: {e}", exc_info=True)
        raise
    finally:
        db.close()
