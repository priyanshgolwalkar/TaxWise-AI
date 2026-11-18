from functools import lru_cache
from secrets import token_urlsafe
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = 'sqlite:///./taxwise.db'
    tidb_ca_path: str | None = None
    environment: str = 'development'
    jwt_secret: str = ''
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60
    cors_origins: str = 'http://localhost:5173'
    llm_provider: str = 'gemini'
    llm_api_key: str | None = None
    llm_model: str = 'gemini-3.8-flash'
    llm_base_url: str = 'https://generativelanguage.googleapis.com/v1beta/openai/'
    gemini_api_key: str | None = None
    gemini_model: str = 'gemini-3.8-flash'
    gemini_base_url: str = 'https://generativelanguage.googleapis.com/v1beta/openai/'
    groq_api_key: str | None = None
    groq_model: str = ''
    groq_base_url: str = 'https://api.groq.com/openai/v1'
    minio_endpoint: str | None = None
    minio_access_key: str = ''
    minio_secret_key: str = ''
    minio_bucket: str = 'taxwise-documents'
    minio_secure: bool = False
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @model_validator(mode='after')
    def validate_jwt_secret(self):
        if self.environment.strip().lower() in {'production', 'prod'}:
            if not self.jwt_secret.strip() or self.jwt_secret.strip().lower().startswith('replace-with-'):
                raise ValueError('JWT_SECRET must be set to a strong value in production.')
        elif not self.jwt_secret:
            self.jwt_secret = token_urlsafe(32)
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip().rstrip('/') for origin in self.cors_origins.split(',')]
        return [origin for origin in origins if origin]

@lru_cache
def get_settings() -> Settings:
    return Settings()
