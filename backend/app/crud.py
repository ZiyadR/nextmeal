from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, datetime, timedelta
from typing import List, Optional
from app import models, schemas


# --------------------------------------------------------------------------
# Category seeding
# --------------------------------------------------------------------------

# Default category names used to seed new user accounts.
# These match the categories that were initially loaded via seed_data.py.
def seed_categories_for_user(db: Session, user_id: int) -> None:
    """
    Copy the global seed categories (user_id IS NULL) into a new user's space.
    Skips any category name the user already owns (idempotent).
    """
    # Names the user already has
    existing = {
        row[0]
        for row in db.query(models.Category.name)
        .filter(models.Category.user_id == user_id)
        .all()
    }

    # Global seed pool (created by seed_data.py with user_id=NULL)
    seed_names = [
        row[0]
        for row in db.query(models.Category.name)
        .filter(models.Category.user_id.is_(None))
        .distinct()
        .all()
    ]

    for name in seed_names:
        if name not in existing:
            db.add(models.Category(name=name, user_id=user_id))

    db.commit()



def seed_recipes_for_user(db: Session, user_id: int) -> None:
    """
    Copy the global seed recipes (user_id IS NULL) into a new user's recipe list.
    Each recipe's categories are remapped to the user's own categories by name.
    Idempotent — skips any recipe name the user already owns.
    """
    # Names the user already has
    existing_names = {
        row[0]
        for row in db.query(models.Recipe.name)
        .filter(models.Recipe.user_id == user_id)
        .all()
    }

    # Build a lookup of the user's categories by name
    user_cats = {
        cat.name: cat
        for cat in db.query(models.Category)
        .filter(models.Category.user_id == user_id)
        .all()
    }

    # Fetch all global seed recipes with their categories eagerly
    seed_recipes = (
        db.query(models.Recipe)
        .filter(models.Recipe.user_id.is_(None))
        .all()
    )

    for seed in seed_recipes:
        if seed.name in existing_names:
            continue

        new_recipe = models.Recipe(
            user_id=user_id,
            name=seed.name,
            like_score=seed.like_score,
            effort_score=seed.effort_score,
            prep_time_minutes=seed.prep_time_minutes,
            cook_time_minutes=seed.cook_time_minutes,
            cleanup_effort=seed.cleanup_effort,
            skip_count=0,
        )

        # Map global categories → user's categories by name
        new_recipe.categories = [
            user_cats[cat.name]
            for cat in seed.categories
            if cat.name in user_cats
        ]

        db.add(new_recipe)

    db.commit()


# --------------------------------------------------------------------------
# Recipe operations

# --------------------------------------------------------------------------

def get_recipes(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
) -> List[models.Recipe]:
    """Get all recipes for a user with optional filtering and pagination."""
    query = db.query(models.Recipe).filter(models.Recipe.user_id == user_id)

    if category_id:
        query = query.join(models.Recipe.categories).filter(models.Category.id == category_id)

    return query.offset(skip).limit(limit).all()


def get_recipe(db: Session, recipe_id: int, user_id: int) -> Optional[models.Recipe]:
    """Get a specific recipe by ID, scoped to the requesting user."""
    return (
        db.query(models.Recipe)
        .filter(models.Recipe.id == recipe_id, models.Recipe.user_id == user_id)
        .first()
    )


def create_recipe(db: Session, recipe: schemas.RecipeCreate, user_id: int) -> models.Recipe:
    """Create a new recipe owned by user_id."""
    db_recipe = models.Recipe(
        user_id=user_id,
        name=recipe.name,
        like_score=recipe.like_score,
        effort_score=recipe.effort_score,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        cleanup_effort=recipe.cleanup_effort,
    )

    if recipe.category_ids:
        categories = (
            db.query(models.Category)
            .filter(models.Category.id.in_(recipe.category_ids), models.Category.user_id == user_id)
            .all()
        )
        db_recipe.categories = categories

    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def update_recipe_dates(
    db: Session,
    recipe_id: int,
    user_id: int,
    last_cooked_date: Optional[date] = None,
    last_suggested_date: Optional[date] = None,
) -> None:
    """Update recipe's last cooked or suggested dates."""
    recipe = get_recipe(db, recipe_id, user_id)
    if recipe:
        if last_cooked_date:
            recipe.last_cooked_date = last_cooked_date
        if last_suggested_date:
            recipe.last_suggested_date = last_suggested_date
        recipe.updated_at = datetime.utcnow()
        db.commit()


