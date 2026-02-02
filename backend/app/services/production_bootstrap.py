"""
Production user bootstrap.

Creates initial departments/roles and login users from ENV when BOOTSTRAP_ENABLED=true.
Idempotent: departments, roles, and users are created only if they do not already exist.
Credentials from ENV only; passwords hashed with existing logic. Never log passwords.
"""
import logging
import os
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import get_password_hash
from app.models.user import User
from app.models.department import Department
from app.models.role import Role

logger = logging.getLogger(__name__)

# Department codes and display names (OPERATIONS, FINANCE, HR, ADMIN)
DEPT_SPECS: list[Tuple[str, str]] = [
    ("ADMIN", "Administration"),
    ("OPS", "Operations"),
    ("FIN", "Finance"),
    ("HR", "Human Resources"),
]

# Role codes and display names
ROLE_SPECS: list[Tuple[str, str, str]] = [
    ("MASTER_ADMIN", "Master Admin", "Full system access"),
    ("SUB_ADMIN", "Sub-Admin", "Admin with limited access"),
    ("OPS_USER", "Operations User", "Operations department user"),
    ("FINANCE_USER", "Finance User", "Finance department user"),
    ("HR_USER", "HR User", "HR department user"),
]

# (env_email_key, env_password_key, role_code, dept_code, display_name)
USER_SPECS: list[Tuple[str, str, str, str, str]] = [
    ("ADMIN_EMAIL", "ADMIN_PASSWORD", "MASTER_ADMIN", "ADMIN", "Admin"),
    ("SUBADMIN_EMAIL", "SUBADMIN_PASSWORD", "SUB_ADMIN", "ADMIN", "Sub-Admin"),
    ("OPS_EMAIL", "OPS_PASSWORD", "OPS_USER", "OPS", "Operations"),
    ("FINANCE_EMAIL", "FINANCE_PASSWORD", "FINANCE_USER", "FIN", "Finance"),
    ("HR_EMAIL", "HR_PASSWORD", "HR_USER", "HR", "HR"),
]


def _get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Find user by email (case-insensitive)."""
    if not email:
        return None
    return db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()


def _get_role_by_code(db: Session, code: str) -> Optional[Role]:
    return db.query(Role).filter(Role.code == code).first()


def _get_department_by_code(db: Session, code: str) -> Optional[Department]:
    return db.query(Department).filter(Department.code == code).first()


def _ensure_departments_and_roles(db: Session) -> None:
    """Ensure OPERATIONS, FINANCE, HR, ADMIN departments and required roles exist. Idempotent."""
    for code, name in DEPT_SPECS:
        if _get_department_by_code(db, code) is None:
            db.add(Department(name=name, code=code, is_active=True))
    db.commit()

    for code, name, desc in ROLE_SPECS:
        if _get_role_by_code(db, code) is None:
            db.add(Role(name=name, code=code, description=desc, is_active=True))
    db.commit()


def seed_initial_users(db: Session) -> None:
    """
    Ensure departments/roles exist, then create bootstrap users from ENV if missing.
    Uses email lookup case-insensitive. Transaction-safe; idempotent.
    Logs only "Bootstrap user created: <email>" or "Bootstrap user exists: <email>".
    Never logs plaintext passwords.
    """
    _ensure_departments_and_roles(db)

    must_change = (os.getenv("DEFAULT_PASSWORD_CHANGE_REQUIRED") or "").strip().lower() in ("true", "1", "yes")

    for env_email_key, env_password_key, role_code, dept_code, display_name in USER_SPECS:
        email = (os.getenv(env_email_key) or "").strip()
        password = os.getenv(env_password_key) or ""

        if not email:
            continue
        existing = _get_user_by_email(db, email)
        if existing:
            logger.info("Bootstrap user exists: %s", email)
            continue
        if not password:
            logger.warning("[BOOTSTRAP] Skipped %s: password env not set (%s)", email, env_password_key)
            continue

        role = _get_role_by_code(db, role_code)
        dept = _get_department_by_code(db, dept_code)
        if not role:
            logger.warning("[BOOTSTRAP] Skipped %s: role %s not found", email, role_code)
            continue
        if not dept:
            logger.warning("[BOOTSTRAP] Skipped %s: department %s not found", email, dept_code)
            continue

        try:
            user = User(
                full_name=display_name,
                email=email,
                password_hash=get_password_hash(password),
                dept_id=dept.id,
                role_id=role.id,
                is_active=True,
                must_change_password=must_change,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Bootstrap user created: %s", email)
        except Exception as e:
            db.rollback()
            logger.exception("[BOOTSTRAP] Failed to create user %s: %s", email, e)
            raise


def run_bootstrap_if_enabled() -> None:
    """
    If BOOTSTRAP_ENABLED is "true", run seed_initial_users with a new session.
    Used from FastAPI startup. Does not crash if re-run.
    """
    enabled = (os.getenv("BOOTSTRAP_ENABLED") or "false").strip().lower() in ("true", "1", "yes")
    if not enabled:
        logger.info("[BOOTSTRAP] Skipped: BOOTSTRAP_ENABLED is not true")
        return
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        seed_initial_users(db)
    except Exception as e:
        logger.error("[BOOTSTRAP] Bootstrap failed: %s", e, exc_info=True)
        raise
    finally:
        db.close()


# Backward compatibility: ENABLE_PROD_BOOTSTRAP + PROD_* env vars
def bootstrap_production_users() -> None:
    """Legacy entry: run bootstrap when ENABLE_PROD_BOOTSTRAP=true or BOOTSTRAP_ENABLED=true."""
    enabled_prod = (os.getenv("ENABLE_PROD_BOOTSTRAP") or "").strip().lower() in ("true", "1", "yes")
    enabled_new = (os.getenv("BOOTSTRAP_ENABLED") or "false").strip().lower() in ("true", "1", "yes")
    if not (enabled_prod or enabled_new):
        logger.info("[BOOTSTRAP] Skipped: BOOTSTRAP_ENABLED / ENABLE_PROD_BOOTSTRAP not true")
        return
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        seed_initial_users(db)
    finally:
        db.close()
