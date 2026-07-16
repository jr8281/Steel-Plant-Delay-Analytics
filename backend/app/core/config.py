"""Runtime configuration loaded from environment variables."""
from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://steeluser:steelpassword@localhost:5432/steelplant"
    )
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-before-deployment")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:8501")


settings = Settings()
