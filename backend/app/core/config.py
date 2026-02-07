from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Azure Document Intelligence (Prebuilt Invoice model – has TotalDiscount support)
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    AZURE_DOCUMENT_INTELLIGENCE_API_KEY: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY", "")
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://74.162.89.220:8080"
    ]
    
    # File upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
