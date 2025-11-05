from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_db: str = "bcll_poc"
    
    # Google Maps 
    google_maps_api_key: Optional[str] = None
    
    # Gemini 
    gemini_api_key: Optional[str] = None
    
    #jwt
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    
    class Config:
        # Load from .env
        env_file = [".env"]
        case_sensitive = False


# Ensure .env is loaded before instantiating settings
load_dotenv()
settings = Settings()


if not settings.jwt_secret:
    settings.jwt_secret = "zYh0JpFg6P0A2Y3b4X9t5sL8W1kZ0qN7vF2rT9mJxN8gB2yH7dQ"

