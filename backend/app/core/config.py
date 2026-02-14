from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "SentimentAnalysis"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sentiment_user:sentiment_pass@localhost:5432/sentiment_db"
    DATABASE_SYNC_URL: str = "postgresql://sentiment_user:sentiment_pass@localhost:5432/sentiment_db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Refresh cycle
    REFRESH_INTERVAL_MINUTES: int = 15
    FETCH_TIMEOUT_SECONDS: int = 45
    DATA_RETENTION_DAYS: int = 90

    # API Keys
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "SentimentAnalysis/1.0"
    NEWSAPI_KEY: str = ""
    MEDIASTACK_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    ALPHA_VANTAGE_KEY: str = ""
    QUIVER_QUANT_KEY: str = ""
    GOOGLE_TRENDS_PROXY: str = ""
    GDELT_BASE_URL: str = "https://api.gdeltproject.org/api/v2"
    STOCKTWITS_TOKEN: str = ""
    YAHOO_FINANCE_KEY: str = ""

    # NLP
    USE_FINBERT: bool = False


settings = Settings()
