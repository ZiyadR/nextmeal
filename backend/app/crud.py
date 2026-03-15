from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, datetime, timedelta
from typing import List, Optional
from app import models, schemas


# Recipe operations
def get_recipes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None
) -> List[models.Recipe]:
    """Get all recipes with optional filtering and pagination."""
    query = db.query(models.Recipe)

    if category_id:
        query = query.join(models.Recipe.categories).filter(models.Category.id == category_id)

    return query.offset(skip).limit(limit).all()


def get_recipe(db: Session, recipe_id: int) -> Optional[models.Recipe]:
    """Get a specific recipe by ID."""
    return db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()


def create_recipe(db: Session, recipe: schemas.RecipeCreate) -> models.Recipe:
    """Create a new recipe."""
    db_recipe = models.Recipe(
        name=recipe.name,
        like_score=recipe.like_score,
        effort_score=recipe.effort_score,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        cleanup_effort=recipe.cleanup_effort,
    )

    # Add categories
    if recipe.category_ids:
        categories = db.query(models.Category).filter(
            models.Category.id.in_(recipe.category_ids)
        ).all()
        db_recipe.categories = categories

    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def update_recipe_dates(
    db: Session,
    recipe_id: int,
    last_cooked_date: Optional[date] = None,
    last_suggested_date: Optional[date] = None
) -> None:
    """Update recipe's last cooked or suggested dates."""
    recipe = get_recipe(db, recipe_id)
    if recipe:
        if last_cooked_date:
            recipe.last_cooked_date = last_cooked_date
        if last_suggested_date:
            recipe.last_suggested_date = last_suggested_date
        recipe.updated_at = datetime.utcnow()
        db.commit()


def increment_skip_count(db: Session, recipe_id: int) -> None:
    """Increment the skip count for a recipe."""
    recipe = get_recipe(db, recipe_id)
    if recipe:
        recipe.skip_count += 1
        recipe.updated_at = datetime.utcnow()
        db.commit()


def update_like_score(db: Session, recipe_id: int, new_score: int) -> None:
    """Update a recipe's like score."""
    recipe = get_recipe(db, recipe_id)
    if recipe and 1 <= new_score <= 5:
        recipe.like_score = new_score
        recipe.updated_at = datetime.utcnow()
        db.commit()


# Category operations
def get_categories(db: Session) -> List[models.Category]:
    """Get all categories."""
    return db.query(models.Category).all()


def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    """Get a specific category by ID."""
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_or_create_category(db: Session, name: str) -> models.Category:
    """Get existing category by name or create new one."""
    category = db.query(models.Category).filter(models.Category.name == name).first()
    if not category:
        category = models.Category(name=name)
        db.add(category)
        db.commit()
        db.refresh(category)
    return category


