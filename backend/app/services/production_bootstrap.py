"""
Production user bootstrap.

Creates initial production login users from ENV only when:
- ENVIRONMENT=production
- ENABLE_PROD_BOOTSTRAP=true

Idempotent: users are created only if they do not already exist.
Credentials from ENV; passwords hashed with existing logic. Never log passwords.
"""
import logging
import os
from typing import List, Optional, Tuple

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.department import Department
from app.models.role import Role

logger = logging.getLogger(__name__)

# Role code used in app (SUPER_ADMIN in spec → MASTER_ADMIN in DB)
ROLE_MASTER_ADMIN = "MASTER_ADMIN"
ROLE_SUB_ADMIN = "SUB_ADMIN"
ROLE_OPS_USER = "OPS_USER"
ROLE_FINANCE_USER = "FINANCE_USER"
ROLE_HR_USER = "HR_USER"

# Department codes in DB
DEPT_ADMIN = "ADMIN"
DEPT_OPS = "OPS"
DEPT_FIN = "FIN"
DEPT_HR = "HR"

# (env_email_key, env_password_key, role_code, dept_code, display_name)
BOOTSTRAP_SPEC: List[Tuple[str, str, str, str, str]] = [
    ("PROD_ADMIN_EMAIL", "PROD_ADMIN_PASSWORD", ROLE_MASTER_ADMIN, DEPT_ADMIN, "Production Admin"),
    ("PROD_SUBADMIN_EMAIL", "PROD_SUBADMIN_PASSWORD", ROLE_SUB_ADMIN, DEPT_ADMIN, "Production Sub-Admin"),
    ("PROD_OPS_EMAIL", "PROD_OPS_PASSWORD", ROLE_OPS_USER, DEPT_OPS, "Production Operations"),
    ("PROD_FINANCE_EMAIL", "PROD_FINANCE_PASSWORD", ROLE_FINANCE_USER, DEPT_FIN, "Production Finance"),
    ("PROD_HR_EMAIL", "PROD_HR_PASSWORD", ROLE_HR_USER, DEPT_HR, "Production HR"),
]


def _get_role_by_code(db, code: str) -> Optional[Role]:
    return db.query(Role).filter(Role.code == code).first()


def _get_department_by_code(db, code: str) -> Optional[Department]:
    return db.query(Department).filter(Department.code == code).first()


def bootstrap_production_users() -> None:
    """
    Create production users from ENV when enabled. Idempotent; safe on restart/redeploy.
    Runs only when ENVIRONMENT=production and ENABLE_PROD_BOOTSTRAP=true.
    """
    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    enabled = (os.getenv("ENABLE_PROD_BOOTSTRAP") or "").strip().lower() in ("true", "1", "yes")

    if env != "production":
        logger.info("[BOOTSTRAP] Skipped: ENVIRONMENT is not production")
        return
    if not enabled:
        logger.info("[BOOTSTRAP] Skipped: ENABLE_PROD_BOOTSTRAP is not true")
        return

    created: List[str] = []
    skipped: List[str] = []
    errors: List[str] = []

    db = SessionLocal()
    try:
        for env_email_key, env_password_key, role_code, dept_code, display_name in BOOTSTRAP_SPEC:
            email = (os.getenv(env_email_key) or "").strip()
            password = os.getenv(env_password_key) or ""

            if not email:
                logger.warning("[BOOTSTRAP] Skipped %s: %s not set", display_name, env_email_key)
                continue
            if not password:
                errors.append(f"{display_name} ({email}): password env not set")
                continue

            existing = db.query(User).filter(User.email == email).first()
            if existing:
                skipped.append(email)
                continue

            role = _get_role_by_code(db, role_code)
            dept = _get_department_by_code(db, dept_code)
            if not role:
                errors.append(f"{display_name} ({email}): role {role_code} not found")
                continue
            if not dept:
                errors.append(f"{display_name} ({email}): department {dept_code} not found")
                continue

            user = User(
                full_name=display_name,
                email=email,
                password_hash=get_password_hash(password),
                dept_id=dept.id,
                role_id=role.id,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created.append(email)
            logger.info("BOOTSTRAP CREATED: %s", email)

        if skipped:
            logger.info("[BOOTSTRAP] Already existed: %s", ", ".join(skipped))
        if errors:
            for msg in errors:
                logger.error("[BOOTSTRAP] %s", msg)
    except Exception as e:
        db.rollback()
        logger.exception("[BOOTSTRAP] Failed: %s", e)
        raise
    finally:
        db.close()
