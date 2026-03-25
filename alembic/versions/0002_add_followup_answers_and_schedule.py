"""Add follow-up answer fields and doctor availability schedule.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add answer fields to follow_ups table
    op.add_column('follow_ups', sa.Column('answer_text', sa.Text(), nullable=True))
    op.add_column('follow_ups', sa.Column('answered_by_doctor_id', sa.Integer(), sa.ForeignKey('doctors.id'), nullable=True))
    op.add_column('follow_ups', sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True))

    # Add availability_schedule JSONB to doctors table
    op.add_column('doctors', sa.Column('availability_schedule', JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('doctors', 'availability_schedule')
    op.drop_column('follow_ups', 'answered_at')
    op.drop_column('follow_ups', 'answered_by_doctor_id')
    op.drop_column('follow_ups', 'answer_text')
