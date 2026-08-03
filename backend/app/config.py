from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB Configuration
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "support_copilot"
    
    # JWT Configuration
    jwt_secret: str = "change-me-to-a-secure-secret"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60
    
    # API Configuration
    api_title: str = "Autonomous Customer Support Copilot - Backend"
    api_version: str = "0.1.0"
    api_description: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    # Environment
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
