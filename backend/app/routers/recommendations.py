from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app import schemas, crud, recommendation, models
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()


@router.get("/recommendation", response_model=schemas.RecommendationResponse)
def get_recommendation_endpoint(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get one recommended meal based on context and preferences."""
    try:
        return recommendation.get_recommendation(db, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendation: {str(e)}")


@router.post("/recommendation/accept", response_model=schemas.AcceptResponse)
def accept_recommendation(
    request: schemas.AcceptRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Accept the current recommendation and log it to meal history."""
    try:
        meal = crud.create_meal_history(
            db,
            user_id=current_user.id,
            recipe_id=request.recipe_id,
            meal_date=date.today(),
            meal_type=request.meal_type,
            cooked=True,
        )

        recipe = crud.get_recipe(db, request.recipe_id, current_user.id)
        if recipe:
            history_count = (
                db.query(models.MealHistory)
                .filter(
                    models.MealHistory.recipe_id == request.recipe_id,
                    models.MealHistory.user_id == current_user.id,
                    models.MealHistory.cooked == True,
                )
                .count()
            )
            if history_count >= 3 and (not recipe.like_score or recipe.like_score < 5):
                new_score = min((recipe.like_score or 3) + 1, 5)
                crud.update_like_score(db, request.recipe_id, current_user.id, new_score)

        try:
            next_rec = recommendation.get_recommendation(db, user_id=current_user.id)
        except Exception:
            next_rec = None

        return schemas.AcceptResponse(
            success=True,
            meal_history_id=meal.id,
            next_recommendation=next_rec,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accepting recommendation: {str(e)}")


@router.post("/recommendation/skip", response_model=schemas.SkipResponse)
def skip_recommendation(
    request: schemas.SkipRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Skip the current recommendation (suppresses it for 4 days)."""
    try:
        crud.record_skip(
            db,
            user_id=current_user.id,
            recipe_id=request.recipe_id,
            skipped_date=date.today(),
            reason=request.reason,
        )

        next_rec = recommendation.get_recommendation(
            db, user_id=current_user.id, excluded_ids=[request.recipe_id]
        )

        return schemas.SkipResponse(success=True, next_suggestion=next_rec)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error skipping recommendation: {str(e)}")


@router.post("/recommendation/another", response_model=schemas.RecommendationResponse)
def get_another_recommendation(
    request: schemas.AnotherRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get another suggestion, excluding specified recipe IDs."""
    try:
        return recommendation.get_recommendation(
            db, user_id=current_user.id, excluded_ids=request.excluded_recipe_ids
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting another recommendation: {str(e)}")
