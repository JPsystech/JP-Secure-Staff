"""step14: templates name+is_active, hr_document_drafts for editable HR docs

Revision ID: step14_tpl_drafts
Revises: step13_user_sec
Create Date: 2026-01-29

- templates: add name (nullable), is_active (default false)
- hr_document_drafts: store HR-edited content per person per doc_type (APPOINTMENT/DECLARATION)
"""
from alembic import op
import sqlalchemy as sa

revision = 'step14_tpl_drafts'
down_revision = 'step13_user_sec'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute(sa.text("ALTER TABLE templates ADD COLUMN IF NOT EXISTS name VARCHAR(255)"))
        op.execute(sa.text("ALTER TABLE templates ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false"))
    else:
        try:
            op.add_column("templates", sa.Column("name", sa.String(255), nullable=True))
        except Exception:
            pass
        try:
            op.add_column("templates", sa.Column("is_active", sa.Boolean(), server_default="0", nullable=True))
        except Exception:
            pass

    op.create_table(
        "hr_document_drafts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("person_id", sa.UUID(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("doc_type", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_hr_document_drafts_person_doc_type", "hr_document_drafts", ["person_id", "doc_type"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_hr_document_drafts_person_doc_type", table_name="hr_document_drafts")
    op.drop_table("hr_document_drafts")
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute(sa.text("ALTER TABLE templates DROP COLUMN IF EXISTS is_active"))
        op.execute(sa.text("ALTER TABLE templates DROP COLUMN IF EXISTS name"))
    else:
        try:
            op.drop_column("templates", "is_active")
        except Exception:
            pass
        try:
            op.drop_column("templates", "name")
        except Exception:
            pass
