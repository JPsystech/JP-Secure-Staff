from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load env before config so DATABASE_URL/SECRET_KEY are available (Railway injects at runtime)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.core.database import Base
from app.core.config import settings
from app.models import (
    User, Department, Role, Permission, UserRole,
    CompanyMaster, DocumentNameMaster, LocationMaster, ProjectMaster,
    Policy, Template, TemplateRevision,
    Person, Employment, FinanceKYC, RatePlan, Document
)

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url from env (settings.DATABASE_URL; respects POSTGRES_URL fallback)
db_url = (getattr(settings, "DATABASE_URL", None) or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
if not db_url:
    raise RuntimeError("DATABASE_URL or POSTGRES_URL must be set for migrations")
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

