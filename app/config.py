"""
Application configuration with support for environment variables and AWS Secrets Manager.
"""
import os
import logging
import threading
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables or AWS Secrets Manager."""

    # Flask Configuration
    FLASK_ENV: str = "development"
    FLASK_SECRET_KEY: str = "dev-secret-key-change-in-production"
    FLASK_APP: str = "run.py"

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # Gemini AI Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash-preview"

    # CORS Configuration
    CORS_ORIGINS: str = "*"  # Comma-separated for production: "https://app.example.com"

    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAIL_MAX: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60

    # AWS Configuration (for production deployment)
    USE_AWS_SECRETS: bool = False
    AWS_SECRET_NAME: str = "catalogai/production"
    AWS_REGION: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env file
    )

    def model_post_init(self, __context) -> None:
        """Validate settings after initialization."""
        # Issue #1: Validate Flask secret key in production
        if self.FLASK_ENV == "production" and self.FLASK_SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError(
                "FLASK_SECRET_KEY must be changed in production! "
                "Set a unique, random secret key via environment variable."
            )

        # Issue #48: Validate circuit breaker configuration
        if self.CIRCUIT_BREAKER_FAIL_MAX <= 0:
            raise ValueError("CIRCUIT_BREAKER_FAIL_MAX must be positive")
        if self.CIRCUIT_BREAKER_TIMEOUT <= 0:
            raise ValueError("CIRCUIT_BREAKER_TIMEOUT must be positive")

        # Issue #2: Validate required configuration
        if not self.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not self.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is required")
        if not self.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")

    def load_aws_secrets(self):
        """Load secrets from AWS Secrets Manager if enabled."""
        if not self.USE_AWS_SECRETS:
            return

        try:
            import json
            import boto3
            from botocore.exceptions import ClientError

            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=self.AWS_REGION
            )

            try:
                secret_value = client.get_secret_value(SecretId=self.AWS_SECRET_NAME)
                secrets = json.loads(secret_value['SecretString'])

                # Override with secrets from AWS
                self.SUPABASE_URL = secrets.get('SUPABASE_URL', self.SUPABASE_URL)
                self.SUPABASE_KEY = secrets.get('SUPABASE_KEY', self.SUPABASE_KEY)
                self.SUPABASE_SERVICE_ROLE_KEY = secrets.get(
                    'SUPABASE_SERVICE_ROLE_KEY', self.SUPABASE_SERVICE_ROLE_KEY
                )
                self.FLASK_SECRET_KEY = secrets.get('FLASK_SECRET_KEY', self.FLASK_SECRET_KEY)
                self.GEMINI_API_KEY = secrets.get('GEMINI_API_KEY', self.GEMINI_API_KEY)
            except ClientError as e:
                logger.error(f"Error loading AWS secrets: {e}")
                raise

        except ImportError:
            logger.error("boto3 not installed. Cannot load AWS secrets.")
            raise


# Issue #3: Removed lru_cache to allow secret rotation
# Settings are lightweight enough to recreate on each call
_cached_settings: Optional[Settings] = None
_settings_lock = threading.Lock()


def get_settings() -> Settings:
    """
    Get application settings instance with thread-safe initialization.

    Note: Settings are cached in a module-level variable but can be
    refreshed by setting _cached_settings to None. This allows
    secret rotation without the permanent caching of lru_cache.
    Uses double-checked locking for thread safety.
    """
    global _cached_settings
    if _cached_settings is None:
        with _settings_lock:
            # Double-check after acquiring lock
            if _cached_settings is None:
                _cached_settings = Settings()
                _cached_settings.load_aws_secrets()
    return _cached_settings
