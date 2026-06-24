from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from salesforce.router import router as salesforce_router
from hubspot.router import router as hubspot_router
from sap.router import router as sap_router
from oracle.router import router as oracle_router
from workday.router import router as workday_router
from servicenow.router import router as servicenow_router
from netsuite.router import router as netsuite_router
from googleads.router import router as googleads_router
from ga4.router import router as ga4_router
from metaads.router import router as metaads_router
from adjust.router import router as adjust_router
from pinterest.router import router as pinterest_router
from youtube.router import router as youtube_router
from facebook.router import router as facebook_router
from instagram.router import router as instagram_router
from adobeanalytics.router import router as adobeanalytics_router
from workato.router import router as workato_router

app = FastAPI(
    title="Connectors POC API",
    description="Metadata retrieval POC — Salesforce, HubSpot, SAP, Oracle, Workday, ServiceNow, NetSuite, Google Ads, GA4, Meta Ads, Pinterest, YouTube, Facebook, Instagram, Adobe Analytics, Adjust, Workato",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(salesforce_router, prefix="/api/v1")
app.include_router(hubspot_router, prefix="/api/v1")
app.include_router(sap_router, prefix="/api/v1")
app.include_router(oracle_router, prefix="/api/v1")
app.include_router(workday_router, prefix="/api/v1")
app.include_router(servicenow_router, prefix="/api/v1")
app.include_router(netsuite_router, prefix="/api/v1")
app.include_router(googleads_router, prefix="/api/v1")
app.include_router(ga4_router, prefix="/api/v1")
app.include_router(metaads_router, prefix="/api/v1")
app.include_router(adjust_router, prefix="/api/v1")
app.include_router(pinterest_router, prefix="/api/v1")
app.include_router(youtube_router, prefix="/api/v1")
app.include_router(facebook_router, prefix="/api/v1")
app.include_router(instagram_router, prefix="/api/v1")
app.include_router(adobeanalytics_router, prefix="/api/v1")
app.include_router(workato_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "app": "Connectors POC",
        "version": "0.1.0",
        "connectors": [
            "salesforce", "hubspot", "sap", "oracle", "workday",
            "servicenow", "netsuite", "googleads", "ga4", "metaads", "pinterest", "youtube", "facebook", "instagram", "adobeanalytics", "adjust", "workato",
        ],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
