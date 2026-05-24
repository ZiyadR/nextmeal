from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.config import settings
from app.database import init_db
from app.routers import recommendations, recipes, history, auth

# --- Rate limiter (shared state for the process) ---
limiter = Limiter(key_func=get_remote_address)

# --- Application ---
app = FastAPI(
    title="NextMeal API",
    description="Multi-user cooking assistant API",
    version="2.0.0",
)

# Attach the limiter so slowapi can read it
app.state.limiter = limiter

# --- Rate-limit error handler ---
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Global exception handler - never leak stack traces ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}},
    )


# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.FRONTEND_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
app.include_router(recipes.router, prefix="/api", tags=["recipes"])
app.include_router(history.router, prefix="/api", tags=["history"])





@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "nextmeal-api"}


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {"message": "NextMeal API", "docs": "/docs", "health": "/api/health"}
