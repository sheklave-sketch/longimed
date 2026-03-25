"""Add doctor sex, sub_specialization, profile_photo fields + new specialties.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to doctors
    op.add_column('doctors', sa.Column('sex', sa.String(10), nullable=True))
    op.add_column('doctors', sa.Column('sub_specialization', sa.String(200), nullable=True))
    op.add_column('doctors', sa.Column('profile_photo_file_id', sa.String(200), nullable=True))

    # Add new specialty enum values
    op.execute("ALTER TYPE specialty ADD VALUE IF NOT EXISTS 'internal_medicine'")
    op.execute("ALTER TYPE specialty ADD VALUE IF NOT EXISTS 'surgery'")
    op.execute("ALTER TYPE specialty ADD VALUE IF NOT EXISTS 'orthopedics'")
    op.execute("ALTER TYPE specialty ADD VALUE IF NOT EXISTS 'ent'")
    op.execute("ALTER TYPE specialty ADD VALUE IF NOT EXISTS 'ophthalmology'")
    op.execute("ALTER TYPE specialty ADD VALUE IF NOT EXISTS 'neurology'")

    # Create sex enum type
    op.execute("DO $$ BEGIN CREATE TYPE sex AS ENUM ('male', 'female'); EXCEPTION WHEN duplicate_object THEN null; END $$")
    # Alter column to use enum (convert from varchar)
    op.execute("ALTER TABLE doctors ALTER COLUMN sex TYPE sex USING sex::sex")


def downgrade() -> None:
    op.execute("ALTER TABLE doctors ALTER COLUMN sex TYPE varchar(10)")
    op.drop_column('doctors', 'profile_photo_file_id')
    op.drop_column('doctors', 'sub_specialization')
    op.drop_column('doctors', 'sex')
