"""
Configuration for the FastAPI application.
"""

import os
from typing import Optional


class Settings:
    """Application settings."""

    # API
    API_TITLE: str = "Assignment Evaluation API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "REST API for evaluating student submissions"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS
    CORS_ORIGINS: list = ["*"]

    # File uploads (if needed)
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Evaluation
    EVALUATION_TIMEOUT: int = 30  # seconds


settings = Settings()
