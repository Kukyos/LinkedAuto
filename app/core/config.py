"""
Configuration management using pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    DEBUG: bool = True
    PROJECT_NAME: str = "AutoProjectPost"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://linkedinauto.vercel.app",
        "https://linkedinauto-mayurcwim-kukyos-2121s-projects.vercel.app"
    ]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/autoprojectpost"
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "https://your-backend.railway.app/api/v1/auth/github/callback"
    GITHUB_AUTHORIZATION_URL: str = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL: str = "https://github.com/login/oauth/access_token"
    GITHUB_API_URL: str = "https://api.github.com"
    
    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = "https://your-backend.railway.app/api/v1/auth/linkedin/callback"
    LINKEDIN_AUTHORIZATION_URL: str = "https://www.linkedin.com/oauth/v2/authorization"
    LINKEDIN_TOKEN_URL: str = "https://www.linkedin.com/oauth/v2/accessToken"
    LINKEDIN_API_URL: str = "https://api.linkedin.com/v2"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 1000
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "autoprojectpost-uploads"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ENCRYPTION_KEY: str = "your-encryption-key-32-bytes-min"
    
    # Rate Limiting
    GITHUB_API_RATE_LIMIT: int = 5000
    LINKEDIN_API_RATE_LIMIT: int = 100
    
    # Webhooks
    WEBHOOK_SECRET: str = "your-webhook-secret"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
