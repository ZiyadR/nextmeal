from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from app import schemas, crud, csv_utils, models
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()


@router.get("/recipes", response_model=schemas.PaginatedRecipes)
def list_recipes(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all recipes for the authenticated user with optional filtering and pagination."""
    skip = (page - 1) * limit
    recipes = crud.get_recipes(db, user_id=current_user.id, skip=skip, limit=limit, category_id=category_id)

    total_query = db.query(models.Recipe).filter(models.Recipe.user_id == current_user.id)
    if category_id:
        total_query = total_query.join(models.Recipe.categories).filter(
            models.Category.id == category_id
        )
    total = total_query.count()

    return schemas.PaginatedRecipes(recipes=recipes, total=total, page=page, limit=limit)


@router.get("/recipes/{recipe_id}", response_model=schemas.Recipe)
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get a specific recipe owned by the authenticated user."""
    recipe = crud.get_recipe(db, recipe_id, current_user.id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/recipes", response_model=schemas.Recipe)
def create_recipe(
    recipe: schemas.RecipeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new recipe for the authenticated user."""
    try:
        return crud.create_recipe(db, recipe, user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating recipe: {str(e)}")


@router.get("/categories", response_model=list[schemas.Category])
def list_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all categories for the authenticated user."""
    return crud.get_categories(db, user_id=current_user.id)


@router.put("/recipes/{recipe_id}", response_model=schemas.Recipe)
def update_recipe(
    recipe_id: int,
    recipe_update: schemas.RecipeUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update an existing recipe owned by the authenticated user (partial update)."""
    updated_recipe = crud.update_recipe(db, recipe_id, current_user.id, recipe_update)
    if not updated_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return updated_recipe


@router.delete("/recipes/{recipe_id}", response_model=schemas.DeleteRecipeResponse)
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a recipe owned by the authenticated user."""
    result = crud.delete_recipe(db, recipe_id, current_user.id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])

    return schemas.DeleteRecipeResponse(
        success=result["success"],
        message=result["message"],
        recipe_id=recipe_id,
        meal_history_affected=result["meal_history_affected"],
    )


@router.get("/recipes/search/{query}", response_model=list[schemas.Recipe])
def search_recipes(
    query: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Search recipes by name (case-insensitive), scoped to the authenticated user."""
    skip = (page - 1) * limit
    return crud.search_recipes(db, user_id=current_user.id, query=query, skip=skip, limit=limit)


@router.post("/recipes/import", response_model=schemas.ImportResult)
async def import_recipes(
    file: UploadFile = File(...),
    update_existing: bool = Query(True, description="Update existing recipes with same name"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Import recipes from a CSV file into the authenticated user's recipe list."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        result = csv_utils.import_recipes_from_csv(db, csv_content, update_existing, user_id=current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/recipes/export")
def export_recipes(
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Export the authenticated user's recipes to a CSV file."""
    try:
        if category_id:
            recipes = crud.get_recipes(db, user_id=current_user.id, category_id=category_id, limit=10000)
            recipe_ids = [r.id for r in recipes]
        else:
            recipe_ids = None

        csv_content = csv_utils.export_recipes_to_csv(db, recipe_ids)

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=recipes.csv"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/categories", response_model=schemas.Category)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new category for the authenticated user, or return an existing one."""
    return crud.get_or_create_category(db, category.name, user_id=current_user.id)


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a category owned by the authenticated user."""
    success = crud.delete_category(db, category_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True, "message": "Category deleted"}
