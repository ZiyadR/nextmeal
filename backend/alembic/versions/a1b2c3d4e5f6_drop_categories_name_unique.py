"""drop_categories_name_unique_add_name_user_index

Revision ID: a1b2c3d4e5f6
Revises: 7e0cccd93cac
Create Date: 2026-03-16 21:05:00.000000

SQLite does not support DROP CONSTRAINT.  The only reliable way to remove an
inline UNIQUE constraint is to recreate the table without it.  We do this
with raw SQL so we are not dependent on the reflected schema or index names.
"""
from alembic import op
from sqlalchemy.engine import Inspector


revision = 'a1b2c3d4e5f6'
down_revision = '7e0cccd93cac'
branch_labels = None
depends_on = None


def _has_unique_on_name() -> bool:
    """Return True if categories.name still carries a unique constraint."""
    bind = op.get_bind()
    for idx in Inspector.from_engine(bind).get_indexes('categories'):
        if idx.get('unique') and idx.get('column_names') == ['name']:
            return True
    return False


def upgrade() -> None:
    if not _has_unique_on_name():
        # Already fixed — nothing to do
        return

    # SQLite table-copy to drop the inline UNIQUE on name.
    op.execute("""
        CREATE TABLE IF NOT EXISTS categories_new (
            id       INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
            name     VARCHAR(100) NOT NULL,
            user_id  INTEGER  REFERENCES users(id) ON DELETE CASCADE,
            created_at DATETIME
        )
    """)
    op.execute("INSERT INTO categories_new SELECT id, name, user_id, created_at FROM categories")
    op.execute("DROP TABLE categories")
    op.execute("ALTER TABLE categories_new RENAME TO categories")

    # Restore indexes (without the old unique-on-name one)
    op.execute("CREATE INDEX IF NOT EXISTS ix_categories_user_id    ON categories (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_categories_name_user  ON categories (name, user_id)")


def downgrade() -> None:
    # Recreate with the unique constraint
    op.execute("""
        CREATE TABLE IF NOT EXISTS categories_old (
            id       INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name     VARCHAR(100) NOT NULL UNIQUE,
            user_id  INTEGER REFERENCES users(id) ON DELETE CASCADE,
            created_at DATETIME
        )
    """)
    op.execute("INSERT INTO categories_old SELECT id, name, user_id, created_at FROM categories")
    op.execute("DROP TABLE categories")
    op.execute("ALTER TABLE categories_old RENAME TO categories")
    op.execute("CREATE INDEX IF NOT EXISTS ix_categories_user_id ON categories (user_id)")
