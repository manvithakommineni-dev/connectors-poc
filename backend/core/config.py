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

    # ServiceNow
    # Get a FREE Personal Developer Instance at https://developer.servicenow.com
    SN_INSTANCE_URL: str = ""    # e.g.  https://dev12345.service-now.com
    SN_USERNAME: str = "admin"   # Default username for developer instances
    SN_PASSWORD: str = ""        # Password set when you activated your instance

    # NetSuite
    # Get a 30-day free trial at https://www.netsuite.com
    # Account ID is in your NetSuite URL: https://ACCOUNTID.app.netsuite.com
    NS_ACCOUNT_ID: str = ""       # e.g.  1234567  or  1234567_SB1 for sandbox
    NS_CLIENT_ID: str = ""        # OAuth 2.0 Client ID from Manage Integrations
    NS_CLIENT_SECRET: str = ""    # OAuth 2.0 Client Secret

    # Google Ads
    # Leave GADS_DEVELOPER_TOKEN empty → Demo Mode (built-in real Google Ads v17 schema)
    # To connect live:
    #   1. Create Google Cloud project + enable Google Ads API
    #   2. Create OAuth 2.0 Desktop credentials
    #   3. Apply for Developer Token: Google Ads UI → Tools → API Center (test token is FREE)
    #   4. Run OAuth2 flow to obtain refresh token
    GADS_DEVELOPER_TOKEN: str = ""   # From Google Ads → Tools → API Center
    GADS_CLIENT_ID: str = ""         # OAuth 2.0 Client ID from Google Cloud Console
    GADS_CLIENT_SECRET: str = ""     # OAuth 2.0 Client Secret
    GADS_REFRESH_TOKEN: str = ""     # Long-lived refresh token from OAuth flow
    GADS_CUSTOMER_ID: str = ""       # Google Ads Customer ID (digits only, no dashes)

    # Google Analytics 4 (GA4) — FREE, no payment required
    # 1. Create GA4 property at https://analytics.google.com
    # 2. Google Cloud: enable Analytics Data API + Analytics Admin API
    # 3. Create service account → download JSON key
    # 4. Add service account email to GA4 Admin → Property access → Viewer
    GA4_PROPERTY_ID: str = ""              # Numeric property ID from GA4 Admin → Property Settings
    GA4_SERVICE_ACCOUNT_FILE: str = ""     # Path to service account JSON key file

    # Meta Ads (Facebook + Instagram) — live API only, no demo mode
    # 1. Create app at developers.facebook.com → Business type → add Marketing API
    # 2. Generate access token with ads_read (Graph API Explorer or System User)
    # 3. Ad account ID from Business Manager (act_123456789)
    META_ACCESS_TOKEN: str = ""            # Long-lived user or system user token with ads_read
    META_AD_ACCOUNT_ID: str = ""           # Ad account ID (with or without act_ prefix)
    META_API_VERSION: str = "v21.0"        # Graph API version

    # Adjust — live API only, no demo mode
    # Free Base plan at https://www.adjust.com (1,500 attributions/month, 12 months)
    # API Token: Adjust dashboard → Account settings → My profile → API Token
    ADJUST_API_TOKEN: str = ""

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
