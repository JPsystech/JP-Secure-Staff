"""
CLI to run initial user bootstrap using DATABASE_URL.

Usage (from backend root):
  python -m app.scripts.bootstrap_users

Requires DATABASE_URL (or POSTGRES_URL) and bootstrap env vars
(ADMIN_EMAIL, ADMIN_PASSWORD, SUBADMIN_EMAIL, etc.) in environment or .env.
"""
import os
import sys

# Ensure backend root is on path when run as python -m app.scripts.bootstrap_users
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.core.database import SessionLocal
from app.services.production_bootstrap import seed_initial_users


def main() -> int:
    db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or ""
    if not db_url.strip():
        print("ERROR: DATABASE_URL or POSTGRES_URL not set", file=sys.stderr)
        return 1
    db = SessionLocal()
    try:
        seed_initial_users(db)
        print("Bootstrap completed.")
        return 0
    except Exception as e:
        print(f"Bootstrap failed: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