def increment_skip_count(db: Session, recipe_id: int, user_id: int) -> None:
    """Increment the skip count for a recipe."""
    recipe = get_recipe(db, recipe_id, user_id)
    if recipe:
        recipe.skip_count += 1
        recipe.updated_at = datetime.utcnow()
        db.commit()


def update_like_score(db: Session, recipe_id: int, user_id: int, new_score: int) -> None:
    """Update a recipe's like score."""
    recipe = get_recipe(db, recipe_id, user_id)
    if recipe and 1 <= new_score <= 5:
        recipe.like_score = new_score
        recipe.updated_at = datetime.utcnow()
        db.commit()


# --------------------------------------------------------------------------
# Category operations (per-user)
# --------------------------------------------------------------------------

def get_categories(db: Session, user_id: int) -> List[models.Category]:
    """Get all categories for a user."""
    return db.query(models.Category).filter(models.Category.user_id == user_id).all()


def get_category(db: Session, category_id: int, user_id: int) -> Optional[models.Category]:
    """Get a specific category by ID, scoped to the user."""
    return (
        db.query(models.Category)
        .filter(models.Category.id == category_id, models.Category.user_id == user_id)
        .first()
    )


def get_or_create_category(db: Session, name: str, user_id: int) -> models.Category:
    """Get existing category by name for the user, or create a new one."""
    category = (
        db.query(models.Category)
        .filter(func.lower(models.Category.name) == name.lower(), models.Category.user_id == user_id)
        .first()
    )
    if not category:
        category = models.Category(name=name, user_id=user_id)
        db.add(category)
        db.commit()
        db.refresh(category)
    return category


def delete_category(db: Session, category_id: int, user_id: int) -> bool:
    """
    Delete a category owned by the user. Removes associations from recipes.
    Returns True if deleted, False if not found.
    """
    category = get_category(db, category_id, user_id)
    if not category:
        return False
    db.delete(category)
    db.commit()
    return True


# --------------------------------------------------------------------------
# MealHistory operations
# --------------------------------------------------------------------------

