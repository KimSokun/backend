from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "AllTools API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    TEMP_DIR: Path = STORAGE_DIR / "temp"
    RESULTS_DIR: Path = STORAGE_DIR / "results"
    
    # Upload Limits & TTL
    MAX_UPLOAD_SIZE_MB: int = 500
    TEMP_FILE_TTL_MINUTES: int = 30
    CLEANUP_INTERVAL_MINUTES: int = 5
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    HEAVY_RATE_LIMIT_PER_MINUTE: int = 15
    
    # Redis Cache Settings
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = True
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure directories exist
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
