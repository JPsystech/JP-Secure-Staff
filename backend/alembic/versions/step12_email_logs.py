"""step12: add email_logs table

Revision ID: step12_email_logs
Revises: drop_2fa_users
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = 'step12_email_logs'
down_revision = 'drop_2fa_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'email_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('to_email', sa.String(), nullable=False, index=True),
        sa.Column('cc_emails', JSONB, nullable=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('template_key', sa.String(), nullable=False, index=True),
        sa.Column('entity_type', sa.String(), nullable=True, index=True),
        sa.Column('entity_id', sa.String(), nullable=True, index=True),
        sa.Column('status', sa.String(), nullable=False, index=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('provider_message_id', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('metadata', JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('email_logs')
