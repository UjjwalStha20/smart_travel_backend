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
    # Fast model used for lightweight conversational replies + intent handling.
    # Falls back to LLM_MODEL when not set.
    LLM_FAST_MODEL: str = ""
    # Max seconds to wait for the model before falling back to the knowledge base.
    LLM_TIMEOUT_SECONDS: float = 40.0
    # Model used when a question genuinely needs a complex/reasoning answer.
    LLM_COMPLEX_MODEL: str = ""

    # "auto" -> use live weather in the contextual recommender with automatic
    # offline fallback; "off" -> never make weather lookups for scoring.
    WEATHER_MODE: str = "auto"

    # Maximum straight-line distance (km) for a destination to be considered
    # "nearby". If fewer than NEARBY_MIN_RESULTS qualify, the radius widens in
    # steps until it reaches NEARBY_MAX_KM.
    NEARBY_MIN_KM: float = 80
    NEARBY_MAX_KM: float = 150
    NEARBY_MIN_RESULTS: int = 3

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