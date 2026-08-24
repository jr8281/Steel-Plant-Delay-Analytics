"""Runtime configuration loaded from environment variables."""
import os
import sys
from dataclasses import dataclass
from urllib.parse import quote_plus, unquote

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_JWT_SECRET = "change-this-before-deployment"


def _sanitize_db_url(url: str) -> str:
    """Safely encode database URL credentials."""
    if "://" in url:
        scheme, rest = url.split("://", 1)
        if "@" in rest:
            user_pass, host_db = rest.rsplit("@", 1)
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                clean_pass = unquote(password)
                encoded_pass = quote_plus(clean_pass)
                return f"{scheme}://{user}:{encoded_pass}@{host_db}"
    return url


@dataclass(frozen=True)
class Settings:
    """Application configuration from environment variables."""
    
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv(
        "DATABASE_URL",
        None
    )
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", _DEFAULT_JWT_SECRET)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501"
    )
    allowed_hosts: str = os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,0.0.0.0"
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        """Validate configuration on startup."""
        if not self.database_url:
            sys.exit(
                "FATAL: DATABASE_URL is not set in environment variables. "
                "Set DATABASE_URL in your .env file before starting the app. "
                "Example: postgresql+psycopg2://user:password@localhost:5432/dbname"
            )
        
        object.__setattr__(self, "database_url", _sanitize_db_url(self.database_url))
        
        if self.environment == "production" and self.jwt_secret_key == _DEFAULT_JWT_SECRET:
            sys.exit(
                "FATAL: JWT_SECRET_KEY is using the default placeholder value in a "
                "production environment. Set a strong, random secret via the "
                "JWT_SECRET_KEY environment variable before starting the app."
            )
        
        if self.environment == "production" and "localhost" in self.cors_origins.lower():
            sys.exit(
                "FATAL: CORS_ORIGINS contains 'localhost' in production mode. "
                "Update CORS_ORIGINS to only allow production domains."
            )


settings = Settings()