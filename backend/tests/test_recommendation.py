import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch

from app import recommendation, schemas, models

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_recipe():
    recipe = models.Recipe(
        id=1,
        name="Test Recipe",
        like_score=4,
        effort_score=2,
        prep_time_minutes=10,
        cook_time_minutes=20,
        cleanup_effort='low',
        skip_count=0
    )
    return recipe

def test_get_context_signals_morning_no_fatigue(mock_db, mocker):
    mocker.patch('app.crud.count_skips_since', return_value=0)
    mocker.patch('app.crud.get_last_cooked_meal', return_value=Mock(recipe=Mock(effort_score=3)))
    mocker.patch('app.crud.get_recent_meals', return_value=[])
    mocker.patch('app.crud.get_planned_meals', return_value=[])
    
    current_time = datetime(2023, 1, 1, 9, 0, 0)
    signals = recommendation.get_context_signals(mock_db, current_time=current_time)
    
    assert signals.time_of_day == 'morning'
    assert not signals.is_late
    assert signals.recent_skip_count == 0
    assert not signals.fatigue_inferred
    assert signals.recent_categories == []
    assert signals.planned_categories == []

def test_get_context_signals_late_fatigue_and_planned(mock_db, mocker):
    mocker.patch('app.crud.count_skips_since', return_value=0)
    mocker.patch('app.crud.get_last_cooked_meal', return_value=Mock(recipe=Mock(effort_score=3)))
    mocker.patch('app.crud.get_recent_meals', return_value=[])
    
    planned_meal = Mock(recipe_id=1)
    mocker.patch('app.crud.get_planned_meals', return_value=[planned_meal])
    mocker.patch('app.crud.get_recipe_category_names', return_value=["Italian"])

    current_time = datetime(2023, 1, 1, 23, 0, 0)
    signals = recommendation.get_context_signals(mock_db, current_time=current_time)
    
    assert signals.time_of_day == 'night'
    assert signals.is_late
    assert signals.fatigue_inferred
    assert signals.planned_categories == ["Italian"]

def test_calculate_recipe_score_baseline(mock_db, mock_recipe, mocker):
    context = schemas.ContextSignals(
        time_of_day='evening',
        is_late=False,
        recent_skip_count=0,
        fatigue_inferred=False,
        last_meal_effort=3,
        recent_categories=[],
        planned_categories=[]
    )
    
    mocker.patch('app.crud.get_days_since_last_cooked', return_value=None)
    mocker.patch('app.crud.get_recipe_category_names', return_value=[])
    
    score = recommendation.calculate_recipe_score(mock_recipe, context, mock_db)
    
    # Base: 100
    # Like (4): +40
    # Effort (2): -20
    # Recentness: -0 (never cooked)
    # Overlap: -0
    # Skip: -0
    # Context Bonus: 0
    # Total = 100 + 40 - 20 = 120
    assert score == 120.0

def test_calculate_recipe_score_penalties(mock_db, mock_recipe, mocker):
    context = schemas.ContextSignals(
        time_of_day='evening',
        is_late=False,
        recent_skip_count=0,
        fatigue_inferred=False,
        last_meal_effort=3,
        recent_categories=["Pasta"],
        planned_categories=["Italian"]
    )
    
    # Setup recipe to be recently cooked and have category overlap
    mock_recipe.skip_count = 2
    mocker.patch('app.crud.get_days_since_last_cooked', return_value=2)
    mocker.patch('app.crud.get_recipe_category_names', return_value=["Pasta", "Italian"])
    
    score = recommendation.calculate_recipe_score(mock_recipe, context, mock_db)
    
    # Base: 100
    # Like (4): +40
    # Effort (2): -20
    # Recentness (2 days): -40
    # Overlap (Pasta + Italian): -30 (15+15)
    # Skip (2 skips): -10
    # Total = 100 + 40 - 20 - 40 - 30 - 10 = 40
    assert score == 40.0

def test_filter_skipped_recipes(mock_db, mock_recipe, mocker):
    recipe1 = models.Recipe(id=1, name="R1")
    recipe2 = models.Recipe(id=2, name="R2")
    recipe3 = models.Recipe(id=3, name="R3")
    
    # Recipe 2 was skipped recently
    mocker.patch('app.crud.get_skips_since', return_value=[Mock(recipe_id=2)])
    
    filtered = recommendation.filter_skipped_recipes(mock_db, [recipe1, recipe2, recipe3], days=4)
    assert len(filtered) == 2
    assert recipe1 in filtered
    assert recipe3 in filtered

def test_generate_explanation_fatigue_and_easy(mock_db, mock_recipe, mocker):
    context = schemas.ContextSignals(
        time_of_day='evening',
        is_late=False,
        recent_skip_count=0,
        fatigue_inferred=True,
        last_meal_effort=3,
        recent_categories=[],
        planned_categories=[]
    )
    
    # Effort is 2, Like is 4
    mocker.patch('app.crud.get_days_since_last_cooked', return_value=20)
    
    explanation = recommendation.generate_explanation(mock_recipe, context, 120.0, mock_db)
    assert "you love this" in explanation
    assert "quick and easy" in explanation
    
def test_get_recommendation(mock_db, mocker):
    now = datetime.utcnow()
    recipe1 = models.Recipe(id=1, name="R1", like_score=5, effort_score=1, skip_count=0, cleanup_effort='low', prep_time_minutes=10, cook_time_minutes=20, created_at=now, updated_at=now)
    recipe2 = models.Recipe(id=2, name="R2", like_score=1, effort_score=5, skip_count=0, cleanup_effort='high', prep_time_minutes=10, cook_time_minutes=20, created_at=now, updated_at=now)
    
    mocker.patch('app.crud.get_recipes', return_value=[recipe1, recipe2])
    mocker.patch('app.crud.get_skips_since', return_value=[])
    mocker.patch('app.crud.get_planned_meals', return_value=[])
    
    context = schemas.ContextSignals(
        time_of_day='evening',
        is_late=False,
        recent_skip_count=0,
        fatigue_inferred=False,
        last_meal_effort=3,
        recent_categories=[],
        planned_categories=[]
    )
    mocker.patch('app.recommendation.get_context_signals', return_value=context)
    mocker.patch('app.crud.get_days_since_last_cooked', return_value=None)
    mocker.patch('app.crud.get_recipe_category_names', return_value=[])
    mocker.patch('app.crud.update_recipe_dates')
    mocker.patch('app.recommendation.generate_explanation', return_value="Explanation")
    
    # Exclude recipe 1 intentionally
    response = recommendation.get_recommendation(mock_db, excluded_ids=[1])
    
    # Only R2 should be recommended
    assert response.recipe.id == 2
    assert response.explanation == "Explanation"
