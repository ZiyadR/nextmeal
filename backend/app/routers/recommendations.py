from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app import schemas, crud, recommendation, models
from app.database import get_db

router = APIRouter()


@router.get("/recommendation", response_model=schemas.RecommendationResponse)
def get_recommendation_endpoint(db: Session = Depends(get_db)):
    """
    Get one recommended meal based on context and preferences.

    Returns:
        RecommendationResponse: Recommended recipe with explanation and context
    """
    try:
        return recommendation.get_recommendation(db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendation: {str(e)}")


@router.post("/recommendation/accept", response_model=schemas.AcceptResponse)
def accept_recommendation(
    request: schemas.AcceptRequest,
    db: Session = Depends(get_db)
):
    """
    Accept the current recommendation and log it to meal history.

    Args:
        request: AcceptRequest with recipe_id and optional meal_type

    Returns:
        AcceptResponse: Success status, meal history ID, and next recommendation
    """
    try:
        # Create meal history entry
        meal = crud.create_meal_history(
            db,
            recipe_id=request.recipe_id,
            meal_date=date.today(),
            meal_type=request.meal_type,
            cooked=True
        )

        # Optionally auto-boost like_score for frequently accepted recipes
        recipe = crud.get_recipe(db, request.recipe_id)
        if recipe:
            # Count how many times this recipe has been cooked
            history_count = db.query(models.MealHistory).filter(
                models.MealHistory.recipe_id == request.recipe_id,
                models.MealHistory.cooked == True
            ).count()

            # If cooked 3+ times and not yet rated 5, increase like_score
            if history_count >= 3 and (not recipe.like_score or recipe.like_score < 5):
                new_score = min((recipe.like_score or 3) + 1, 5)
                crud.update_like_score(db, request.recipe_id, new_score)

        # Get next recommendation
        try:
            next_rec = recommendation.get_recommendation(db)
        except:
            next_rec = None

        return schemas.AcceptResponse(
            success=True,
            meal_history_id=meal.id,
            next_recommendation=next_rec
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accepting recommendation: {str(e)}")


@router.post("/recommendation/skip", response_model=schemas.SkipResponse)
def skip_recommendation(
    request: schemas.SkipRequest,
    db: Session = Depends(get_db)
):
    """
    Skip the current recommendation (suppresses it for 4 days).

    Args:
        request: SkipRequest with recipe_id and optional reason

    Returns:
        SkipResponse: Success status and next suggestion
    """
    try:
        # Record the skip
        crud.record_skip(
            db,
            recipe_id=request.recipe_id,
            skipped_date=date.today(),
            reason=request.reason
        )

        # Get next suggestion (excluding the skipped recipe)
        next_rec = recommendation.get_recommendation(db, excluded_ids=[request.recipe_id])

        return schemas.SkipResponse(
            success=True,
            next_suggestion=next_rec
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error skipping recommendation: {str(e)}")


@router.post("/recommendation/another", response_model=schemas.RecommendationResponse)
def get_another_recommendation(
    request: schemas.AnotherRequest,
    db: Session = Depends(get_db)
):
    """
    Get another suggestion, excluding specified recipe IDs.

    Args:
        request: AnotherRequest with list of recipe IDs to exclude

    Returns:
        RecommendationResponse: Different recommended recipe
    """
    try:
        return recommendation.get_recommendation(db, excluded_ids=request.excluded_recipe_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting another recommendation: {str(e)}")
