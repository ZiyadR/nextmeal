import os
from app.config import Settings

def test_database_url_property_postgres_fix():
    # Test that 'postgres://' is correctly replaced with 'postgresql://'
    settings = Settings(DATABASE_URL="postgres://user:pass@localhost:5432/db")
    assert settings.get_database_url == "postgresql://user:pass@localhost:5432/db"

def test_database_url_property_no_change_needed():
    # Test that 'postgresql://' is left untouched
    settings = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/db")
    assert settings.get_database_url == "postgresql://user:pass@localhost:5432/db"

    # Test that 'sqlite://' is left untouched
    settings_sqlite = Settings(DATABASE_URL="sqlite:///./test.db")
    assert settings_sqlite.get_database_url == "sqlite:///./test.db"

def test_frontend_origins_parsing():
    settings = Settings(FRONTEND_ORIGINS="http://localhost:5173, https://your-app.vercel.app ,  ")
    origins = [origin.strip() for origin in settings.FRONTEND_ORIGINS.split(",") if origin.strip()]
    
    assert len(origins) == 2
    assert origins[0] == "http://localhost:5173"
    assert origins[1] == "https://your-app.vercel.app"
