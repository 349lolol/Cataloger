import os
import logging
import threading
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    FLASK_ENV: str = "development"
    FLASK_SECRET_KEY: str = "dev-secret-key-change-in-production"
    FLASK_APP: str = "run.py"

    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash-preview"

    CORS_ORIGINS: str = "*"

    CIRCUIT_BREAKER_FAIL_MAX: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60

    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_RATE_LIMIT_ATTEMPTS: int = 5

    USE_AWS_SECRETS: bool = False
    AWS_SECRET_NAME: str = "catalogai/production"
    AWS_REGION: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    def model_post_init(self, __context) -> None:
        if self.FLASK_ENV == "production" and self.FLASK_SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError("FLASK_SECRET_KEY must be changed in production")

        if self.CIRCUIT_BREAKER_FAIL_MAX <= 0:
            raise ValueError("CIRCUIT_BREAKER_FAIL_MAX must be positive")
        if self.CIRCUIT_BREAKER_TIMEOUT <= 0:
            raise ValueError("CIRCUIT_BREAKER_TIMEOUT must be positive")

        if not self.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not self.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is required")
        if not self.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")

    def load_aws_secrets(self):
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
            logger.error("boto3 not installed")
            raise


_cached_settings: Optional[Settings] = None
_settings_lock = threading.Lock()


def get_settings() -> Settings:
    global _cached_settings
    if _cached_settings is None:
        with _settings_lock:
            if _cached_settings is None:
                _cached_settings = Settings()
                _cached_settings.load_aws_secrets()
    return _cached_settings
