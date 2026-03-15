# NextMeal - Your Local Cooking Assistant

A local-first, decision-fatigue-friendly cooking assistant that suggests what to cook based on your preferences, effort tolerance, meal history, and context.

## Features

- **Smart Recommendations**: Get one meal suggestion at a time based on intelligent scoring
- **Context-Aware**: Considers time of day, recent skips, category spacing, and fatigue
- **Zero Configuration**: Works out of the box with sensible defaults
- **Local-First**: All data stays on your computer, no cloud sync
- **Minimal UI**: Just 3 buttons - Accept, Get Another, Skip
- **Learning System**: Adapts to your preferences over time

## Quick Start

### Option 1: Docker (Recommended)

The easiest way to run NextMeal is with Docker:

#### Prerequisites
- **Docker** and **Docker Compose** installed

#### Run with Docker
```bash
# Clone the repository
git clone <repo-url>
cd nextmeal

# Start the application
docker-compose up -d

# Open browser to http://localhost
```

That's it! The app will be running at **http://localhost**

#### Docker Commands
```bash
# Start the app
docker-compose up -d

# Stop the app
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Reset database (remove volume)
docker-compose down -v
docker-compose up -d
```

---

### Option 2: Manual Installation

#### Prerequisites

- **Python 3.9+** (3.11 recommended)
- **Node.js 18+**
- **pip** and **npm**

#### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd nextmeal
   ```

2. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Initialize database**
   ```bash
   alembic upgrade head
   python -m app.seed_data
   ```

4. **Install frontend dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Run the app**
   ```bash
   cd ..
   python scripts/run.py
   ```

6. **Open browser**
   Navigate to **http://localhost:5173**

That's it! 🎉

## Usage

### Main Flow

1. App shows **one recommended meal**
2. You can:
   - **Accept** - Cook this meal (logs to history)
   - **Get Another** - See a different suggestion
   - **Skip** - Skip this recipe (suppressed for 4 days)
3. App learns from your behavior over time

### How Recommendations Work

The app uses a scoring algorithm that considers:

- **Preference**: Recipes you've cooked and liked score higher
- **Effort**: Lower effort when you're tired (inferred from skips or late hour)
- **Recentness**: Recipes you haven't cooked in a while score higher
- **Category Spacing**: Avoids suggesting pasta 3 days in a row
- **Skip Behavior**: Frequently skipped recipes score lower
- **Context**: Time of day, recent activity, fatigue signals

### Skip Behavior

- Skipping a recipe suppresses it for **4 days**
- You can optionally provide a reason:
  - **Too much effort** - Increases effort penalty for this recipe
  - **Don't like anymore** - Decreases preference score

### Automatic Learning

- **Accepting recipes** increases their preference score over time
- **Frequently skipping** decreases their weight
- **Category spacing** is handled automatically
- No manual configuration needed!

## Manual Commands

If you prefer running backend and frontend separately:

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Project Structure

```
nextmeal/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # Database models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── crud.py              # Database operations
│   │   ├── recommendation.py    # Core recommendation engine
│   │   ├── routers/             # API endpoints
│   │   └── seed_data.py         # Example recipes
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile               # Backend Docker image
│   ├── .dockerignore
│   └── nextmeal.db             # SQLite database (auto-created)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app component
│   │   ├── components/          # React components
│   │   └── api/                 # API client
│   ├── package.json
│   ├── vite.config.js
│   ├── nginx.conf               # Nginx config for Docker
│   ├── Dockerfile               # Frontend Docker image
│   └── .dockerignore
│
├── scripts/
│   └── run.py                   # Single command to run both servers
│
├── docker-compose.yml           # Docker Compose orchestration
├── .gitignore
└── README.md
```

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite + Nginx (for Docker)
- **Database**: SQLite (local file)
- **Deployment**: Docker Compose or local development servers
- **Containerization**: Docker with multi-stage builds

## API Documentation

The backend provides auto-generated API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `GET /api/recommendation` - Get meal recommendation
- `POST /api/recommendation/accept` - Accept meal
- `POST /api/recommendation/skip` - Skip meal
- `POST /api/recommendation/another` - Get different suggestion
- `GET /api/recipes` - List all recipes
- `GET /api/history` - Get meal history
- `GET /api/history/stats` - Get cooking statistics

## Database Reset

To reset and re-seed the database:

```bash
cd backend
rm nextmeal.db
alembic upgrade head
python -m app.seed_data
```

## Adding Your Own Recipes

You can add recipes through the API or by editing `backend/app/seed_data.py`.

Example recipe:
```python
("Pasta Carbonara", 5, 3, 10, 20, "medium", ["pasta"])
# (name, like_score, effort_score, prep_min, cook_min, cleanup, categories)
```

## Customization

### Recommendation Algorithm

Edit `backend/app/recommendation.py` to adjust:

- Scoring weights
- Skip suppression duration (default: 4 days)
- Context inference rules
- Effort penalties

### UI Styling

Edit `frontend/src/App.css` to customize colors, fonts, and layout.

## Troubleshooting

### Backend won't start

- Ensure Python 3.9+ is installed: `python --version`
- Install dependencies: `cd backend && pip install -r requirements.txt`
- Check database exists: `alembic upgrade head && python -m app.seed_data`

### Frontend won't start

- Ensure Node.js 18+ is installed: `node --version`
- Install dependencies: `cd frontend && npm install`
- Clear node_modules if issues persist: `rm -rf node_modules && npm install`

### No recommendations

- Check backend is running on http://localhost:8000
- Verify database has recipes: `cd backend && python -m app.seed_data`
- Check browser console for errors

### CORS errors

- Ensure frontend is running on port 5173 (manual) or port 80 (Docker)
- Check backend CORS settings in `backend/app/main.py`

### Docker issues

**Containers won't start:**
- Ensure Docker and Docker Compose are installed: `docker --version && docker-compose --version`
- Check if ports 80 and 8000 are available: `docker-compose down` first
- View logs: `docker-compose logs -f`

**Database is empty:**
- The database is seeded automatically on first start
- To reset: `docker-compose down -v && docker-compose up -d`

**Can't access on http://localhost:**
- Check containers are running: `docker-compose ps`
- Try http://127.0.0.1 instead
- On Windows, ensure Docker Desktop is running

**Changes not reflected:**
- Rebuild containers: `docker-compose up -d --build`
- Clear volumes for database reset: `docker-compose down -v`

## Philosophy

This app is designed to:

- **Minimize decisions**: You get one suggestion, not a list
- **Learn passively**: No explicit ratings, learns from behavior
- **Respect context**: Time of day, fatigue, recent meals matter
- **Stay simple**: Local-first, no accounts, no cloud
- **Reduce fatigue**: Easy meals when you're tired

## What This App Does NOT Do

- No nutrition tracking
- No shopping lists
- No meal planning/calendars
- No social features
- No cloud sync
- No accounts or authentication

## Future Ideas

- Recipe images
- Import recipes from URLs
- Export/import database
- Recipe search and filtering
- Manual meal logging
- Ingredient tracking
- Dark mode

## License

MIT License - feel free to use and modify!

## Contributing

This is a personal project, but suggestions and improvements are welcome.

---

**Enjoy cooking with less decision fatigue!** 🍽️