# MealHistory operations
def get_meal_history(
    db: Session,
    limit: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[models.MealHistory]:
    """Get meal history with optional date filtering."""
    query = db.query(models.MealHistory).order_by(desc(models.MealHistory.date))

    if start_date:
        query = query.filter(models.MealHistory.date >= start_date)
    if end_date:
        query = query.filter(models.MealHistory.date <= end_date)

    return query.limit(limit).all()


def get_last_cooked_meal(db: Session) -> Optional[models.MealHistory]:
    """Get the most recent cooked meal."""
    return db.query(models.MealHistory)\
        .filter(models.MealHistory.cooked == True)\
        .order_by(desc(models.MealHistory.date))\
        .first()


def get_recent_meals(db: Session, limit: int = 3) -> List[models.MealHistory]:
    """Get the most recent meals."""
    return db.query(models.MealHistory)\
        .filter(models.MealHistory.cooked == True)\
        .order_by(desc(models.MealHistory.date))\
        .limit(limit)\
        .all()


def get_planned_meals(db: Session, days: int = 7) -> List[models.MealHistory]:
    """Get planned (not yet cooked) meals for the next N days."""
    today = date.today()
    # Allow 1 day of tolerance for client vs server timezone differences
    start_date = today - timedelta(days=1)
    end_date = today + timedelta(days=days - 1)
    return db.query(models.MealHistory)\
        .filter(
            models.MealHistory.date >= start_date,
            models.MealHistory.date <= end_date,
            models.MealHistory.cooked == False
        )\
        .order_by(models.MealHistory.date)\
        .all()


def delete_meal_history(db: Session, meal_id: int) -> bool:
    """Delete a planned meal. Only allows deleting future/today entries with cooked=False."""
    meal = db.query(models.MealHistory).filter(models.MealHistory.id == meal_id).first()
    if not meal:
        return False
    # Allow 1 day timezone offset tolerance
    if meal.date < (date.today() - timedelta(days=1)):
        return False
    if meal.cooked:
        return False
    db.delete(meal)
    db.commit()
    return True


def create_meal_history(
    db: Session,
    recipe_id: Optional[int],
    meal_date: date,
    meal_type: str = 'dinner',
    cooked: bool = True
) -> models.MealHistory:
    """Create a new meal history entry."""
    meal = models.MealHistory(
        date=meal_date,
        recipe_id=recipe_id,
        meal_type=meal_type,
        cooked=cooked
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)

    # Update recipe's last_cooked_date if cooked
    if cooked and recipe_id:
        update_recipe_dates(db, recipe_id, last_cooked_date=meal_date)

    return meal


# Skip operations
def record_skip(
    db: Session,
    recipe_id: int,
    skipped_date: date,
    reason: Optional[str] = None
) -> models.Skip:
    """Record a recipe skip."""
    skip = models.Skip(
        recipe_id=recipe_id,
        skipped_date=skipped_date,
        reason=reason
    )
    db.add(skip)

    # Increment skip count
    increment_skip_count(db, recipe_id)

    # Optionally adjust like_score based on reason
    if reason == 'dont_like':
        recipe = get_recipe(db, recipe_id)
        if recipe and recipe.like_score and recipe.like_score > 1:
            update_like_score(db, recipe_id, recipe.like_score - 1)

    db.commit()
    db.refresh(skip)
    return skip


def get_skips_since(db: Session, days: int = 4) -> List[models.Skip]:
    """Get all skips within the last N days."""
    cutoff_date = date.today() - timedelta(days=days)
    return db.query(models.Skip)\
        .filter(models.Skip.skipped_date >= cutoff_date)\
        .all()


def count_skips_since(db: Session, days: int = 7) -> int:
    """Count total skips within the last N days."""
    cutoff_date = date.today() - timedelta(days=days)
    return db.query(models.Skip)\
        .filter(models.Skip.skipped_date >= cutoff_date)\
        .count()


# Stats operations
def get_cooking_stats(db: Session) -> dict:
    """Get cooking statistics."""
    # Total meals cooked
    total_meals = db.query(models.MealHistory)\
        .filter(models.MealHistory.cooked == True)\
        .count()

    # Most cooked recipes
    most_cooked = db.query(
        models.Recipe.id,
        models.Recipe.name,
        func.count(models.MealHistory.id).label('count')
    ).join(models.MealHistory)\
        .filter(models.MealHistory.cooked == True)\
        .group_by(models.Recipe.id)\
        .order_by(desc('count'))\
        .limit(5)\
        .all()

    most_cooked_list = [
        {'recipe_id': r.id, 'recipe_name': r.name, 'times_cooked': r.count}
        for r in most_cooked
    ]

    # Category distribution
    category_dist = db.query(
        models.Category.name,
        func.count(models.MealHistory.id).label('count')
    ).join(models.Recipe.categories)\
        .join(models.MealHistory)\
        .filter(models.MealHistory.cooked == True)\
        .group_by(models.Category.name)\
        .all()

    category_dict = {cat.name: cat.count for cat in category_dist}

    # Average effort score
    avg_effort = db.query(func.avg(models.Recipe.effort_score))\
        .join(models.MealHistory)\
        .filter(models.MealHistory.cooked == True)\
        .scalar() or 0.0

    return {
        'total_meals_cooked': total_meals,
        'most_cooked_recipes': most_cooked_list,
        'category_distribution': category_dict,
        'average_effort_score': round(avg_effort, 2)
    }


def get_recipe_category_names(db: Session, recipe_id: int) -> List[str]:
    """Get category names for a recipe."""
    recipe = get_recipe(db, recipe_id)
    if recipe:
        return [cat.name for cat in recipe.categories]
    return []


def get_days_since_last_cooked(db: Session, recipe_id: int) -> Optional[int]:
    """Get number of days since recipe was last cooked."""
    recipe = get_recipe(db, recipe_id)
    if recipe and recipe.last_cooked_date:
        delta = date.today() - recipe.last_cooked_date
        return delta.days
    return None


def update_recipe(db: Session, recipe_id: int, recipe_update: schemas.RecipeUpdate) -> Optional[models.Recipe]:
    """Update an existing recipe with partial data."""
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return None

    # Update fields if provided
    update_data = recipe_update.model_dump(exclude_unset=True)
    category_ids = update_data.pop('category_ids', None)

    for field, value in update_data.items():
        setattr(recipe, field, value)

    # Update categories if provided
    if category_ids is not None:
        categories = db.query(models.Category).filter(
            models.Category.id.in_(category_ids)
        ).all()
        recipe.categories = categories

    recipe.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe_id: int) -> dict:
    """
    Delete a recipe and return affected records count.

    - MealHistory entries with this recipe_id will be SET NULL (preserve history)
    - Skip entries will CASCADE DELETE (configured in model)
    """
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return {"success": False, "message": "Recipe not found", "meal_history_affected": 0}

    # Count meal history entries that will be affected
    meal_history_count = db.query(models.MealHistory).filter(
        models.MealHistory.recipe_id == recipe_id
    ).count()

    recipe_name = recipe.name

    # Delete the recipe (cascade handles Skip entries, SET NULL handles MealHistory)
    db.delete(recipe)
    db.commit()

    return {
        "success": True,
        "message": f"Recipe '{recipe_name}' deleted successfully",
        "meal_history_affected": meal_history_count
    }


def get_recipe_by_name(db: Session, name: str) -> Optional[models.Recipe]:
    """Get a recipe by exact name match (case-insensitive)."""
    return db.query(models.Recipe).filter(
        func.lower(models.Recipe.name) == name.lower()
    ).first()


def search_recipes(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 100
) -> List[models.Recipe]:
    """Search recipes by name (case-insensitive partial match)."""
    search_pattern = f"%{query}%"
    return db.query(models.Recipe).filter(
        models.Recipe.name.ilike(search_pattern)
    ).offset(skip).limit(limit).all()


def delete_category(db: Session, category_id: int) -> bool:
    """
    Delete a category. Will remove category associations from recipes.
    Returns True if deleted, False if not found.
    """
    category = get_category(db, category_id)
    if not category:
        return False

    db.delete(category)
    db.commit()
    return True
