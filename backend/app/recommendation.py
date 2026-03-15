from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Tuple
from app import models, schemas, crud


def get_context_signals(db: Session, current_time: Optional[datetime] = None) -> schemas.ContextSignals:
    """
    Infer context from current time and recent behavior.

    Returns:
        ContextSignals: Context information including time of day, fatigue, recent categories
    """
    if current_time is None:
        current_time = datetime.now()

    hour = current_time.hour

    # Time of day classification
    if 5 <= hour < 12:
        time_of_day = 'morning'
    elif 12 <= hour < 17:
        time_of_day = 'afternoon'
    elif 17 <= hour < 22:
        time_of_day = 'evening'
    else:
        time_of_day = 'night'

    is_late = hour >= 21 or hour < 6

    # Get recent skip count (last 7 days)
    recent_skip_count = crud.count_skips_since(db, days=7)

    # Infer fatigue from skips or late hour
    fatigue_inferred = recent_skip_count >= 3 or is_late

    # Get last meal effort
    last_meal = crud.get_last_cooked_meal(db)
    last_meal_effort = last_meal.recipe.effort_score if last_meal and last_meal.recipe else 3

    # Get categories from last 3 meals
    recent_meals = crud.get_recent_meals(db, limit=3)
    recent_categories = []
    for meal in recent_meals:
        if meal.recipe:
            categories = crud.get_recipe_category_names(db, meal.recipe_id)
            recent_categories.extend(categories)

    # Remove duplicates while preserving order
    recent_categories = list(dict.fromkeys(recent_categories))
    
    # Get categories from planned meals (next 14 days)
    planned_meals = crud.get_planned_meals(db, days=14)
    planned_categories = []
    for meal in planned_meals:
        if meal.recipe_id:
            categories = crud.get_recipe_category_names(db, meal.recipe_id)
            planned_categories.extend(categories)
    
    # Remove duplicates
    planned_categories = list(dict.fromkeys(planned_categories))

    return schemas.ContextSignals(
        time_of_day=time_of_day,
        is_late=is_late,
        recent_skip_count=recent_skip_count,
        fatigue_inferred=fatigue_inferred,
        last_meal_effort=last_meal_effort,
        recent_categories=recent_categories,
        planned_categories=planned_categories
    )


def calculate_recipe_score(
    recipe: models.Recipe,
    context: schemas.ContextSignals,
    db: Session
) -> float:
    """
    Calculate score for a recipe based on preferences, effort, recentness, and context.

    Scoring formula:
        score = 100 (base)
          + preference_weight (0 to +50)
          - effort_penalty (-50 to 0, amplified if fatigued)
          - recentness_penalty (-40 to 0)
          - category_overlap_penalty (-30 to 0)
          - skip_penalty (-50 to 0)
          + context_bonus (0 to +30)

    Returns:
        float: Score for the recipe (higher is better)
    """
    score = 100.0  # Base score

    # --- PREFERENCE WEIGHT (0 to +50 points) ---
    if recipe.like_score:
        score += recipe.like_score * 10  # 10, 20, 30, 40, 50
    else:
        score += 25  # Neutral for unrated recipes

    # --- EFFORT PENALTY (-50 to 0 points) ---
    effort_penalty = recipe.effort_score * 10  # 10, 20, 30, 40, 50

    # Amplify effort penalty when fatigued
    if context.fatigue_inferred:
        effort_penalty *= 1.5

    # Penalize long cook times if late
    if context.is_late:
        total_time = recipe.prep_time_minutes + recipe.cook_time_minutes
        if total_time > 45:
            effort_penalty += 20

    score -= effort_penalty

    # --- RECENTNESS PENALTY (-40 to 0 points) ---
    days_since_cooked = crud.get_days_since_last_cooked(db, recipe.id)
    if days_since_cooked is None:
        recentness_penalty = 0  # Never cooked = no penalty
    elif days_since_cooked < 3:
        recentness_penalty = 40
    elif days_since_cooked < 7:
        recentness_penalty = 25
    elif days_since_cooked < 14:
        recentness_penalty = 10
    else:
        recentness_penalty = 0

    score -= recentness_penalty

    # --- CATEGORY OVERLAP PENALTY (-45 to 0 points) ---
    recipe_categories = crud.get_recipe_category_names(db, recipe.id)
    overlap_penalty = 0
    for cat in recipe_categories:
        if cat in context.recent_categories:
            overlap_penalty += 15
        if hasattr(context, 'planned_categories') and cat in context.planned_categories:
            overlap_penalty += 15

    score -= min(overlap_penalty, 45)  # Cap at -45

    # --- SKIP PENALTY (-50 to 0 points) ---
    skip_penalty = recipe.skip_count * 5  # Each skip = -5 points
    score -= min(skip_penalty, 50)  # Cap at -50

    # --- CONTEXT BONUS (0 to +30 points) ---
    bonus = 0

    # Bonus for easy meals when fatigued
    if context.fatigue_inferred and recipe.effort_score <= 2:
        bonus += 15

    # Bonus for favorites when user is consistent (no recent skips)
    if context.recent_skip_count == 0 and recipe.like_score == 5:
        bonus += 10

    # Bonus for low cleanup when tired
    if context.fatigue_inferred and recipe.cleanup_effort == 'low':
        bonus += 5

    score += bonus

    return score


