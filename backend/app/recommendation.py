from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from app import models, schemas, crud


def get_context_signals(
    db: Session,
    user_id: int,
    current_time: Optional[datetime] = None,
) -> schemas.ContextSignals:
    """
    Infer context from current time and recent behaviour for a user.

    Returns:
        ContextSignals: Context information including time of day, fatigue, recent categories
    """
    if current_time is None:
        current_time = datetime.now()

    hour = current_time.hour

    if 5 <= hour < 12:
        time_of_day = 'morning'
    elif 12 <= hour < 17:
        time_of_day = 'afternoon'
    elif 17 <= hour < 22:
        time_of_day = 'evening'
    else:
        time_of_day = 'night'

    is_late = hour >= 21 or hour < 6

    recent_skip_count = crud.count_skips_since(db, user_id=user_id, days=7)
    fatigue_inferred = recent_skip_count >= 3 or is_late

    last_meal = crud.get_last_cooked_meal(db, user_id=user_id)
    last_meal_effort = last_meal.recipe.effort_score if last_meal and last_meal.recipe else 3

    recent_meals = crud.get_recent_meals(db, user_id=user_id, limit=3)
    recent_categories: List[str] = []
    for meal in recent_meals:
        if meal.recipe:
            categories = crud.get_recipe_category_names(db, meal.recipe_id, user_id)
            recent_categories.extend(categories)
    recent_categories = list(dict.fromkeys(recent_categories))

    planned_meals = crud.get_planned_meals(db, user_id=user_id, days=14)
    planned_categories: List[str] = []
    for meal in planned_meals:
        if meal.recipe_id:
            categories = crud.get_recipe_category_names(db, meal.recipe_id, user_id)
            planned_categories.extend(categories)
    planned_categories = list(dict.fromkeys(planned_categories))

    return schemas.ContextSignals(
        time_of_day=time_of_day,
        is_late=is_late,
        recent_skip_count=recent_skip_count,
        fatigue_inferred=fatigue_inferred,
        last_meal_effort=last_meal_effort,
        recent_categories=recent_categories,
        planned_categories=planned_categories,
    )


def calculate_recipe_score(
    recipe: models.Recipe,
    context: schemas.ContextSignals,
    db: Session,
    user_id: int,
) -> float:
    """
    Calculate score for a recipe based on preferences, effort, recentness, and context.

    Scoring formula:
        score = 100 (base)
          + preference_weight (0 to +50)
          - effort_penalty (-50 to 0, amplified if fatigued)
          - recentness_penalty (-40 to 0)
          - category_overlap_penalty (-45 to 0)
          - skip_penalty (-50 to 0)
          + context_bonus (0 to +30)

    Returns:
        float: Score for the recipe (higher is better)
    """
    score = 100.0

    # --- PREFERENCE WEIGHT (0 to +50) ---
    if recipe.like_score:
        score += recipe.like_score * 10
    else:
        score += 25

    # --- EFFORT PENALTY (-50 to 0) ---
    effort_penalty = recipe.effort_score * 10
    if context.fatigue_inferred:
        effort_penalty *= 1.5
    if context.is_late:
        total_time = recipe.prep_time_minutes + recipe.cook_time_minutes
        if total_time > 45:
            effort_penalty += 20
    score -= effort_penalty

    # --- RECENTNESS PENALTY (-40 to 0) ---
    days_since_cooked = crud.get_days_since_last_cooked(db, recipe.id, user_id)
    if days_since_cooked is None:
        recentness_penalty = 0
    elif days_since_cooked < 3:
        recentness_penalty = 40
    elif days_since_cooked < 7:
        recentness_penalty = 25
    elif days_since_cooked < 14:
        recentness_penalty = 10
    else:
        recentness_penalty = 0
    score -= recentness_penalty

    # --- CATEGORY OVERLAP PENALTY (-45 to 0) ---
    recipe_categories = crud.get_recipe_category_names(db, recipe.id, user_id)
    overlap_penalty = 0
    for cat in recipe_categories:
        if cat in context.recent_categories:
            overlap_penalty += 15
        if cat in context.planned_categories:
            overlap_penalty += 15
    score -= min(overlap_penalty, 45)

    # --- SKIP PENALTY (-50 to 0) ---
    score -= min(recipe.skip_count * 5, 50)

    # --- CONTEXT BONUS (0 to +30) ---
    bonus = 0
    if context.fatigue_inferred and recipe.effort_score <= 2:
        bonus += 15
    if context.recent_skip_count == 0 and recipe.like_score == 5:
        bonus += 10
    if context.fatigue_inferred and recipe.cleanup_effort == 'low':
        bonus += 5
    score += bonus

    return score


