"""
Print current Alembic heads and applied revision. Warn if multiple heads.
Run: python -m app.scripts.db_check (from backend/ or project root with PYTHONPATH=backend)
"""
import os
import sys

# Ensure backend is on path when run as python -m app.scripts.db_check
if __name__ == "__main__":
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

def main():
    # Load .env from backend if present
    backend_for_env = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(backend_for_env, ".env")
    if os.path.isfile(env_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            pass

    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine, text

    # Find alembic.ini (backend/alembic.ini)
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(backend, "alembic.ini")
    if not os.path.isfile(ini_path):
        backend = os.getcwd()
        ini_path = os.path.join(backend, "alembic.ini")
    if not os.path.isfile(ini_path):
        print("alembic.ini not found")
        sys.exit(1)

    config = Config(ini_path)
    config.set_main_option("script_location", os.path.join(backend, "alembic"))
    script = ScriptDirectory.from_config(config)
    heads = list(script.get_heads())

    print("Alembic heads:", heads if heads else "(none)")
    if len(heads) > 1:
        print("WARNING: Multiple heads. Run: alembic merge -m 'merge heads' " + " ".join(heads))
        print("Then: alembic upgrade head")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set, cannot show applied revision")
        return
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            r = conn.execute(text("SELECT version_num FROM alembic_version"))
            rows = r.fetchall()
        applied = [row[0] for row in rows]
        print("Applied revision(s):", applied if applied else "(none)")
        if len(applied) > 1:
            print("WARNING: Multiple applied revisions (branching). Consider merging heads.")
        if applied and heads and applied[0] not in heads:
            print("INFO: Applied revision may be behind head. Run: alembic upgrade head")
    except Exception as e:
        print("Could not read alembic_version:", e)

if __name__ == "__main__":
    main()
    sys.exit(0)
