from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@host:5432/dbname"

    @property
    def get_database_url(self) -> str:
        """Return the database URL, replacing postgres:// with postgresql:// if needed."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    FRONTEND_ORIGINS: str = "http://localhost:5173,https://your-app.vercel.app"

    # Rate limiting (requests per minute)
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
