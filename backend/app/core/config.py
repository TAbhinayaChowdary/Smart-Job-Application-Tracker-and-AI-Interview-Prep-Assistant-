from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Job Application Tracker"
    DATABASE_URL: str = "sqlite:///./sjtap.db"
    OPENAI_API_KEY: str = ""
    SECRET_KEY: str = "supersecretkey"
    
    # Google Auth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    
    class Config:
        env_file = ".env"

settings = Settings()
