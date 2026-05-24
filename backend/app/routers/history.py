from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app import schemas, crud, models
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()


@router.get("/history", response_model=list[schemas.MealHistory])
def get_meal_history(
    limit: int = Query(50, ge=1, le=200),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get meal history for the authenticated user with optional date filtering."""
    try:
        return crud.get_meal_history(
            db, user_id=current_user.id, limit=limit, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching meal history: {str(e)}")


@router.get("/history/stats", response_model=schemas.CookingStats)
def get_cooking_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get cooking statistics for the authenticated user."""
    try:
        stats = crud.get_cooking_stats(db, user_id=current_user.id)
        return schemas.CookingStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cooking stats: {str(e)}")


@router.post("/history", response_model=schemas.MealHistory)
def add_meal_history(
    meal_data: schemas.MealHistoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Manually add a meal history entry for the authenticated user."""
    try:
        if meal_data.recipe_id:
            recipe = crud.get_recipe(db, meal_data.recipe_id, current_user.id)
            if not recipe:
                raise HTTPException(status_code=404, detail=f"Recipe with ID {meal_data.recipe_id} not found")

        meal = crud.create_meal_history(
            db=db,
            user_id=current_user.id,
            recipe_id=meal_data.recipe_id,
            meal_date=meal_data.date,
            meal_type=meal_data.meal_type,
            cooked=meal_data.cooked,
        )
        return meal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating meal history: {str(e)}")


@router.get("/history/planned", response_model=list[schemas.MealHistory])
def get_planned_meals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get planned (not yet cooked) meals for the authenticated user for the next 7 days."""
    try:
        return crud.get_planned_meals(db, user_id=current_user.id, days=7)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching planned meals: {str(e)}")


@router.delete("/history/{meal_id}", response_model=schemas.DeleteMealHistoryResponse)
def delete_planned_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a planned meal owned by the authenticated user."""
    try:
        success = crud.delete_meal_history(db, meal_id, user_id=current_user.id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete: meal not found, already cooked, or in the past",
            )
        return schemas.DeleteMealHistoryResponse(success=True, message="Planned meal removed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting planned meal: {str(e)}")
