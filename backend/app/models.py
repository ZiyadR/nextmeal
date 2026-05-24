from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, Date, DateTime, ForeignKey, Table, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Many-to-many association table for recipes and categories
recipe_categories = Table(
    'recipe_categories',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    refresh_token = Column(String(512), nullable=True)  # stored to allow logout invalidation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recipes = relationship('Recipe', back_populates='owner', cascade='all, delete-orphan')
    meal_histories = relationship('MealHistory', back_populates='owner', cascade='all, delete-orphan')
    categories = relationship('Category', back_populates='owner', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"


class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = (
        # One category name per user (NULL user_id = global seed pool, duplicates allowed there)
        # SQLite treats each NULL as distinct so this won't block multiple seed rows with the same name.
        Index('ix_categories_name_user', 'name', 'user_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recipes = relationship('Recipe', secondary=recipe_categories, back_populates='categories')
    owner = relationship('User', back_populates='categories')

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', user_id={self.user_id})>"



class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    like_score = Column(Integer, CheckConstraint('like_score BETWEEN 1 AND 5'), nullable=True)
    effort_score = Column(Integer, CheckConstraint('effort_score BETWEEN 1 AND 5'), nullable=False)
    prep_time_minutes = Column(Integer, nullable=False, default=0)
    cook_time_minutes = Column(Integer, nullable=False, default=0)
    cleanup_effort = Column(String(10), CheckConstraint("cleanup_effort IN ('low', 'medium', 'high')"), default='medium')
    last_cooked_date = Column(Date, nullable=True)
    last_suggested_date = Column(Date, nullable=True)
    skip_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship('User', back_populates='recipes')
    categories = relationship('Category', secondary=recipe_categories, back_populates='recipes')
    meal_histories = relationship('MealHistory', back_populates='recipe')
    skips = relationship('Skip', back_populates='recipe', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, name='{self.name}', effort={self.effort_score}, like={self.like_score})>"


class MealHistory(Base):
    __tablename__ = 'meal_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    date = Column(Date, nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete='SET NULL'), nullable=True)
    meal_type = Column(String(20), default='dinner')
    cooked = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship('User', back_populates='meal_histories')
    recipe = relationship('Recipe', back_populates='meal_histories')

    def __repr__(self) -> str:
        return f"<MealHistory(id={self.id}, date={self.date}, recipe_id={self.recipe_id}, cooked={self.cooked})>"


class Skip(Base):
    __tablename__ = 'skips'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    skipped_date = Column(Date, nullable=False)
    reason = Column(String(50), nullable=True)  # 'too_much_effort', 'dont_like', or null
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recipe = relationship('Recipe', back_populates='skips')

    def __repr__(self) -> str:
        return f"<Skip(id={self.id}, recipe_id={self.recipe_id}, date={self.skipped_date}, reason='{self.reason}')>"
