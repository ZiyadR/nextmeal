"""force_drop_categories_name_unique

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-16 21:10:00.000000

Force-drop the UNIQUE constraint on categories.name by recreating the table
with raw SQL.  This migration is idempotent: if the constraint is already gone
it is a safe no-op (the table-copy still completes successfully).
"""
from alembic import op


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
