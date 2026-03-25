"""Add doctor signup_token for Telegram account linking.

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('doctors', sa.Column('signup_token', sa.String(32), nullable=True))
    op.create_index('ix_doctors_signup_token', 'doctors', ['signup_token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_doctors_signup_token', 'doctors')
    op.drop_column('doctors', 'signup_token')
