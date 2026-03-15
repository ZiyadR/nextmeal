from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import recommendations, recipes, history

# Create FastAPI app
app = FastAPI(
    title="NextMeal API",
    description="Local-first cooking assistant API",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
app.include_router(recipes.router, prefix="/api", tags=["recipes"])
app.include_router(history.router, prefix="/api", tags=["history"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nextmeal-api"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "NextMeal API",
        "docs": "/docs",
        "health": "/api/health"
    }
