"""CSV import/export utilities for recipes."""
import csv
from io import StringIO
from typing import List
from sqlalchemy.orm import Session
from app import models, schemas, crud


def parse_csv_categories(categories_str: str) -> List[str]:
    """Parse pipe-separated category names."""
    if not categories_str:
        return []
    return [cat.strip() for cat in categories_str.split('|') if cat.strip()]


def import_recipes_from_csv(
    db: Session,
    csv_content: str,
    update_existing: bool = True
) -> schemas.ImportResult:
    """
    Import recipes from CSV content.

    Args:
        db: Database session
        csv_content: CSV file content as string
        update_existing: If True, update recipes with duplicate names

    Returns:
        ImportResult with counts and errors
    """
    reader = csv.DictReader(StringIO(csv_content))

    imported = 0
    updated = 0
    skipped = 0
    errors = []
    total = 0

    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
        total += 1

        try:
            # Parse categories and get/create them
            category_names = parse_csv_categories(row.get('categories', ''))
            categories = []
            for cat_name in category_names:
                category = crud.get_or_create_category(db, cat_name)
                categories.append(category)

            # Check if recipe exists
            existing_recipe = crud.get_recipe_by_name(db, row['name'])

            if existing_recipe:
                if update_existing:
                    # Update existing recipe
                    update_data = schemas.RecipeUpdate(
                        name=row['name'],
                        like_score=int(row['like_score']) if row.get('like_score') and row['like_score'] else None,
                        effort_score=int(row['effort_score']),
                        prep_time_minutes=int(row.get('prep_time_minutes', 0)),
                        cook_time_minutes=int(row.get('cook_time_minutes', 0)),
                        cleanup_effort=row.get('cleanup_effort', 'medium'),
                        category_ids=[cat.id for cat in categories]
                    )
                    crud.update_recipe(db, existing_recipe.id, update_data)
                    updated += 1
                else:
                    skipped += 1
                    errors.append({
                        'row': row_num,
                        'error': f"Recipe '{row['name']}' already exists (skipped)"
                    })
            else:
                # Create new recipe
                recipe_data = schemas.RecipeCreate(
                    name=row['name'],
                    like_score=int(row['like_score']) if row.get('like_score') and row['like_score'] else None,
                    effort_score=int(row['effort_score']),
                    prep_time_minutes=int(row.get('prep_time_minutes', 0)),
                    cook_time_minutes=int(row.get('cook_time_minutes', 0)),
                    cleanup_effort=row.get('cleanup_effort', 'medium'),
                    category_ids=[cat.id for cat in categories]
                )
                crud.create_recipe(db, recipe_data)
                imported += 1

        except Exception as e:
            errors.append({
                'row': row_num,
                'error': str(e)
            })
            skipped += 1

    return schemas.ImportResult(
        success=True,
        total_rows=total,
        imported_count=imported,
        updated_count=updated,
        skipped_count=skipped,
        errors=errors
    )


def export_recipes_to_csv(db: Session, recipe_ids: List[int] = None) -> str:
    """
    Export recipes to CSV format.

    Args:
        db: Database session
        recipe_ids: Optional list of specific recipe IDs to export. If None, exports all.

    Returns:
        CSV content as string
    """
    if recipe_ids:
        recipes = [crud.get_recipe(db, rid) for rid in recipe_ids if crud.get_recipe(db, rid)]
    else:
        recipes = crud.get_recipes(db, limit=10000)  # Export all

    output = StringIO()
    fieldnames = [
        'name', 'like_score', 'effort_score',
        'prep_time_minutes', 'cook_time_minutes',
        'cleanup_effort', 'categories'
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for recipe in recipes:
        category_names = [cat.name for cat in recipe.categories]
        writer.writerow({
            'name': recipe.name,
            'like_score': recipe.like_score or '',
            'effort_score': recipe.effort_score,
            'prep_time_minutes': recipe.prep_time_minutes,
            'cook_time_minutes': recipe.cook_time_minutes,
            'cleanup_effort': recipe.cleanup_effort,
            'categories': '|'.join(category_names)
        })

    return output.getvalue()
