"""add_access_model_fields_visibility_scope_person_timestamps

Revision ID: ec9cc6de81b3
Revises: a31038410342
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ec9cc6de81b3'
down_revision = 'a31038410342'
branch_labels = None
depends_on = None


def upgrade():
    # Create DocumentVisibilityScope enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documentvisibilityscope AS ENUM ('PRIVATE', 'PUBLIC_AFTER_FINANCE', 'PUBLIC_ALWAYS');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add visibility_scope column to documents table
    op.add_column('documents', sa.Column('visibility_scope', postgresql.ENUM('PRIVATE', 'PUBLIC_AFTER_FINANCE', 'PUBLIC_ALWAYS', name='documentvisibilityscope', create_type=False), nullable=True))
    
    # Add new PersonStatus values
    op.execute("""
        DO $$ BEGIN
            ALTER TYPE personstatus ADD VALUE IF NOT EXISTS 'FINANCE_IN_PROGRESS';
            ALTER TYPE personstatus ADD VALUE IF NOT EXISTS 'HR_COMPLETED';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add new columns to persons table
    op.add_column('persons', sa.Column('created_dept_id', sa.Integer(), nullable=True))
    op.add_column('persons', sa.Column('finance_submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('persons', sa.Column('hr_submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('persons', sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add foreign key for created_dept_id
    op.create_foreign_key('fk_persons_created_dept', 'persons', 'departments', ['created_dept_id'], ['id'])
    
    # Create index on activated_at for CV Wallet queries
    op.create_index('ix_persons_activated_at', 'persons', ['activated_at'])


def downgrade():
    # Drop index
    op.drop_index('ix_persons_activated_at', table_name='persons')
    
    # Drop foreign key
    op.drop_constraint('fk_persons_created_dept', 'persons', type_='foreignkey')
    
    # Drop columns from persons
    op.drop_column('persons', 'activated_at')
    op.drop_column('persons', 'hr_submitted_at')
    op.drop_column('persons', 'finance_submitted_at')
    op.drop_column('persons', 'created_dept_id')
    
    # Drop visibility_scope column from documents
    op.drop_column('documents', 'visibility_scope')
    
    # Note: We don't drop the enum types as they might be used elsewhere
    # If needed, manually drop: DROP TYPE IF EXISTS documentvisibilityscope;
