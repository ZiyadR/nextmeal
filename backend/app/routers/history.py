from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app import schemas, crud
from app.database import get_db

router = APIRouter()


@router.get("/history", response_model=list[schemas.MealHistory])
def get_meal_history(
    limit: int = Query(50, ge=1, le=200),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get meal history with optional date filtering.

    Args:
        limit: Maximum number of entries to return (default: 50, max: 200)
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List[MealHistory]: Meal history entries
    """
    try:
        return crud.get_meal_history(db, limit=limit, start_date=start_date, end_date=end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching meal history: {str(e)}")


@router.get("/history/stats", response_model=schemas.CookingStats)
def get_cooking_stats(db: Session = Depends(get_db)):
    """
    Get cooking statistics.

    Returns:
        CookingStats: Statistics about cooking history
    """
    try:
        stats = crud.get_cooking_stats(db)
        return schemas.CookingStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cooking stats: {str(e)}")


@router.post("/history", response_model=schemas.MealHistory)
def add_meal_history(
    meal_data: schemas.MealHistoryCreate,
    db: Session = Depends(get_db)
):
    """
    Manually add a meal history entry.

    Args:
        meal_data: Meal history data (date, recipe_id, meal_type, cooked)

    Returns:
        MealHistory: Created meal history entry
    """
    try:
        # Validate that recipe exists if recipe_id is provided
        if meal_data.recipe_id:
            recipe = crud.get_recipe(db, meal_data.recipe_id)
            if not recipe:
                raise HTTPException(status_code=404, detail=f"Recipe with ID {meal_data.recipe_id} not found")

        meal = crud.create_meal_history(
            db=db,
            recipe_id=meal_data.recipe_id,
            meal_date=meal_data.date,
            meal_type=meal_data.meal_type,
            cooked=meal_data.cooked
        )
        return meal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating meal history: {str(e)}")


@router.get("/history/planned", response_model=list[schemas.MealHistory])
def get_planned_meals(db: Session = Depends(get_db)):
    """
    Get planned (not yet cooked) meals for the next 7 days.
    """
    try:
        return crud.get_planned_meals(db, days=7)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching planned meals: {str(e)}")


@router.delete("/history/{meal_id}", response_model=schemas.DeleteMealHistoryResponse)
def delete_planned_meal(meal_id: int, db: Session = Depends(get_db)):
    """
    Delete a planned meal. Only allows deleting future/today entries that haven't been cooked.
    """
    try:
        success = crud.delete_meal_history(db, meal_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete: meal not found, already cooked, or in the past"
            )
        return schemas.DeleteMealHistoryResponse(
            success=True,
            message="Planned meal removed"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting planned meal: {str(e)}")
