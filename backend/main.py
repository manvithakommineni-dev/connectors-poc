from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from salesforce.router import router as salesforce_router
from hubspot.router import router as hubspot_router
from sap.router import router as sap_router

app = FastAPI(
    title="Connectors POC API",
    description="Metadata retrieval POC for Salesforce, Netsuite, Hubspot, SAP, Oracle Apps",
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


@app.get("/")
def root():
    return {
        "app": "Connectors POC",
        "version": "0.1.0",
        "connectors": ["salesforce", "hubspot", "sap", "netsuite (coming)", "oracle (coming)"],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
