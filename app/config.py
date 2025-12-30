"""
Application configuration with support for environment variables and AWS Secrets Manager.
"""
import os
import json
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


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

    # Embedding Model Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Gemini AI Configuration (for product enrichment)
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3-flash-preview"  # Gemini 3.0 Flash Preview - latest model with search grounding

    # AWS Configuration (for production deployment)
    USE_AWS_SECRETS: bool = False
    AWS_SECRET_NAME: str = "catalogai/production"
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file

    def load_aws_secrets(self):
        """Load secrets from AWS Secrets Manager if enabled."""
        if not self.USE_AWS_SECRETS:
            return

        try:
            import boto3
            from botocore.exceptions import ClientError

            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=self.AWS_REGION
            )

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
            print(f"Error loading AWS secrets: {e}")
            raise
        except ImportError:
            print("boto3 not installed. Cannot load AWS secrets.")
            raise


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings instance."""
    settings = Settings()
    settings.load_aws_secrets()
    return settings
