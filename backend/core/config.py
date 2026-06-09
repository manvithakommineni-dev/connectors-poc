from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Any


class Settings(BaseSettings):
    SF_USERNAME: str = ""
    SF_PASSWORD: str = ""
    SF_SECURITY_TOKEN: str = ""
    SF_CONSUMER_KEY: str = ""
    SF_CONSUMER_SECRET: str = ""
    SF_DOMAIN: str = "login"
    SF_INSTANCE_URL: str = ""
    SF_OAUTH_CALLBACK_URL: str = "http://localhost:8000/api/v1/salesforce/oauth/callback"

    # HubSpot
    HS_ACCESS_TOKEN: str = ""

    APP_ENV: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
