from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Core settings populated via dotenv or environment configuration."""
    BOT_TOKEN: str
    DATABASE_URL: str
    WEBHOOK_URL: str
    
    class Config:
        env_file = ".env"

settings = Settings()
