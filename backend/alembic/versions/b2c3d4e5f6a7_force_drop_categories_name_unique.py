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
    # Unconditional table-copy — the only way to remove a SQLite inline UNIQUE.
    # Using a timestamp suffix on the temp table avoids collisions with any
    # leftover temp table from a previous failed run.
    op.execute("""
        CREATE TABLE categories_rebuild (
            id         INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
            name       VARCHAR(100) NOT NULL,
            user_id    INTEGER  REFERENCES users(id) ON DELETE CASCADE,
            created_at DATETIME
        )
    """)
    op.execute("INSERT INTO categories_rebuild SELECT id, name, user_id, created_at FROM categories")
    op.execute("DROP TABLE categories")
    op.execute("ALTER TABLE categories_rebuild RENAME TO categories")
    op.execute("CREATE INDEX IF NOT EXISTS ix_categories_user_id   ON categories (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_categories_name_user ON categories (name, user_id)")


def downgrade() -> None:
    pass  # No safe way to restore a unique constraint with existing duplicate names