def filter_skipped_recipes(db: Session, recipes: List[models.Recipe], days: int = 4) -> List[models.Recipe]:
    """
    Filter out recipes that have been skipped in the last N days.

    Args:
        db: Database session
        recipes: List of recipes to filter
        days: Number of days to look back for skips

    Returns:
        List of recipes not skipped within the specified days
    """
    recent_skips = crud.get_skips_since(db, days=days)
    skipped_recipe_ids = {skip.recipe_id for skip in recent_skips}

    filtered = [r for r in recipes if r.id not in skipped_recipe_ids]

    # If all recipes are suppressed (edge case), reduce suppression to 2 days
    if not filtered and recipes:
        recent_skips = crud.get_skips_since(db, days=2)
        skipped_recipe_ids = {skip.recipe_id for skip in recent_skips}
        filtered = [r for r in recipes if r.id not in skipped_recipe_ids]

    return filtered


def generate_explanation(
    recipe: models.Recipe,
    context: schemas.ContextSignals,
    score: float,
    db: Session
) -> str:
    """
    Generate a human-readable one-liner explaining why this recipe was suggested.

    Args:
        recipe: The recommended recipe
        context: Current context signals
        score: Recipe's calculated score
        db: Database session

    Returns:
        str: Brief explanation (1-2 reasons max)
    """
    reasons = []

    # Recentness reasons
    days_since = crud.get_days_since_last_cooked(db, recipe.id)
    
    # Preference-based reasons
    if recipe.like_score and recipe.like_score >= 4 and days_since is not None:
        reasons.append("you love this")

    # Effort-based reasons
    if recipe.effort_score <= 2:
        reasons.append("quick and easy")

    # Context-aware reasons
    if context.fatigue_inferred and recipe.effort_score <= 2:
        reasons.append("perfect for low energy")

    if days_since and days_since >= 14:
        reasons.append(f"it's been {days_since} days")
    elif days_since is None:
        reasons.append("you haven't tried this yet")

    # Cleanup reasons
    if recipe.cleanup_effort == 'low':
        reasons.append("minimal cleanup")

    # Default if no specific reasons
    if not reasons:
        reasons.append("balanced choice for today")

    # Return max 2 reasons for brevity
    return " • ".join(reasons[:2])


def get_recommendation(
    db: Session,
    excluded_ids: Optional[List[int]] = None,
    current_time: Optional[datetime] = None
) -> schemas.RecommendationResponse:
    """
    Get the best recipe recommendation based on context and scoring algorithm.

    Args:
        db: Database session
        excluded_ids: List of recipe IDs to exclude (for "get another" functionality)
        current_time: Optional override for current time (for testing)

    Returns:
        RecommendationResponse: Recommended recipe with explanation and context

    Raises:
        ValueError: If no recipes are available
    """
    # Get all recipes
    all_recipes = crud.get_recipes(db, limit=1000)

    # Filter out excluded recipes
    if excluded_ids:
        all_recipes = [r for r in all_recipes if r.id not in excluded_ids]

    # Filter out recently skipped recipes (4-day suppression)
    eligible_recipes = filter_skipped_recipes(db, all_recipes, days=4)

    # Filter out planned meals
    planned_meals = crud.get_planned_meals(db, days=14)
    planned_ids = {m.recipe_id for m in planned_meals if m.recipe_id}
    if planned_ids:
        eligible_recipes = [r for r in eligible_recipes if r.id not in planned_ids]

    if not eligible_recipes:
        raise ValueError("No recipes available. All recipes are either excluded, skipped, or already planned.")

    # Get context signals
    context = get_context_signals(db, current_time)

    # Score all eligible recipes
    scored_recipes: List[Tuple[models.Recipe, float]] = []
    for recipe in eligible_recipes:
        score = calculate_recipe_score(recipe, context, db)
        scored_recipes.append((recipe, score))

    # Sort by score (highest first)
    scored_recipes.sort(key=lambda x: x[1], reverse=True)

    # Get the best recipe
    best_recipe, best_score = scored_recipes[0]

    # Update last_suggested_date
    crud.update_recipe_dates(db, best_recipe.id, last_suggested_date=date.today())

    # Generate explanation
    explanation = generate_explanation(best_recipe, context, best_score, db)

    return schemas.RecommendationResponse(
        recipe=best_recipe,
        explanation=explanation,
        context=context
    )
