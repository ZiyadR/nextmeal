"""add_users_and_user_id_columns

Revision ID: 7e0cccd93cac
Revises: 001
Create Date: 2026-03-15 18:46:27.293347

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Inspector


# revision identifiers, used by Alembic.
revision = '7e0cccd93cac'
down_revision = '001'
branch_labels = None
depends_on = None


def _existing_tables() -> set:
    bind = op.get_bind()
    return set(Inspector.from_engine(bind).get_table_names())


def _existing_columns(table: str) -> set:
    bind = op.get_bind()
    return {col["name"] for col in Inspector.from_engine(bind).get_columns(table)}


def _existing_indexes(table: str) -> set:
    bind = op.get_bind()
    return {idx["name"] for idx in Inspector.from_engine(bind).get_indexes(table)}


def upgrade() -> None:
    tables = _existing_tables()

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('hashed_password', sa.String(length=255), nullable=False),
            sa.Column('refresh_token', sa.String(length=512), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )

    indexes = _existing_indexes('users')
    if 'ix_users_email' not in indexes:
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # ------------------------------------------------------------------
    # categories — add user_id column if table pre-exists
    # ------------------------------------------------------------------
    if 'categories' not in tables:
        op.create_table(
            'categories',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    else:
        cols = _existing_columns('categories')
        if 'user_id' not in cols:
            op.add_column('categories', sa.Column('user_id', sa.Integer(), nullable=True))

    indexes = _existing_indexes('categories')
    if 'ix_categories_user_id' not in indexes:
        op.create_index(op.f('ix_categories_user_id'), 'categories', ['user_id'], unique=False)

    # ------------------------------------------------------------------
    # recipes — add user_id column if table pre-exists
    # ------------------------------------------------------------------
    if 'recipes' not in tables:
        op.create_table(
            'recipes',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('like_score', sa.Integer(), nullable=True),
            sa.Column('effort_score', sa.Integer(), nullable=False),
            sa.Column('prep_time_minutes', sa.Integer(), nullable=False),
            sa.Column('cook_time_minutes', sa.Integer(), nullable=False),
            sa.Column('cleanup_effort', sa.String(length=10), nullable=True),
            sa.Column('last_cooked_date', sa.Date(), nullable=True),
            sa.Column('last_suggested_date', sa.Date(), nullable=True),
            sa.Column('skip_count', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    else:
        cols = _existing_columns('recipes')
        if 'user_id' not in cols:
            op.add_column('recipes', sa.Column('user_id', sa.Integer(), nullable=True))

    indexes = _existing_indexes('recipes')
    if 'ix_recipes_user_id' not in indexes:
        op.create_index(op.f('ix_recipes_user_id'), 'recipes', ['user_id'], unique=False)

    # ------------------------------------------------------------------
    # meal_history — add user_id column if table pre-exists
    # ------------------------------------------------------------------
    if 'meal_history' not in tables:
        op.create_table(
            'meal_history',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('recipe_id', sa.Integer(), nullable=True),
            sa.Column('meal_type', sa.String(length=20), nullable=True),
            sa.Column('cooked', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    else:
        cols = _existing_columns('meal_history')
        if 'user_id' not in cols:
            op.add_column('meal_history', sa.Column('user_id', sa.Integer(), nullable=True))

    indexes = _existing_indexes('meal_history')
    if 'ix_meal_history_user_id' not in indexes:
        op.create_index(op.f('ix_meal_history_user_id'), 'meal_history', ['user_id'], unique=False)

    # ------------------------------------------------------------------
    # recipe_categories
    # ------------------------------------------------------------------
    if 'recipe_categories' not in tables:
        op.create_table(
            'recipe_categories',
            sa.Column('recipe_id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('recipe_id', 'category_id'),
        )

    # ------------------------------------------------------------------
    # skips — add user_id column if table pre-exists
    # ------------------------------------------------------------------
    if 'skips' not in tables:
        op.create_table(
            'skips',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('recipe_id', sa.Integer(), nullable=False),
            sa.Column('skipped_date', sa.Date(), nullable=False),
            sa.Column('reason', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    else:
        cols = _existing_columns('skips')
        if 'user_id' not in cols:
            op.add_column('skips', sa.Column('user_id', sa.Integer(), nullable=True))

    indexes = _existing_indexes('skips')
    if 'ix_skips_user_id' not in indexes:
        op.create_index(op.f('ix_skips_user_id'), 'skips', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_skips_user_id'), table_name='skips')
    op.drop_table('skips')
    op.drop_table('recipe_categories')
    op.drop_index(op.f('ix_meal_history_user_id'), table_name='meal_history')
    op.drop_table('meal_history')
    op.drop_index(op.f('ix_recipes_user_id'), table_name='recipes')
    op.drop_table('recipes')
    op.drop_index(op.f('ix_categories_user_id'), table_name='categories')
    op.drop_table('categories')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
