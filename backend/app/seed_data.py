"""
Seed database with example recipes.

Run this script to populate the database with initial recipes:
    python -m app.seed_data
"""

from app.database import SessionLocal, init_db
from app import crud, models

def seed_database():
    """Populate database with example recipes and categories."""

    # Initialize database
    init_db()

    db = SessionLocal()

    try:
        # Check if recipes already exist
        existing_recipes = crud.get_recipes(db, limit=1)
        if existing_recipes:
            print("Database already contains recipes. Skipping seed.")
            return

        print("Seeding database with example recipes...")

        # Create categories
        categories = {
            'pasta': crud.get_or_create_category(db, 'pasta'),
            'Middle Eastern stew': crud.get_or_create_category(db, 'Middle Eastern stew'),
            'vegetarian': crud.get_or_create_category(db, 'vegetarian'),
            'curry': crud.get_or_create_category(db, 'curry'),
            'Kebabs': crud.get_or_create_category(db, 'Kebabs'),
            'asian': crud.get_or_create_category(db, 'asian'),
            'fast food': crud.get_or_create_category(db, 'fast food'),
            'dairy': crud.get_or_create_category(db, 'dairy'),
            'Mahshi': crud.get_or_create_category(db, 'Mahshi'),
            'rice dish': crud.get_or_create_category(db, 'rice dish'),
        }

        # Recipe data: (name, like_score, effort, prep, cook, cleanup, category_names)
        recipes_data = [

            # Easy & Quick (effort 1–2)
            ("Fried veggies", 4, 2, 10, 10, "low", ["vegetarian"]),
            ("Simple Ablama", 3, 2, 10, 15, "low", ["Middle Eastern stew"]),
            ("Beef burger", 4, 2, 10, 10, "low", ["fast food"]),
            ("Chicken burger", 4, 2, 10, 10, "low", ["fast food"]),
            ("Costco chicken", 3, 1, 2, 10, "low", ["fast food"]),
            ("Veggies Pasta", 4, 2, 10, 15, "low", ["pasta", "vegetarian"]),
            ("Red sauce pasta", 4, 2, 5, 20, "low", ["pasta"]),
            ("Fish in oven", 4, 2, 10, 20, "low", ["Middle Eastern stew"]),
            ("Fried veggies with soup", 3, 2, 10, 15, "low", ["vegetarian"]),


            # Medium Effort (effort 3)
            ("Authentic Ablama", 4, 3, 15, 25, "medium", ["Middle Eastern stew"]),
            ("Chicken shawarma", 5, 3, 20, 25, "medium", ["Kebabs"]),
            ("Boftek", 4, 3, 15, 20, "medium", ["fast food"]),
            ("Bulgur wbandora", 4, 3, 10, 25, "medium", ["vegetarian"]),
            ("Crispy chicken with Chick fil A sauce", 5, 3, 15, 20, "medium", ["fast food"]),
            ("Chicken cashew", 4, 3, 15, 20, "medium", ["asian"]),
            ("Kabab", 5, 3, 20, 20, "medium", ["Kebabs"]),
            ("Korma", 4, 3, 15, 30, "medium", ["curry"]),
            ("Fajitas", 4, 3, 15, 20, "medium", ["fast food"]),
            ("Falafel", 5, 3, 20, 15, "medium", ["vegetarian"]),
            ("Fasolye arida", 4, 3, 15, 30, "medium", ["Middle Eastern stew"]),
            ("Tahini Kafta", 5, 3, 15, 25, "medium", ["Kebabs", "dairy"]),
            ("Red sauce Kafta", 5, 3, 15, 25, "medium", ["Kebabs"]),
            ("Lemon juice kafta", 4, 3, 15, 25, "medium", ["Kebabs"]),
            ("Kima", 4, 3, 15, 20, "medium", ["Middle Eastern stew"]),
            ("Lahme bajin", 5, 3, 20, 15, "medium", ["fast food"]),
            ("Lobye", 4, 3, 15, 30, "medium", ["Middle Eastern stew"]),
            ("Mhamar", 3, 3, 15, 25, "medium", ["vegetarian"]),
            ("Mjadara", 5, 3, 10, 30, "medium", ["vegetarian", "rice dish"]),
            ("Koshary", 5, 3, 20, 30, "medium", ["vegetarian"]),
            ("Mtabaa batenjan", 4, 3, 15, 25, "medium", ["vegetarian"]),
            ("Tahwiset batenjan", 4, 3, 10, 20, "medium", ["vegetarian"]),
            ("Tajin arnabit", 4, 3, 15, 30, "medium", ["vegetarian"]),
            ("Tuna curry", 4, 3, 10, 25, "medium", ["curry"]),
            ("Yellow curry", 4, 3, 15, 30, "medium", ["curry"]),
            ("Thai curries", 5, 3, 15, 30, "medium", ["curry", "asian"]),
            ("Beef shawarma", 5, 3, 20, 25, "medium", ["Kebabs"]),
            ("Baked veggies and beef tray", 4, 3, 15, 30, "medium", ["Middle Eastern stew"]),


            # Higher Effort (effort 4–5)
            ("Bamye", 4, 4, 20, 45, "high", ["Middle Eastern stew"]),
            ("Regular Kabse", 5, 4, 20, 45, "high", ["rice dish"]),
            ("Saudi kabse", 5, 4, 25, 50, "high", ["rice dish"]),
            ("Mahshi kosa", 5, 5, 30, 60, "high", ["Mahshi"]),
            ("Mahshi malfoof", 5, 5, 30, 60, "high", ["Mahshi"]),
            ("Mahshi basal", 4, 5, 30, 60, "high", ["Mahshi"]),
            ("Mash-boos", 4, 4, 20, 45, "high", ["rice dish"]),
            ("Makloba", 5, 4, 25, 45, "high", ["rice dish"]),
            ("Mlokheye", 5, 4, 20, 40, "high", ["Middle Eastern stew"]),
            ("Mnazale", 4, 4, 20, 40, "high", ["Middle Eastern stew"]),
            ("Mograbeye", 5, 4, 20, 45, "high", ["Middle Eastern stew"]),
            ("Spinach stew", 4, 4, 15, 40, "high", ["Middle Eastern stew"]),
            ("Arnabit stew", 4, 4, 20, 40, "high", ["Middle Eastern stew"]),
            ("Bazela stew", 4, 4, 20, 40, "high", ["Middle Eastern stew"]),
            ("Frike", 5, 4, 20, 45, "high", ["rice dish"]),
            ("Mahshe dawaly", 5, 5, 30, 70, "high", ["Mahshi"]),
            ("Lasagna", 5, 5, 30, 60, "high", ["pasta", "dairy"]),
            ("Stroganoff", 4, 4, 15, 35, "high", ["dairy"]),
        ]

        # Create recipes
        for recipe_data in recipes_data:
            name, like_score, effort, prep, cook, cleanup, cat_names = recipe_data

            # Get category IDs
            category_ids = [categories[cat_name].id for cat_name in cat_names]

            # Create recipe
            recipe = models.Recipe(
                name=name,
                like_score=like_score,
                effort_score=effort,
                prep_time_minutes=prep,
                cook_time_minutes=cook,
                cleanup_effort=cleanup
            )

            # Add categories
            recipe.categories = [categories[cat_name] for cat_name in cat_names]

            db.add(recipe)

        db.commit()

        # Count created recipes
        total_recipes = db.query(models.Recipe).count()
        total_categories = db.query(models.Category).count()

        print(f"✅ Successfully seeded database!")
        print(f"   - Created {total_recipes} recipes")
        print(f"   - Created {total_categories} categories")
        print(f"\nYou can now start the application with: uvicorn app.main:app --reload")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
