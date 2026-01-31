"""drop 2FA columns from users

Revision ID: drop_2fa_users
Revises: 49e3b0aee1f9
Create Date: 2026-01-29

Removes twofa_enabled and twofa_secret_encrypted from users so schema matches model.
"""
from alembic import op
import sqlalchemy as sa

revision = 'drop_2fa_users'
down_revision = '49e3b0aee1f9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute("ALTER TABLE users DROP COLUMN IF EXISTS twofa_enabled")
        op.execute("ALTER TABLE users DROP COLUMN IF EXISTS twofa_secret_encrypted")
    else:
        try:
            op.drop_column('users', 'twofa_enabled')
        except Exception:
            pass
        try:
            op.drop_column('users', 'twofa_secret_encrypted')
        except Exception:
            pass


def downgrade() -> None:
    # Do not re-add 2FA columns: 2FA removed from product; no migration re-adds them.
    pass