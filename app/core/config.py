from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_ECHO: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    LLM_API_KEY: str
    LLM_BASE_URL: str
    LLM_MODEL: str

    # "auto" -> use live weather in the contextual recommender with automatic
    # offline fallback; "off" -> never make weather lookups for scoring.
    WEATHER_MODE: str = "auto"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @property
    def database_url(self) -> str:
        """Construct the database URL from the individual components."""

        return f"postgresql+psycopg2://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()