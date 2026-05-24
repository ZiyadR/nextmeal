"""
Seed database with the global category/recipe pool.

These records have user_id=NULL and act as templates.
When a new user registers, seed_categories_for_user() copies them
into the user's own category list.

Run:
    python -m app.seed_data
"""

from app.database import SessionLocal
from app import models
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Seed categories (user_id=NULL → shared seed pool)
# ---------------------------------------------------------------------------
SEED_CATEGORIES = [
    'pasta',
    'Middle Eastern stew',
    'vegetarian',
    'curry',
    'Kebabs',
    'asian',
    'fast food',
    'dairy',
    'Mahshi',
    'rice dish',
]

# (name, like_score, effort, prep_min, cook_min, cleanup, [category_names])
SEED_RECIPES = [
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


def _get_or_create_seed_category(db: Session, name: str) -> models.Category:
    """Get or create a global seed category (user_id=NULL)."""
    cat = db.query(models.Category).filter(
        models.Category.name == name,
        models.Category.user_id == None,  # noqa: E711
    ).first()
    if not cat:
        cat = models.Category(name=name, user_id=None)
        db.add(cat)
        db.flush()
    return cat


def seed_database() -> None:
    """Populate the database with the global seed pool (user_id=NULL records)."""
    db = SessionLocal()
    try:
        # Check if seed data already exists
        existing = db.query(models.Recipe).filter(models.Recipe.user_id == None).first()  # noqa: E711
        if existing:
            print("Seed data already present. Skipping.")
            return

        print("Seeding global recipe/category pool…")

        # Create seed categories
        cat_map = {name: _get_or_create_seed_category(db, name) for name in SEED_CATEGORIES}
        db.flush()

        # Create seed recipes (user_id=NULL)
        for name, like_score, effort, prep, cook, cleanup, cat_names in SEED_RECIPES:
            recipe = models.Recipe(
                name=name,
                like_score=like_score,
                effort_score=effort,
                prep_time_minutes=prep,
                cook_time_minutes=cook,
                cleanup_effort=cleanup,
                user_id=None,
            )
            recipe.categories = [cat_map[c] for c in cat_names]
            db.add(recipe)

        db.commit()

        total_recipes = db.query(models.Recipe).filter(models.Recipe.user_id == None).count()  # noqa: E711
        total_cats = db.query(models.Category).filter(models.Category.user_id == None).count()  # noqa: E711
        print(f"✅ Seeded {total_recipes} recipes and {total_cats} categories.")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
