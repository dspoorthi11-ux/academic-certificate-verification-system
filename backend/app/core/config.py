from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Certificate Verification Platform"
    app_env: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/certificate_db"
    jwt_secret: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    blockchain_rpc_url: str = "http://127.0.0.1:8545"
    contract_address: str = "0x0000000000000000000000000000000000000000"
    ipfs_api_url: str = "http://localhost:5001"
    ipfs_project_id: str = ""
    ipfs_project_secret: str = ""
    tesseract_path: str = ""
    model_path: str = "./ai-service/models"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache

def get_settings() -> Settings:
    return Settings()
