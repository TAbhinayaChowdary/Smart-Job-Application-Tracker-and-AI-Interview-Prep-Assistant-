from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv() 

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (.env file).
    """
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Database Settings (PostgreSQL)
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_NAME: str = Field(default="job_tracker_db")
    DB_USER: str = Field(default="job_user")
    DB_PASSWORD: str = Field(default="secret_db_password")

    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str = Field(default="dummy_client_id")
    GOOGLE_CLIENT_SECRET: str = Field(default="dummy_client_secret")
    GOOGLE_REDIRECT_URI: str = Field(default="http://127.0.0.1:8000/auth/google/callback")
    
    # Security Settings
    SECRET_KEY: str = Field(default="long_secret_key_default")

    # OpenAI Settings
    OPENAI_API_KEY: str = Field(default="sk-dummy-key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")


settings = Settings()
