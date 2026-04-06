from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    auth_enabled: bool = True
    fraud_semantic_enabled: bool = False
    fraud_api_key: str
    faq_api_key: str

    @field_validator("auth_enabled", mode="before")
    @classmethod
    def parse_auth_enabled(cls, v):
        if isinstance(v, bool):
            return v
        if v is None:
            return True
        s = str(v).strip().lower()
        if s in ("0", "false", "no", "off", ""):
            return False
        return True

    @field_validator("fraud_semantic_enabled", mode="before")
    @classmethod
    def parse_fraud_semantic(cls, v):
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        s = str(v).strip().lower()
        if s in ("0", "false", "no", "off", ""):
            return False
        return True


def get_settings() -> Settings:
    return Settings()
