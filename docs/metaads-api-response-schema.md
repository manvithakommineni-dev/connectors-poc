# Meta Ads (Facebook + Instagram) API — Response Schema Documentation

Live-only connector. No demo mode — credentials required in `backend/.env`.

Instagram ads are accessed through the same Meta Marketing API. Use `publisher_platform` breakdown for Facebook vs Instagram split.

---

## Authentication

| Variable | Description |
|----------|-------------|
| `META_ACCESS_TOKEN` | User or System User token with `ads_read` scope |
| `META_AD_ACCOUNT_ID` | Ad account ID (`act_123456789` or `123456789`) |
| `META_API_VERSION` | Graph API version (default `v21.0`) |

---

## Endpoints

| Purpose | URL |
|---------|-----|
| Connect / test | `GET /api/v1/metaads/connect` |
| Categories | `GET /api/v1/metaads/categories` |
| List items | `GET /api/v1/metaads/items?category=campaigns` |
| Item detail | `GET /api/v1/metaads/items/{id}?category=campaigns` |

**Categories:** `account`, `campaigns`, `adsets`, `ads`, `campaign_fields`, `adset_fields`, `ad_fields`, `insights_metrics`, `insights_breakdowns`

---

## Meta vs Salesforce terminology

| Salesforce | Meta Ads |
|------------|----------|
| SObject | Campaign / AdSet / Ad / AdAccount |
| Field | Graph API field (`name`, `status`, `objective`) |
| Describe | Field catalog + live object fetch |
| Record | Campaign / Ad row from live API |

---

## Underlying Graph API

| Resource | Endpoint |
|----------|----------|
| Ad Account | `GET /act_{id}?fields=...` |
| Campaigns | `GET /act_{id}/campaigns?fields=...` |
| Ad Sets | `GET /act_{id}/adsets?fields=...` |
| Ads | `GET /act_{id}/ads?fields=...` |
| Insights | `GET /act_{id}/insights?fields=impressions,clicks,spend` |

**Docs:** https://developers.facebook.com/docs/marketing-api
