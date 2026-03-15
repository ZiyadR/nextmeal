from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from app import schemas, crud, csv_utils, models
from app.database import get_db

router = APIRouter()


@router.get("/recipes", response_model=schemas.PaginatedRecipes)
def list_recipes(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    List all recipes with optional filtering and pagination.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 50, max: 100)
        category_id: Optional category ID to filter by

    Returns:
        PaginatedRecipes: List of recipes with pagination info
    """
    skip = (page - 1) * limit
    recipes = crud.get_recipes(db, skip=skip, limit=limit, category_id=category_id)

    # Get total count for pagination
    total_query = db.query(models.Recipe)
    if category_id:
        total_query = total_query.join(models.Recipe.categories).filter(
            models.Category.id == category_id
        )
    total = total_query.count()

    return schemas.PaginatedRecipes(
        recipes=recipes,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/recipes/{recipe_id}", response_model=schemas.Recipe)
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific recipe by ID.

    Args:
        recipe_id: Recipe ID

    Returns:
        Recipe: Recipe details
    """
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/recipes", response_model=schemas.Recipe)
def create_recipe(
    recipe: schemas.RecipeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new recipe.

    Args:
        recipe: Recipe data

    Returns:
        Recipe: Created recipe
    """
    try:
        return crud.create_recipe(db, recipe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating recipe: {str(e)}")


@router.get("/categories", response_model=list[schemas.Category])
def list_categories(db: Session = Depends(get_db)):
    """
    List all categories.

    Returns:
        List[Category]: All categories
    """
    return crud.get_categories(db)


@router.put("/recipes/{recipe_id}", response_model=schemas.Recipe)
def update_recipe(
    recipe_id: int,
    recipe_update: schemas.RecipeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing recipe (partial update).

    Args:
        recipe_id: Recipe ID
        recipe_update: Fields to update

    Returns:
        Recipe: Updated recipe
    """
    updated_recipe = crud.update_recipe(db, recipe_id, recipe_update)
    if not updated_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return updated_recipe


@router.delete("/recipes/{recipe_id}", response_model=schemas.DeleteRecipeResponse)
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a recipe.

    Note:
    - Meal history entries will have recipe_id set to NULL (preserves history)
    - Skip entries will be deleted (CASCADE)

    Args:
        recipe_id: Recipe ID to delete

    Returns:
        DeleteRecipeResponse: Deletion result with affected records count
    """
    result = crud.delete_recipe(db, recipe_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])

    return schemas.DeleteRecipeResponse(
        success=result["success"],
        message=result["message"],
        recipe_id=recipe_id,
        meal_history_affected=result["meal_history_affected"]
    )


@router.get("/recipes/search/{query}", response_model=list[schemas.Recipe])
def search_recipes(
    query: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search recipes by name (case-insensitive).

    Args:
        query: Search query string
        page: Page number
        limit: Results per page

    Returns:
        List[Recipe]: Matching recipes
    """
    skip = (page - 1) * limit
    return crud.search_recipes(db, query=query, skip=skip, limit=limit)


@router.post("/recipes/import", response_model=schemas.ImportResult)
async def import_recipes(
    file: UploadFile = File(...),
    update_existing: bool = Query(True, description="Update existing recipes with same name"),
    db: Session = Depends(get_db)
):
    """
    Import recipes from CSV file.

    CSV format:
    - name, like_score, effort_score, prep_time_minutes, cook_time_minutes, cleanup_effort, categories
    - Categories should be pipe-separated (e.g., "Italian|Pasta|Quick")

    Args:
        file: CSV file
        update_existing: If True, updates existing recipes; if False, skips duplicates

    Returns:
        ImportResult: Import statistics and errors
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        result = csv_utils.import_recipes_from_csv(db, csv_content, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/recipes/export")
def export_recipes(
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Export recipes to CSV file.

    Args:
        category_id: Optional category ID to filter by

    Returns:
        CSV file download
    """
    try:
        # Get recipe IDs based on filter
        if category_id:
            recipes = crud.get_recipes(db, category_id=category_id, limit=10000)
            recipe_ids = [r.id for r in recipes]
        else:
            recipe_ids = None

        csv_content = csv_utils.export_recipes_to_csv(db, recipe_ids)

        # Return as downloadable file
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=recipes.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/categories", response_model=schemas.Category)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new category or return existing one.

    Args:
        category: Category data

    Returns:
        Category: Created or existing category
    """
    return crud.get_or_create_category(db, category.name)


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a category. Removes category from all associated recipes.

    Args:
        category_id: Category ID

    Returns:
        Success message
    """
    success = crud.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True, "message": "Category deleted"}
