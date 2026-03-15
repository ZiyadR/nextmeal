"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create recipes table
    op.create_table(
        'recipes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('like_score', sa.Integer(), nullable=True),
        sa.Column('effort_score', sa.Integer(), nullable=False),
        sa.Column('prep_time_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cook_time_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cleanup_effort', sa.String(length=10), nullable=True, server_default='medium'),
        sa.Column('last_cooked_date', sa.Date(), nullable=True),
        sa.Column('last_suggested_date', sa.Date(), nullable=True),
        sa.Column('skip_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('like_score BETWEEN 1 AND 5'),
        sa.CheckConstraint('effort_score BETWEEN 1 AND 5'),
        sa.CheckConstraint("cleanup_effort IN ('low', 'medium', 'high')"),
        sa.PrimaryKeyConstraint('id')
    )

    # Create recipe_categories junction table
    op.create_table(
        'recipe_categories',
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('recipe_id', 'category_id')
    )

    # Create meal_history table
    op.create_table(
        'meal_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=True),
        sa.Column('meal_type', sa.String(length=20), nullable=True, server_default='dinner'),
        sa.Column('cooked', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create skips table
    op.create_table(
        'skips',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.Column('skipped_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_recipes_last_cooked', 'recipes', ['last_cooked_date'])
    op.create_index('idx_recipes_last_suggested', 'recipes', ['last_suggested_date'])
    op.create_index('idx_meal_history_date', 'meal_history', ['date'])
    op.create_index('idx_skips_recipe_date', 'skips', ['recipe_id', 'skipped_date'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_skips_recipe_date', table_name='skips')
    op.drop_index('idx_meal_history_date', table_name='meal_history')
    op.drop_index('idx_recipes_last_suggested', table_name='recipes')
    op.drop_index('idx_recipes_last_cooked', table_name='recipes')

    # Drop tables
    op.drop_table('skips')
    op.drop_table('meal_history')
    op.drop_table('recipe_categories')
    op.drop_table('recipes')
    op.drop_table('categories')