def filter_skipped_recipes(
    db: Session,
    user_id: int,
    recipes: List[models.Recipe],
    days: int = 4,
) -> List[models.Recipe]:
    """Filter out recipes skipped by the user in the last N days."""
    recent_skips = crud.get_skips_since(db, user_id=user_id, days=days)
    skipped_recipe_ids = {skip.recipe_id for skip in recent_skips}
    filtered = [r for r in recipes if r.id not in skipped_recipe_ids]

    if not filtered and recipes:
        recent_skips = crud.get_skips_since(db, user_id=user_id, days=2)
        skipped_recipe_ids = {skip.recipe_id for skip in recent_skips}
        filtered = [r for r in recipes if r.id not in skipped_recipe_ids]

    return filtered


def generate_explanation(
    recipe: models.Recipe,
    context: schemas.ContextSignals,
    score: float,
    db: Session,
    user_id: int,
) -> str:
    """Generate a human-readable one-liner explaining why this recipe was suggested."""
    reasons: List[str] = []

    days_since = crud.get_days_since_last_cooked(db, recipe.id, user_id)

    if recipe.like_score and recipe.like_score >= 4 and days_since is not None:
        reasons.append("you love this")
    if recipe.effort_score <= 2:
        reasons.append("quick and easy")
    if context.fatigue_inferred and recipe.effort_score <= 2:
        reasons.append("perfect for low energy")
    if days_since and days_since >= 14:
        reasons.append(f"it's been {days_since} days")
    elif days_since is None:
        reasons.append("you haven't tried this yet")
    if recipe.cleanup_effort == 'low':
        reasons.append("minimal cleanup")
    if not reasons:
        reasons.append("balanced choice for today")

    return " • ".join(reasons[:2])


def get_recommendation(
    db: Session,
    user_id: int,
    excluded_ids: Optional[List[int]] = None,
    current_time: Optional[datetime] = None,
) -> schemas.RecommendationResponse:
    """
    Get the best recipe recommendation for a user based on context and scoring.

    Args:
        db: Database session
        user_id: ID of the authenticated user
        excluded_ids: Recipe IDs to exclude (for "get another" functionality)
        current_time: Optional override for testing

    Returns:
        RecommendationResponse: Recommended recipe with explanation and context

    Raises:
        ValueError: If no eligible recipes are available
    """
    all_recipes = crud.get_recipes(db, user_id=user_id, limit=1000)

    if excluded_ids:
        all_recipes = [r for r in all_recipes if r.id not in excluded_ids]

    eligible_recipes = filter_skipped_recipes(db, user_id, all_recipes, days=4)

    planned_meals = crud.get_planned_meals(db, user_id=user_id, days=14)
    planned_ids = {m.recipe_id for m in planned_meals if m.recipe_id}
    if planned_ids:
        eligible_recipes = [r for r in eligible_recipes if r.id not in planned_ids]

    if not eligible_recipes:
        raise ValueError("No recipes available. All recipes are either excluded, skipped, or already planned.")

    context = get_context_signals(db, user_id=user_id, current_time=current_time)

    scored_recipes: List[Tuple[models.Recipe, float]] = [
        (recipe, calculate_recipe_score(recipe, context, db, user_id))
        for recipe in eligible_recipes
    ]
    scored_recipes.sort(key=lambda x: x[1], reverse=True)

    best_recipe, best_score = scored_recipes[0]

    crud.update_recipe_dates(db, best_recipe.id, user_id, last_suggested_date=date.today())

    explanation = generate_explanation(best_recipe, context, best_score, db, user_id)

    return schemas.RecommendationResponse(
        recipe=best_recipe,
        explanation=explanation,
        context=context,
    )
