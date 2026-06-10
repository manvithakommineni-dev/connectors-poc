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

    # SAP
    SAP_BASE_URL: str = ""  # Leave empty to use sandbox: https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap
    SAP_API_KEY: str = ""   # From https://api.sap.com → avatar → Settings → Show API Key
    SAP_USERNAME: str = ""  # For on-premise / Basic Auth
    SAP_PASSWORD: str = ""  # For on-premise / Basic Auth
    SAP_AUTH_TYPE: str = "apikey"  # "apikey" or "basic"

    # Oracle Fusion Cloud ERP
    # Leave ORACLE_BASE_URL empty → Demo Mode (built-in real Oracle schema, no account needed)
    # For real Oracle Cloud: set to  https://your-instance.fa.oc.oraclecloud.com
    ORACLE_BASE_URL: str = ""
    ORACLE_USERNAME: str = ""   # Oracle Cloud username (email)
    ORACLE_PASSWORD: str = ""   # Oracle Cloud password

    # Workday
    # Leave WORKDAY_TENANT empty → Demo Mode (built-in real Workday schema, no account needed)
    # For real Workday: register an API Client in Workday Security > OAuth 2.0 Clients
    WORKDAY_TENANT: str = ""          # e.g.  mycompany  (from mycompany.workday.com)
    WORKDAY_CLIENT_ID: str = ""       # OAuth 2.0 Client ID from Workday
    WORKDAY_CLIENT_SECRET: str = ""   # OAuth 2.0 Client Secret from Workday

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
