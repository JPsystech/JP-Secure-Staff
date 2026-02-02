"""add_intake_dept_to_person

Revision ID: ffff_add_intake_dept_to_person
Revises: ec9cc6de81b3
Create Date: 2026-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ffff_add_intake_dept_to_person'
down_revision = 'ec9cc6de81b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create IntakeDept enum idempotently (SQLSTATE 42710 = duplicate_object)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE intakedept AS ENUM ('OPERATION', 'HR');
        EXCEPTION WHEN SQLSTATE '42710' THEN NULL;
        END $$;
    """)

    op.add_column(
        'persons',
        sa.Column(
            'intake_dept',
            postgresql.ENUM('OPERATION', 'HR', name='intakedept', create_type=False),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column('persons', 'intake_dept')
    # NOTE: We intentionally do not drop the enum type intakedept to avoid breaking existing rows


