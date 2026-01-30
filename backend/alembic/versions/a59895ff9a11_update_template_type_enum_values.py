"""update_template_type_enum_values

Revision ID: a59895ff9a11
Revises: 16ae72943693
Create Date: 2026-01-22 11:01:44.974989

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a59895ff9a11'
down_revision = '16ae72943693'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update PostgreSQL enum type to add new values
    # Note: ALTER TYPE ADD VALUE cannot be run inside a transaction in PostgreSQL
    # If this migration fails, run: python scripts/update_template_enum.py
    # Then mark this migration as applied: alembic stamp head
    
    # Try to add enum values (will fail if already added, but that's OK)
    try:
        op.execute("ALTER TYPE templatetype ADD VALUE 'APPOINTMENT_PERMANENT'")
    except Exception:
        pass  # Already exists
    
    try:
        op.execute("ALTER TYPE templatetype ADD VALUE 'APPOINTMENT_FREELANCER'")
    except Exception:
        pass  # Already exists
    
    try:
        op.execute("ALTER TYPE templatetype ADD VALUE 'APPOINTMENT_CONTRACTUAL'")
    except Exception:
        pass  # Already exists
    
    # Update existing data to use new enum values
    op.execute("""
        UPDATE templates 
        SET type = 'APPOINTMENT_PERMANENT'::templatetype
        WHERE type = 'APPOINTMENT_PERM'::templatetype
    """)
    op.execute("""
        UPDATE templates 
        SET type = 'APPOINTMENT_FREELANCER'::templatetype
        WHERE type = 'APPOINTMENT_FREEL'::templatetype
    """)
    op.execute("""
        UPDATE templates 
        SET type = 'APPOINTMENT_CONTRACTUAL'::templatetype
        WHERE type = 'APPOINTMENT_CONT'::templatetype
    """)
    
    # Note: PostgreSQL doesn't support removing enum values directly
    # The old values will remain in the enum but won't be used


def downgrade() -> None:
    # Revert data back to old enum values
    op.execute("""
        UPDATE templates 
        SET type = 'APPOINTMENT_PERM'::templatetype
        WHERE type = 'APPOINTMENT_PERMANENT'::templatetype
    """)
    op.execute("""
        UPDATE templates 
        SET type = 'APPOINTMENT_FREEL'::templatetype
        WHERE type = 'APPOINTMENT_FREELANCER'::templatetype
    """)
    op.execute("""
        UPDATE templates 
        SET type = 'APPOINTMENT_CONT'::templatetype
        WHERE type = 'APPOINTMENT_CONTRACTUAL'::templatetype
    """)
    
    # Note: Cannot remove enum values in PostgreSQL, so they remain
