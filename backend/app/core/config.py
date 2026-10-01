from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    APP_NAME: str = "ResolveAI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Supabase
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_SERVICE_KEY: str = "your-supabase-service-key-here"

    # Gemini (for future parts)
    GEMINI_API_KEY: str = "your-gemini-api-key-here"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()


def allowed_origin(origin: Optional[str]) -> Optional[str]:
    """Return `origin` if it appears in CORS_ORIGINS, otherwise None.

    Single source of truth for the CORS allow-list. Both the middleware and the
    exception handlers must gate on this: a handler that reflects the incoming
    Origin unconditionally would hand any site a credentialed CORS grant on
    every error response.
    """
    if not origin:
        return None
    return origin if origin in settings.CORS_ORIGINS else None