def get_meal_history(
    db: Session,
    user_id: int,
    limit: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[models.MealHistory]:
    """Get meal history for a user with optional date filtering."""
    query = (
        db.query(models.MealHistory)
        .filter(models.MealHistory.user_id == user_id)
        .order_by(desc(models.MealHistory.date))
    )

    if start_date:
        query = query.filter(models.MealHistory.date >= start_date)
    if end_date:
        query = query.filter(models.MealHistory.date <= end_date)

    return query.limit(limit).all()


def get_last_cooked_meal(db: Session, user_id: int) -> Optional[models.MealHistory]:
    """Get the most recent cooked meal for a user."""
    return (
        db.query(models.MealHistory)
        .filter(models.MealHistory.user_id == user_id, models.MealHistory.cooked == True)
        .order_by(desc(models.MealHistory.date))
        .first()
    )


def get_recent_meals(db: Session, user_id: int, limit: int = 3) -> List[models.MealHistory]:
    """Get the most recent cooked meals for a user."""
    return (
        db.query(models.MealHistory)
        .filter(models.MealHistory.user_id == user_id, models.MealHistory.cooked == True)
        .order_by(desc(models.MealHistory.date))
        .limit(limit)
        .all()
    )


def get_planned_meals(db: Session, user_id: int, days: int = 7) -> List[models.MealHistory]:
    """Get planned (not yet cooked) meals for the next N days for a user."""
    today = date.today()
    start_date = today - timedelta(days=1)
    end_date = today + timedelta(days=days - 1)
    return (
        db.query(models.MealHistory)
        .filter(
            models.MealHistory.user_id == user_id,
            models.MealHistory.date >= start_date,
            models.MealHistory.date <= end_date,
            models.MealHistory.cooked == False,
        )
        .order_by(models.MealHistory.date)
        .all()
    )


def delete_meal_history(db: Session, meal_id: int, user_id: int) -> bool:
    """Delete a planned meal owned by the user. Only allows future/today uncooked entries."""
    meal = (
        db.query(models.MealHistory)
        .filter(models.MealHistory.id == meal_id, models.MealHistory.user_id == user_id)
        .first()
    )
    if not meal:
        return False
    if meal.date < (date.today() - timedelta(days=1)):
        return False
    if meal.cooked:
        return False
    db.delete(meal)
    db.commit()
    return True


def create_meal_history(
    db: Session,
    user_id: int,
    recipe_id: Optional[int],
    meal_date: date,
    meal_type: str = 'dinner',
    cooked: bool = True,
) -> models.MealHistory:
    """Create a new meal history entry for a user."""
    meal = models.MealHistory(
        user_id=user_id,
        date=meal_date,
        recipe_id=recipe_id,
        meal_type=meal_type,
        cooked=cooked,
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)

    if cooked and recipe_id:
        update_recipe_dates(db, recipe_id, user_id, last_cooked_date=meal_date)

    return meal


# --------------------------------------------------------------------------
# Skip operations
# --------------------------------------------------------------------------

def record_skip(
    db: Session,
    user_id: int,
    recipe_id: int,
    skipped_date: date,
    reason: Optional[str] = None,
) -> models.Skip:
    """Record a recipe skip for a user."""
    skip = models.Skip(
        user_id=user_id,
        recipe_id=recipe_id,
        skipped_date=skipped_date,
        reason=reason,
    )
    db.add(skip)

    increment_skip_count(db, recipe_id, user_id)

    if reason == 'dont_like':
        recipe = get_recipe(db, recipe_id, user_id)
        if recipe and recipe.like_score and recipe.like_score > 1:
            update_like_score(db, recipe_id, user_id, recipe.like_score - 1)

    db.commit()
    db.refresh(skip)
    return skip


def get_skips_since(db: Session, user_id: int, days: int = 4) -> List[models.Skip]:
    """Get all skips for a user within the last N days."""
    cutoff_date = date.today() - timedelta(days=days)
    return (
        db.query(models.Skip)
        .filter(models.Skip.user_id == user_id, models.Skip.skipped_date >= cutoff_date)
        .all()
    )


def count_skips_since(db: Session, user_id: int, days: int = 7) -> int:
    """Count total skips for a user within the last N days."""
    cutoff_date = date.today() - timedelta(days=days)
    return (
        db.query(models.Skip)
        .filter(models.Skip.user_id == user_id, models.Skip.skipped_date >= cutoff_date)
        .count()
    )


# --------------------------------------------------------------------------
# Stats operations
# --------------------------------------------------------------------------

def get_cooking_stats(db: Session, user_id: int) -> dict:
    """Get cooking statistics for a user."""
    total_meals = (
        db.query(models.MealHistory)
        .filter(models.MealHistory.user_id == user_id, models.MealHistory.cooked == True)
        .count()
    )

    most_cooked = (
        db.query(
            models.Recipe.id,
            models.Recipe.name,
            func.count(models.MealHistory.id).label('count'),
        )
        .join(models.MealHistory)
        .filter(models.MealHistory.user_id == user_id, models.MealHistory.cooked == True)
        .group_by(models.Recipe.id)
        .order_by(desc('count'))
        .limit(5)
        .all()
    )

    most_cooked_list = [
        {'recipe_id': r.id, 'recipe_name': r.name, 'times_cooked': r.count}
        for r in most_cooked
    ]

    category_dist = (
        db.query(
            models.Category.name,
            func.count(models.MealHistory.id).label('count'),
        )
        .join(models.Recipe.categories)
        .join(models.MealHistory)
        .filter(models.MealHistory.user_id == user_id, models.MealHistory.cooked == True)
        .group_by(models.Category.name)
        .all()
    )

    category_dict = {cat.name: cat.count for cat in category_dist}

    avg_effort = (
        db.query(func.avg(models.Recipe.effort_score))
        .join(models.MealHistory)
        .filter(models.MealHistory.user_id == user_id, models.MealHistory.cooked == True)
        .scalar()
        or 0.0
    )

    return {
        'total_meals_cooked': total_meals,
        'most_cooked_recipes': most_cooked_list,
        'category_distribution': category_dict,
        'average_effort_score': round(avg_effort, 2),
    }


# --------------------------------------------------------------------------
# Miscellaneous helpers
# --------------------------------------------------------------------------

def get_recipe_category_names(db: Session, recipe_id: int, user_id: int) -> List[str]:
    """Get category names for a recipe owned by the user."""
    recipe = get_recipe(db, recipe_id, user_id)
    if recipe:
        return [cat.name for cat in recipe.categories]
    return []


def get_days_since_last_cooked(db: Session, recipe_id: int, user_id: int) -> Optional[int]:
    """Get number of days since a recipe owned by the user was last cooked."""
    recipe = get_recipe(db, recipe_id, user_id)
    if recipe and recipe.last_cooked_date:
        delta = date.today() - recipe.last_cooked_date
        return delta.days
    return None


def update_recipe(
    db: Session,
    recipe_id: int,
    user_id: int,
    recipe_update: schemas.RecipeUpdate,
) -> Optional[models.Recipe]:
    """Update an existing recipe with partial data, scoped to the user."""
    recipe = get_recipe(db, recipe_id, user_id)
    if not recipe:
        return None

    update_data = recipe_update.model_dump(exclude_unset=True)
    category_ids = update_data.pop('category_ids', None)

    for field, value in update_data.items():
        setattr(recipe, field, value)

    if category_ids is not None:
        categories = (
            db.query(models.Category)
            .filter(models.Category.id.in_(category_ids), models.Category.user_id == user_id)
            .all()
        )
        recipe.categories = categories

    recipe.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe_id: int, user_id: int) -> dict:
    """
    Delete a recipe owned by the user and return affected records count.

    - MealHistory entries will be SET NULL (preserves history)
    - Skip entries will CASCADE DELETE
    """
    recipe = get_recipe(db, recipe_id, user_id)
    if not recipe:
        return {"success": False, "message": "Recipe not found", "meal_history_affected": 0}

    meal_history_count = (
        db.query(models.MealHistory)
        .filter(models.MealHistory.recipe_id == recipe_id)
        .count()
    )

    recipe_name = recipe.name
    db.delete(recipe)
    db.commit()

    return {
        "success": True,
        "message": f"Recipe '{recipe_name}' deleted successfully",
        "meal_history_affected": meal_history_count,
    }


def get_recipe_by_name(db: Session, name: str, user_id: int) -> Optional[models.Recipe]:
    """Get a recipe by exact name match (case-insensitive), scoped to the user."""
    return (
        db.query(models.Recipe)
        .filter(func.lower(models.Recipe.name) == name.lower(), models.Recipe.user_id == user_id)
        .first()
    )


def search_recipes(
    db: Session,
    user_id: int,
    query: str,
    skip: int = 0,
    limit: int = 100,
) -> List[models.Recipe]:
    """Search recipes by name (case-insensitive partial match), scoped to the user."""
    search_pattern = f"%{query}%"
    return (
        db.query(models.Recipe)
        .filter(models.Recipe.name.ilike(search_pattern), models.Recipe.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
