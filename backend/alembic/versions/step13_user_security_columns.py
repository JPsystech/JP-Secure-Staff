"""step13: add user security columns (password policy, no 2FA)

Revision ID: step13_user_sec
Revises: step12_email_logs
Create Date: 2026-01-29

Adds columns for production hardening: must_change_password, password_changed_at,
failed_login_count, locked_until. 2FA removed from product; no twofa columns.
"""
from alembic import op
import sqlalchemy as sa

revision = 'step13_user_sec'
down_revision = 'step12_email_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT false"))
        op.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP WITH TIME ZONE"))
        op.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_count INTEGER DEFAULT 0"))
        op.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE"))
    else:
        for col_name, col_type in [
            ("must_change_password", sa.Boolean()),
            ("password_changed_at", sa.DateTime(timezone=True)),
            ("failed_login_count", sa.Integer()),
            ("locked_until", sa.DateTime(timezone=True)),
        ]:
            try:
                op.add_column("users", sa.Column(col_name, col_type, nullable=True))
            except Exception:
                pass


def downgrade() -> None:
    conn = op.get_bind()
    cols = ("locked_until", "failed_login_count", "password_changed_at", "must_change_password")
    if conn.dialect.name == 'postgresql':
        for col in cols:
            op.execute(sa.text(f"ALTER TABLE users DROP COLUMN IF EXISTS {col}"))
    else:
        for col in cols:
            try:
                op.drop_column("users", col)
            except Exception:
                pass
