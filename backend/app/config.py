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
            
        from urllib.parse import quote, unquote
        scheme_end = url.find('://')
        if scheme_end != -1:
            scheme = url[:scheme_end+3]
            rest = url[scheme_end+3:]
            pieces = rest.rsplit('@', 1)
            if len(pieces) == 2:
                user_pass, host_rest = pieces
                user_pass_parts = user_pass.split(':', 1)
                if len(user_pass_parts) == 2:
                    user, raw_pass = user_pass_parts
                    raw_pass = unquote(raw_pass)
                    encoded_pass = quote(raw_pass, safe="")
                    url = f"{scheme}{user}:{encoded_pass}@{host_rest}"
                
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
