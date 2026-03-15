# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NextMeal is a **local-first decision-fatigue-friendly cooking assistant** that suggests one meal at a time based on intelligent scoring. It's built with:
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite
- **Deployment**: Docker Compose or manual development servers

**Philosophy**: Minimize user decisions, learn passively from behavior, respect context (time, fatigue, recent meals), and stay simple with local-first data.

## Development Commands

### Docker (Primary Method)
```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Stop services
docker-compose down

# Reset database (removes volume)
docker-compose down -v
```

Frontend runs on http://localhost:8001, backend on http://localhost:8000.

### Manual Development

**Backend:**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed initial data
python -m app.seed_data

# Start development server (with hot reload)
uvicorn app.main:app --reload

# Alternative: run single command for both servers
cd ..
python scripts/run.py
```

Backend runs on http://localhost:8000. API docs: http://localhost:8000/docs

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

Frontend runs on http://localhost:5173 (manual mode).

**Database Operations:**
```bash
cd backend

# Reset database completely
rm nextmeal.db
alembic upgrade head
python -m app.seed_data

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Architecture

### Backend Structure

**Core Modules:**
- `app/main.py` - FastAPI app initialization, CORS configuration, router registration
- `app/models.py` - SQLAlchemy ORM models (Recipe, Category, MealHistory, Skip)
- `app/schemas.py` - Pydantic schemas for request/response validation
- `app/crud.py` - Database operations (create, read, update)
- `app/recommendation.py` - **Core recommendation engine** (scoring algorithm)
- `app/database.py` - Database session management

**Routers (API endpoints):**
- `app/routers/recommendations.py` - `/api/recommendation`, `/api/recommendation/accept`, `/api/recommendation/skip`, `/api/recommendation/another`
- `app/routers/recipes.py` - `/api/recipes`, recipe CRUD operations
- `app/routers/history.py` - `/api/history`, `/api/history/stats`, meal tracking

**Database:**
- SQLite file-based database (`nextmeal.db` or `/data/nextmeal.db` in Docker)
- Alembic for migrations (`alembic/versions/`)

### Data Models

**Recipe:**
- Stores name, like_score (1-5, nullable), effort_score (1-5), prep/cook times, cleanup effort
- Tracks `last_cooked_date`, `last_suggested_date`, `skip_count`
- Many-to-many relationship with Categories

**MealHistory:**
- Logs accepted meals with date, recipe_id, meal_type, cooked flag
- Auto-updates recipe's `last_cooked_date` when logged

**Skip:**
- Records skipped recipes with date and optional reason (`too_much_effort`, `dont_like`)
- Increments recipe's `skip_count`
- Suppresses recipe from recommendations for 4 days (see `filter_skipped_recipes()`)

**Category:**
- Simple name-based categorization (e.g., "pasta", "chicken")
- Used for category spacing logic

### Recommendation Algorithm (`app/recommendation.py`)

**Core Function:** `get_recommendation(db, excluded_ids=None, current_time=None)`

**Process:**
1. Fetch all recipes and filter out:
   - Excluded IDs (for "get another" functionality)
   - Recently skipped recipes (4-day suppression, reduced to 2 days if all recipes suppressed)
2. Gather context signals via `get_context_signals()`:
   - Time of day classification (morning/afternoon/evening/night)
   - Fatigue inference (from recent skips or late hour)
   - Recent categories from last 3 meals
   - Last meal effort score
3. Score each eligible recipe via `calculate_recipe_score()`:
   - Base score: 100
   - Preference weight: +0 to +50 (like_score * 10, or +25 for unrated)
   - Effort penalty: -0 to -50 (effort_score * 10, amplified 1.5x if fatigued, +20 if late and long cook time)
   - Recentness penalty: -0 to -40 (based on days since last cooked)
   - Category overlap penalty: -0 to -30 (if recipe categories match recent meals)
   - Skip penalty: -0 to -50 (skip_count * 5)
   - Context bonus: +0 to +30 (easy meals when fatigued, favorites when consistent, low cleanup when tired)
4. Return highest-scored recipe with human-readable explanation

**Key Behaviors:**
- Skipping a recipe suppresses it for 4 days (configurable in `filter_skipped_recipes()`)
- Skip reasons auto-adjust recipe attributes:
  - `dont_like` decreases like_score by 1
  - `too_much_effort` increases effort penalty (via skip_count)
- Accepting a recipe 3+ times auto-boosts like_score (see `recommendations.py:accept_recommendation`)
- Context is inferred automatically—no user configuration required

### Frontend Structure

**Components:**
- `src/App.jsx` - Main app component, manages recommendation state
- `src/components/RecommendationCard.jsx` - Displays single meal recommendation
- `src/components/ActionButtons.jsx` - Accept, Get Another, Skip buttons
- `src/components/SkipModal.jsx` - Optional skip reason selection
- `src/api/client.js` - API client for backend communication

**State Management:**
- Uses React state (no Redux/Context needed)
- Minimal UI: shows one recommendation at a time
- Three-button interaction model

## Key Principles

### Non-Goals
- No nutrition tracking, shopping lists, meal calendars, social features, cloud sync, or authentication
- No heavy onboarding or configuration required
- Everything runs locally

### Design Philosophy
1. **Minimize decisions**: Show one suggestion, not a list
2. **Learn passively**: No explicit ratings required—learns from accept/skip behavior
3. **Respect context**: Time of day, fatigue signals, and recent meals matter
4. **Simple**: Zero configuration to get value
5. **Local-first**: All data stays on user's computer (SQLite)

### Recommendation Tuning

To adjust recommendation behavior, edit `backend/app/recommendation.py`:
- **Scoring weights**: Modify multipliers in `calculate_recipe_score()` (e.g., change preference weight from 10 to 15)
- **Skip suppression duration**: Change `days=4` parameter in `filter_skipped_recipes()`
- **Fatigue inference**: Adjust `recent_skip_count >= 3` threshold in `get_context_signals()`
- **Context bonuses**: Modify bonus logic in `calculate_recipe_score()`

### Common Modifications

**Adding new recipe fields:**
1. Update `app/models.py` (Recipe model)
2. Update `app/schemas.py` (RecipeCreate, RecipeResponse)
3. Create Alembic migration: `alembic revision --autogenerate -m "add field"`
4. Apply migration: `alembic upgrade head`
5. Update scoring logic in `app/recommendation.py` if needed

**Changing API behavior:**
- Modify routers in `app/routers/`
- CORS origins configured in `app/main.py` (update for production deployment)

**UI customization:**
- Edit `frontend/src/App.css` for styling
- Modify component files in `frontend/src/components/`

## Testing Notes

- No formal test suite currently
- Test recommendations by seeding data and observing behavior over time
- API can be tested via Swagger UI: http://localhost:8000/docs
- Database can be inspected directly (it's SQLite): `sqlite3 backend/nextmeal.db`
