from functools import lru_cache
from secrets import token_urlsafe
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = 'sqlite:///./taxwise.db'
    jwt_secret: str = token_urlsafe(32)
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60
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

@lru_cache
def get_settings() -> Settings:
    return Settings()
