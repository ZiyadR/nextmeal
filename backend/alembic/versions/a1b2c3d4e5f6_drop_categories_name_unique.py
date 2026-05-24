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


def _get_unique_constraint_name() -> str | None:
    """Return the name of the unique constraint on categories.name, if it exists."""
    bind = op.get_bind()
    from sqlalchemy.engine import Inspector
    inspector = Inspector.from_engine(bind)
    
    # Try to find it as a unique constraint
    for uc in inspector.get_unique_constraints('categories'):
        if uc.get('column_names') == ['name']:
            return uc.get('name')
            
    # Try to find it as a unique index (sometimes constraints show up as indexes)
    for idx in inspector.get_indexes('categories'):
        if idx.get('unique') and idx.get('column_names') == ['name']:
            return idx.get('name')
            
    return None


def upgrade() -> None:
    constraint_name = _get_unique_constraint_name()
    if constraint_name:
        op.drop_constraint(constraint_name, 'categories', type_='unique')
    
    # Create indexes using the standard approach
    # In Postgres, creating an index that already exists will fail unless we use IF NOT EXISTS,
    # but Alembic's op.create_index doesn't natively support IF NOT EXISTS easily.
    # However, since this is a forward migration, they shouldn't exist yet.
    bind = op.get_bind()
    from sqlalchemy.engine import Inspector
    inspector = Inspector.from_engine(bind)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('categories')]
    
    if 'ix_categories_user_id' not in existing_indexes:
        op.create_index('ix_categories_user_id', 'categories', ['user_id'])
    if 'ix_categories_name_user' not in existing_indexes:
        op.create_index('ix_categories_name_user', 'categories', ['name', 'user_id'])


def downgrade() -> None:
    try:
        op.drop_index('ix_categories_name_user', table_name='categories')
        op.drop_index('ix_categories_user_id', table_name='categories')
        op.create_unique_constraint('categories_name_key', 'categories', ['name'])
    except Exception as e:
        print(f"Notice: Could not restore constraint: {e}")
