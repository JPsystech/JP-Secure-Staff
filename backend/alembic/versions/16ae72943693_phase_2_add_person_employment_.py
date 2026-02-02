"""Phase 2: Add Person, Employment, FinanceKYC, RatePlan, Document models

Revision ID: 16ae72943693
Revises: 06e276ae99bb
Create Date: 2026-01-21 16:06:33.649206

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '16ae72943693'
down_revision = '06e276ae99bb'
branch_labels = None
depends_on = None


def _create_enum_if_not_exists(enum_name: str, values: list) -> None:
    """Idempotent PostgreSQL ENUM creation (SQLSTATE 42710 = duplicate_object)."""
    vals = ", ".join(repr(v) for v in values)
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE {enum_name} AS ENUM ({vals});
        EXCEPTION WHEN SQLSTATE '42710' THEN NULL;
        END $$;
    """)


def upgrade() -> None:
    # Create enum types idempotently first (no duplicate_object on re-run)
    _create_enum_if_not_exists("stream", ["MECH", "CIVIL", "ELEC", "OTHER"])
    _create_enum_if_not_exists("education", ["DIPLOMA", "DEGREE", "ME", "OTHER"])
    _create_enum_if_not_exists("personstatus", ["DRAFT", "SUBMITTED_TO_FINANCE", "SENT_TO_HR", "ACTIVE"])
    _create_enum_if_not_exists("documentstage", ["OPERATION", "FINANCE", "HR"])
    _create_enum_if_not_exists("employmenttype", ["PERMANENT", "FREELANCER", "CONTRACTUAL"])
    _create_enum_if_not_exists("plantype", ["MANDAY", "MANMONTH", "MONTHLY_SALARY"])
    _create_enum_if_not_exists("workingdaymode", ["CALENDAR", "WORKING_26"])

    stream_enum = postgresql.ENUM("MECH", "CIVIL", "ELEC", "OTHER", name="stream", create_type=False)
    education_enum = postgresql.ENUM("DIPLOMA", "DEGREE", "ME", "OTHER", name="education", create_type=False)
    personstatus_enum = postgresql.ENUM("DRAFT", "SUBMITTED_TO_FINANCE", "SENT_TO_HR", "ACTIVE", name="personstatus", create_type=False)
    documentstage_enum = postgresql.ENUM("OPERATION", "FINANCE", "HR", name="documentstage", create_type=False)
    employmenttype_enum = postgresql.ENUM("PERMANENT", "FREELANCER", "CONTRACTUAL", name="employmenttype", create_type=False)
    plantype_enum = postgresql.ENUM("MANDAY", "MANMONTH", "MONTHLY_SALARY", name="plantype", create_type=False)
    workingdaymode_enum = postgresql.ENUM("CALENDAR", "WORKING_26", name="workingdaymode", create_type=False)

    op.create_table('persons',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('mobile', sa.String(), nullable=False),
    sa.Column('alt_mobile', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('dob', sa.Date(), nullable=True),
    sa.Column('stream', stream_enum, nullable=True),
    sa.Column('stream_other', sa.String(), nullable=True),
    sa.Column('education', education_enum, nullable=True),
    sa.Column('education_other', sa.String(), nullable=True),
    sa.Column('location', sa.String(), nullable=True),
    sa.Column('status', personstatus_enum, nullable=False),
    sa.Column('created_by_user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_persons_id'), 'persons', ['id'], unique=False)
    op.create_table('documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.UUID(), nullable=False),
    sa.Column('stage', documentstage_enum, nullable=False),
    sa.Column('doc_name', sa.String(), nullable=False),
    sa.Column('file_key', sa.String(), nullable=False),
    sa.Column('mime_type', sa.String(), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('is_mandatory', sa.Boolean(), nullable=True),
    sa.Column('created_by_user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_table('employments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.UUID(), nullable=False),
    sa.Column('employment_type', employmenttype_enum, nullable=False),
    sa.Column('employee_code', sa.String(), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['company_master.id'], ),
    sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employments_employee_code'), 'employments', ['employee_code'], unique=True)
    op.create_index(op.f('ix_employments_id'), 'employments', ['id'], unique=False)
    op.create_table('finance_kyc',
    sa.Column('person_id', sa.UUID(), nullable=False),
    sa.Column('aadhaar', sa.String(), nullable=True),
    sa.Column('pan', sa.String(), nullable=True),
    sa.Column('bank_account_no', sa.String(), nullable=True),
    sa.Column('ifsc', sa.String(), nullable=True),
    sa.Column('bank_name', sa.String(), nullable=True),
    sa.Column('branch', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ),
    sa.PrimaryKeyConstraint('person_id')
    )
    op.create_table('rate_plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.UUID(), nullable=False),
    sa.Column('plan_type', plantype_enum, nullable=False),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('working_day_mode', workingdaymode_enum, nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project_master.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rate_plans_id'), 'rate_plans', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_rate_plans_id'), table_name='rate_plans')
    op.drop_table('rate_plans')
    op.drop_table('finance_kyc')
    op.drop_index(op.f('ix_employments_id'), table_name='employments')
    op.drop_index(op.f('ix_employments_employee_code'), table_name='employments')
    op.drop_table('employments')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_index(op.f('ix_persons_id'), table_name='persons')
    op.drop_table('persons')
    # ### end Alembic commands ###

