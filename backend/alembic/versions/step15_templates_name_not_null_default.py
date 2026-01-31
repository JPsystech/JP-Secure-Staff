"""step15: templates name NOT NULL + default for existing rows

Revision ID: step15_tpl_name
Revises: step14_tpl_drafts
Create Date: 2026-01-29

- Backfill templates.name where NULL to 'Untitled Template'
- Set name NOT NULL with server_default for new rows
- Ensure is_active is NOT NULL where missing (additive only)
"""
from alembic import op
import sqlalchemy as sa

revision = 'step15_tpl_name'
down_revision = 'step14_tpl_drafts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != 'postgresql':
        return
    # Backfill name for existing rows (idempotent)
    op.execute(sa.text("UPDATE templates SET name = 'Untitled Template' WHERE name IS NULL"))
    # Set default for new rows and make NOT NULL (PostgreSQL)
    op.execute(sa.text("ALTER TABLE templates ALTER COLUMN name SET DEFAULT 'Untitled Template'"))
    op.execute(sa.text("ALTER TABLE templates ALTER COLUMN name SET NOT NULL"))
    # Ensure is_active has NOT NULL (in case step14 added it nullable)
    op.execute(sa.text("UPDATE templates SET is_active = false WHERE is_active IS NULL"))
    op.execute(sa.text("ALTER TABLE templates ALTER COLUMN is_active SET DEFAULT false"))
    op.execute(sa.text("ALTER TABLE templates ALTER COLUMN is_active SET NOT NULL"))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != 'postgresql':
        return
    op.execute(sa.text("ALTER TABLE templates ALTER COLUMN name DROP NOT NULL"))
    op.execute(sa.text("ALTER TABLE templates ALTER COLUMN name DROP DEFAULT"))
    op.execute(sa.text("ALTER TABLE templates ALTER COLUMN is_active DROP NOT NULL"))
    op.execute(sa.text("ALTER TABLE templates ALTER COLUMN is_active DROP DEFAULT"))
