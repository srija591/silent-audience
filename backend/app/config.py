import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")


def _normalize_db_url(url: str) -> str:
    """Render/Heroku-style URLs (postgres:// or postgresql://) -> SQLAlchemy + psycopg2 driver."""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL", "sqlite:///./silent_audience.db"))
# Comma-separated list of frontend origins allowed to call the API, e.g. https://silent-audience.onrender.com
CORS_ORIGINS = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
MOCK_MODE = os.getenv("MOCK_MODE", "auto").lower()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
STT_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v4")
STT_MODE = os.getenv("SARVAM_STT_MODE", "verbatim")
STT_LANGUAGE = os.getenv("SARVAM_LANGUAGE", "en-IN")
STT_TIMEOUT = int(os.getenv("SARVAM_TIMEOUT_SECONDS", "1800"))
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.sarvam.ai/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "sarvam-105b")
LLM_API_KEY = os.getenv("LLM_API_KEY") or SARVAM_API_KEY


def use_mock() -> bool:
    return MOCK_MODE == "true" or (MOCK_MODE == "auto" and not SARVAM_API_KEY)
