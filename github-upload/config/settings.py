"""Configuration settings for the AI Code Reviewer Bot."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # GitHub App Configuration
    github_app_id: str = Field(..., env="GITHUB_APP_ID")
    github_app_private_key: str = Field(..., env="GITHUB_APP_PRIVATE_KEY")
    github_webhook_secret: str = Field(..., env="GITHUB_WEBHOOK_SECRET")
    
    # Gemini AI Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model_pro: str = Field(default="gemini-2.0-flash-exp", env="GEMINI_MODEL_PRO")
    gemini_model_flash: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL_FLASH")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Application Configuration
    app_name: str = Field(default="AI Code Reviewer Bot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Review Configuration
    max_comments_per_pr: int = Field(default=20, env="MAX_COMMENTS_PER_PR")
    max_diff_size_mb: int = Field(default=10, env="MAX_DIFF_SIZE_MB")
    review_timeout_seconds: int = Field(default=300, env="REVIEW_TIMEOUT_SECONDS")
    
    # Supported Languages
    supported_languages: List[str] = Field(
        default=["python", "javascript", "typescript", "java", "sql", "go", "rust"]
    )
    
    # Static Analyzer Configuration
    enable_python_analyzers: bool = Field(default=True, env="ENABLE_PYTHON_ANALYZERS")
    enable_js_analyzers: bool = Field(default=True, env="ENABLE_JS_ANALYZERS")
    enable_java_analyzers: bool = Field(default=True, env="ENABLE_JAVA_ANALYZERS")
    enable_sql_analyzers: bool = Field(default=True, env="ENABLE_SQL_ANALYZERS")
    
    # Security Configuration
    allowed_github_ips: Optional[List[str]] = Field(default=None)
    webhook_timeout_seconds: int = Field(default=30, env="WEBHOOK_TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

