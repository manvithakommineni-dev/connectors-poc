# Connectors POC — Metadata Retrieval

Monorepo POC for retrieving metadata from enterprise connectors.

**Sequence:** Salesforce → Netsuite → Hubspot → SAP → Oracle Apps

## Stack
- **Backend:** FastAPI (Python)
- **Frontend:** React + TypeScript (Vite)

## Structure
```
Connectors/
├── backend/          # FastAPI
│   ├── main.py
│   ├── core/         # config, settings
│   ├── salesforce/   # Salesforce connector
│   └── requirements.txt
├── frontend/         # React + Vite
│   └── src/
│       ├── api/      # API clients
│       ├── components/
│       └── pages/
└── README.md
```

## Running the Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Copy and fill in your Salesforce credentials
copy .env.example .env

uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

## Salesforce Setup (How to get credentials)

1. Log in to Salesforce
2. **Security Token:** My Settings → Personal → Reset My Security Token (emailed to you)
3. **Connected App (optional for OAuth):** Setup → Apps → App Manager → New Connected App
4. Fill in `backend/.env` with `SF_USERNAME`, `SF_PASSWORD`, `SF_SECURITY_TOKEN`

## API Endpoints (Salesforce)

| Endpoint | Description |
|---|---|
| `GET /api/v1/salesforce/connect` | Test connection, get org info |
| `GET /api/v1/salesforce/objects` | List all SObjects (tables) |
| `GET /api/v1/salesforce/objects/{name}/metadata` | Full metadata: fields, types, relationships |
| `GET /api/v1/salesforce/objects/{name}/fields` | Fields only |
| `GET /api/v1/salesforce/objects/{name}/sample` | Sample data rows (SOQL) |
