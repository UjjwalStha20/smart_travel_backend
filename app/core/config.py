from pydantic_settings import BaseSettings
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """Application settings."""

    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "google/gemma-4-31b-it:free"

    DB_ECHO: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8" 
    
    @property
    def database_url(self) -> str:
        """Construct the database URL from the individual components."""
        return f"postgresql+psycopg2://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
settings = Settings()