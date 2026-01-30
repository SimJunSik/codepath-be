"""
Application configuration management
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173"
]


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "CodePath Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    AUTO_CREATE_DB: bool = True

    # Redis
    REDIS_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = DEFAULT_CORS_ORIGINS

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.strip("[]").split(",") if origin.strip()]
        elif isinstance(v, list):
            origins = v
        else:
            origins = []
        merged = list({*origins, *DEFAULT_CORS_ORIGINS})
        return merged

    # Code Execution
    CODE_EXECUTION_TIMEOUT: int = 5
    CODE_EXECUTION_MAX_OUTPUT: int = 10000

    # AWS Lambda Code Executor
    USE_LAMBDA_EXECUTOR: bool = True
    CODE_EXECUTOR_LAMBDA_NAME: str = "codepath-code-executor"
    AWS_REGION: str = "ap-northeast-2"

    # AWS SES Email
    AWS_SES_SENDER_EMAIL: str = "noreply@codepath.cloud"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Admin bootstrap (optional)
    ADMIN_EMAIL: str = ""
    ADMIN_USERNAME: str = ""
    ADMIN_PASSWORD: str = ""
    ADMIN_FULL_NAME: str = ""

    # LLM Evaluation
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-mini"
    LLM_EXPLANATION_PASS_SCORE: int = 90
    LLM_EXPLANATION_TIMEOUT_SECONDS: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
