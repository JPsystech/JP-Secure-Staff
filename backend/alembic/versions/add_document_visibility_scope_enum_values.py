"""add_document_visibility_scope_enum_values

Revision ID: add_visibility_enum_values
Revises: a6b947c61d27
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_visibility_enum_values'
down_revision = 'a6b947c61d27'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add new enum values to documentvisibilityscope enum.
    
    Note: PostgreSQL requires enum values to be committed before they can be used in UPDATE statements.
    We only add the enum values here. If DEPT_ONLY exists in the data, it will need to be updated
    in a separate migration or manually after this migration completes.
    """
    # Add new enum values to documentvisibilityscope enum
    # These will be committed when the transaction commits
    op.execute("""
        DO $$ BEGIN
            -- Add DEPARTMENT (replaces DEPT_ONLY if it exists)
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'DEPARTMENT' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'documentvisibilityscope')
            ) THEN
                ALTER TYPE documentvisibilityscope ADD VALUE 'DEPARTMENT';
            END IF;
            
            -- Add GRANT_ONLY
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'GRANT_ONLY' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'documentvisibilityscope')
            ) THEN
                ALTER TYPE documentvisibilityscope ADD VALUE 'GRANT_ONLY';
            END IF;
            
            -- Add STAGE_A
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'STAGE_A' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'documentvisibilityscope')
            ) THEN
                ALTER TYPE documentvisibilityscope ADD VALUE 'STAGE_A';
            END IF;
        END $$;
    """)
    
    # Note: We cannot update DEPT_ONLY to DEPARTMENT in the same transaction
    # because PostgreSQL requires new enum values to be committed first.
    # If DEPT_ONLY exists in your data, run this SQL manually after migration:
    # UPDATE documents SET visibility_scope = 'DEPARTMENT' WHERE visibility_scope = 'DEPT_ONLY';


def downgrade():
    # Note: PostgreSQL does not support removing enum values
    # We can only update data, not remove enum values
    # If downgrading, update STAGE_A and GRANT_ONLY to PRIVATE or PUBLIC_ALWAYS
    op.execute("""
        UPDATE documents 
        SET visibility_scope = 'PRIVATE' 
        WHERE visibility_scope IN ('STAGE_A', 'GRANT_ONLY', 'DEPARTMENT');
    """)
