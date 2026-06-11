"""
Google Ads connectivity and metadata retrieval service.

How Google Ads exposes metadata:
  Google Ads uses its own query language (GAQL — Google Ads Query Language)
  and a special metadata service called GoogleAdsFieldService.

  Key API endpoints:
    Field metadata : POST https://googleads.googleapis.com/v17/googleAdsFields:search
    List customers : GET  https://googleads.googleapis.com/v17/customers:listAccessibleCustomers
    Run query      : POST https://googleads.googleapis.com/v17/customers/{id}/googleAds:search

  Google Ads concept equivalents:
    Salesforce SObject    → Google Ads Resource   (campaign, ad_group, keyword_view)
    Salesforce Field      → Google Ads Attribute  (campaign.name, campaign.status)
    Salesforce Metric     → Google Ads Metric     (metrics.clicks, metrics.impressions)
    SAP EntityType        → Google Ads Resource
    Database Table        → Google Ads Resource

  Field categories in Google Ads:
    ATTRIBUTE  → Descriptive fields  (campaign.name, campaign.status, campaign.budget)
    METRIC     → Performance numbers (metrics.clicks, metrics.cost_micros, metrics.conversions)
    SEGMENT    → Grouping dimensions (segments.date, segments.device, segments.ad_network_type)
    RESOURCE   → Related sub-resource references

  Key resources:
    campaign            → Campaigns (search, display, shopping, video, app)
    ad_group            → Ad Groups within campaigns
    ad_group_ad         → Individual ads (text ads, responsive ads)
    ad_group_criterion  → Keywords, placements, audiences
    keyword_view        → Keyword performance view
    search_term_view    → Search terms triggering ads
    campaign_budget     → Campaign budget settings
    customer            → Google Ads account (top-level)
    geographic_view     → Performance by location
    audience            → Audience lists

Authentication (real Google Ads):
  OAuth 2.0 with offline refresh token:
    1. Create Google Cloud Project at https://console.cloud.google.com
    2. Enable Google Ads API
    3. Create OAuth 2.0 credentials (Desktop app)
    4. Apply for Developer Token: Google Ads UI → Tools → API Center
       (Test token is FREE and approved instantly — works with test accounts)
    5. Run OAuth flow to get refresh token
  Required: GADS_DEVELOPER_TOKEN, GADS_CLIENT_ID, GADS_CLIENT_SECRET,
            GADS_REFRESH_TOKEN, GADS_CUSTOMER_ID

Demo Mode:
  If GADS_DEVELOPER_TOKEN is empty, returns built-in real Google Ads
  field schema based on actual GoogleAdsFieldService definitions.
"""

import requests
import logging
from core.config import settings

logger = logging.getLogger(__name__)

GADS_API_BASE = "https://googleads.googleapis.com/v17"
GADS_TOKEN_URL = "https://oauth2.googleapis.com/token"
GADS_FIELD_SEARCH_URL = f"{GADS_API_BASE}/googleAdsFields:search"

# ─────────────────────────────────────────────────────────────────────────────
# Built-in demo — real Google Ads API resource/field schema
# Based on actual GoogleAdsFieldService definitions (v17)
# ─────────────────────────────────────────────────────────────────────────────
DEMO_CATEGORIES = [
    {
        "id": "campaigns",
        "label": "Campaigns",
        "description": "Campaign settings, budgets, targeting, bidding strategies",
        "resources": [
            {
                "name": "campaign",
                "label": "Campaign",
                "category": "campaigns",
                "description": "Top-level campaign resource. Controls budget, targeting, and bidding for a group of ads.",
                "fields": [
                    {"name": "campaign.id", "label": "Campaign ID", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Unique ID of the campaign"},
                    {"name": "campaign.name", "label": "Campaign Name", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "The name of the campaign"},
                    {"name": "campaign.status", "label": "Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "ENABLED, PAUSED, REMOVED"},
                    {"name": "campaign.advertising_channel_type", "label": "Channel Type", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "SEARCH, DISPLAY, SHOPPING, VIDEO, APP, SMART"},
                    {"name": "campaign.bidding_strategy_type", "label": "Bidding Strategy", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "TARGET_CPA, TARGET_ROAS, MAXIMIZE_CONVERSIONS, MANUAL_CPC, etc."},
                    {"name": "campaign.start_date", "label": "Start Date", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Campaign start date (YYYY-MM-DD)"},
                    {"name": "campaign.end_date", "label": "End Date", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Campaign end date (YYYY-MM-DD)"},
                    {"name": "campaign.campaign_budget", "label": "Budget Resource", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "Resource name of the campaign budget"},
                    {"name": "campaign.target_cpa.target_cpa_micros", "label": "Target CPA (micros)", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Target cost-per-acquisition in micros (1M = $1)"},
                    {"name": "campaign.target_roas.target_roas", "label": "Target ROAS", "data_type": "DOUBLE", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Target return on ad spend"},
                    {"name": "metrics.clicks", "label": "Clicks", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total number of clicks"},
                    {"name": "metrics.impressions", "label": "Impressions", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total number of times ad was shown"},
                    {"name": "metrics.cost_micros", "label": "Cost (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total cost in micros (1,000,000 = $1)"},
                    {"name": "metrics.conversions", "label": "Conversions", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total number of conversions"},
                    {"name": "metrics.ctr", "label": "CTR", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Click-through rate (clicks/impressions)"},
                    {"name": "metrics.average_cpc", "label": "Avg. CPC (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Average cost per click"},
                    {"name": "metrics.conversion_rate", "label": "Conversion Rate", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Conversions / clicks"},
                    {"name": "metrics.cost_per_conversion", "label": "Cost/Conv. (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Cost per conversion in micros"},
                    {"name": "segments.date", "label": "Date", "data_type": "STRING", "category": "SEGMENT", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Date segment (YYYY-MM-DD) for breaking down by day"},
                    {"name": "segments.device", "label": "Device", "data_type": "ENUM", "category": "SEGMENT", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "MOBILE, DESKTOP, TABLET, CONNECTED_TV"},
                ],
                "gaql_example": "SELECT campaign.id, campaign.name, campaign.status, metrics.clicks, metrics.impressions, metrics.cost_micros FROM campaign WHERE campaign.status = 'ENABLED'"
            },
            {
                "name": "campaign_budget",
                "label": "Campaign Budget",
                "category": "campaigns",
                "description": "Budget settings for campaigns — daily budget, delivery method",
                "fields": [
                    {"name": "campaign_budget.id", "label": "Budget ID", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Unique ID of the budget"},
                    {"name": "campaign_budget.name", "label": "Budget Name", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Name of the budget"},
                    {"name": "campaign_budget.amount_micros", "label": "Amount (micros)", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Daily budget amount in micros"},
                    {"name": "campaign_budget.delivery_method", "label": "Delivery Method", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "STANDARD (spread evenly) or ACCELERATED"},
                    {"name": "campaign_budget.status", "label": "Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "ENABLED or REMOVED"},
                    {"name": "campaign_budget.total_amount_micros", "label": "Total Amount (micros)", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total campaign lifetime budget"},
                    {"name": "campaign_budget.explicitly_shared", "label": "Shared Budget", "data_type": "BOOLEAN", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Whether budget is shared across campaigns"},
                ],
                "gaql_example": "SELECT campaign_budget.id, campaign_budget.name, campaign_budget.amount_micros FROM campaign_budget"
            },
        ]
    },
    {
        "id": "adGroups",
        "label": "Ad Groups",
        "description": "Ad Groups, Individual Ads, Keywords, Criteria",
        "resources": [
            {
                "name": "ad_group",
                "label": "Ad Group",
                "category": "adGroups",
                "description": "A group of ads sharing the same budget, targeting, and bidding",
                "fields": [
                    {"name": "ad_group.id", "label": "Ad Group ID", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Unique ID of the ad group"},
                    {"name": "ad_group.name", "label": "Ad Group Name", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Name of the ad group"},
                    {"name": "ad_group.status", "label": "Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "ENABLED, PAUSED, REMOVED"},
                    {"name": "ad_group.campaign", "label": "Campaign", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "Resource name of the parent campaign"},
                    {"name": "ad_group.type", "label": "Type", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "SEARCH_STANDARD, DISPLAY_STANDARD, SHOPPING_PRODUCT_ADS, etc."},
                    {"name": "ad_group.cpc_bid_micros", "label": "CPC Bid (micros)", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Max CPC bid for the ad group in micros"},
                    {"name": "ad_group.target_cpa_micros", "label": "Target CPA (micros)", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Target CPA for the ad group"},
                    {"name": "metrics.clicks", "label": "Clicks", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total clicks"},
                    {"name": "metrics.impressions", "label": "Impressions", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total impressions"},
                    {"name": "metrics.cost_micros", "label": "Cost (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total spend in micros"},
                    {"name": "metrics.conversions", "label": "Conversions", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total conversions"},
                ],
                "gaql_example": "SELECT ad_group.id, ad_group.name, ad_group.status, metrics.clicks, metrics.cost_micros FROM ad_group WHERE campaign.status = 'ENABLED'"
            },
            {
                "name": "ad_group_criterion",
                "label": "Keywords / Criteria",
                "category": "adGroups",
                "description": "Keywords, placements, audiences, and other ad group targeting criteria",
                "fields": [
                    {"name": "ad_group_criterion.criterion_id", "label": "Criterion ID", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Unique ID of the criterion"},
                    {"name": "ad_group_criterion.type", "label": "Type", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "KEYWORD, PLACEMENT, MOBILE_APP_CATEGORY, USER_LIST, etc."},
                    {"name": "ad_group_criterion.status", "label": "Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "ENABLED, PAUSED, REMOVED"},
                    {"name": "ad_group_criterion.keyword.text", "label": "Keyword Text", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "The keyword text"},
                    {"name": "ad_group_criterion.keyword.match_type", "label": "Match Type", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "EXACT, PHRASE, BROAD"},
                    {"name": "ad_group_criterion.cpc_bid_micros", "label": "CPC Bid (micros)", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Keyword-level CPC bid override"},
                    {"name": "ad_group_criterion.quality_info.quality_score", "label": "Quality Score", "data_type": "INT32", "category": "ATTRIBUTE", "filterable": False, "selectable": True, "sortable": True, "is_repeated": False, "description": "Keyword quality score (1-10)"},
                    {"name": "metrics.clicks", "label": "Clicks", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Clicks on this keyword"},
                    {"name": "metrics.impressions", "label": "Impressions", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Times ad was shown for this keyword"},
                    {"name": "metrics.cost_micros", "label": "Cost (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total cost for this keyword"},
                    {"name": "metrics.average_cpc", "label": "Avg. CPC", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Average cost per click"},
                    {"name": "metrics.conversions", "label": "Conversions", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Conversions attributed to this keyword"},
                ],
                "gaql_example": "SELECT ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, metrics.clicks, metrics.impressions FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD'"
            },
        ]
    },
    {
        "id": "ads",
        "label": "Ads & Creatives",
        "description": "Individual ads, responsive search ads, display ads, performance",
        "resources": [
            {
                "name": "ad_group_ad",
                "label": "Ad",
                "category": "ads",
                "description": "Individual ad creatives within ad groups",
                "fields": [
                    {"name": "ad_group_ad.ad.id", "label": "Ad ID", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Unique ID of the ad"},
                    {"name": "ad_group_ad.status", "label": "Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "ENABLED, PAUSED, REMOVED"},
                    {"name": "ad_group_ad.ad.type", "label": "Ad Type", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "EXPANDED_TEXT_AD, RESPONSIVE_SEARCH_AD, DISPLAY_AD, etc."},
                    {"name": "ad_group_ad.ad.name", "label": "Ad Name", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Name of the ad"},
                    {"name": "ad_group_ad.ad.final_urls", "label": "Final URLs", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": True, "description": "Landing page URLs"},
                    {"name": "ad_group_ad.ad.responsive_search_ad.headlines", "label": "Headlines", "data_type": "MESSAGE", "category": "ATTRIBUTE", "filterable": False, "selectable": True, "sortable": False, "is_repeated": True, "description": "Up to 15 headline assets for responsive search ads"},
                    {"name": "ad_group_ad.ad.responsive_search_ad.descriptions", "label": "Descriptions", "data_type": "MESSAGE", "category": "ATTRIBUTE", "filterable": False, "selectable": True, "sortable": False, "is_repeated": True, "description": "Up to 4 description assets"},
                    {"name": "ad_group_ad.policy_summary.approval_status", "label": "Approval Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "APPROVED, DISAPPROVED, UNDER_REVIEW, APPROVED_LIMITED"},
                    {"name": "metrics.clicks", "label": "Clicks", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total clicks on this ad"},
                    {"name": "metrics.impressions", "label": "Impressions", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total impressions"},
                    {"name": "metrics.ctr", "label": "CTR", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Click-through rate"},
                    {"name": "metrics.cost_micros", "label": "Cost (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total spend for this ad"},
                ],
                "gaql_example": "SELECT ad_group_ad.ad.id, ad_group_ad.ad.type, ad_group_ad.status, metrics.clicks, metrics.impressions, metrics.ctr FROM ad_group_ad WHERE ad_group_ad.status != 'REMOVED'"
            },
        ]
    },
    {
        "id": "performance",
        "label": "Performance & Reports",
        "description": "Search terms, geographic performance, audience insights",
        "resources": [
            {
                "name": "search_term_view",
                "label": "Search Term View",
                "category": "performance",
                "description": "Actual search queries that triggered your ads",
                "fields": [
                    {"name": "search_term_view.search_term", "label": "Search Term", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "The actual search query the user typed"},
                    {"name": "search_term_view.status", "label": "Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "ADDED (added as keyword), EXCLUDED, NONE"},
                    {"name": "metrics.clicks", "label": "Clicks", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Clicks from this search term"},
                    {"name": "metrics.impressions", "label": "Impressions", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Impressions for this search term"},
                    {"name": "metrics.cost_micros", "label": "Cost (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Cost for this search term"},
                    {"name": "metrics.conversions", "label": "Conversions", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Conversions from this search term"},
                    {"name": "segments.date", "label": "Date", "data_type": "STRING", "category": "SEGMENT", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Date of performance data"},
                ],
                "gaql_example": "SELECT search_term_view.search_term, metrics.clicks, metrics.impressions, metrics.conversions FROM search_term_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.clicks DESC LIMIT 100"
            },
            {
                "name": "geographic_view",
                "label": "Geographic View",
                "category": "performance",
                "description": "Campaign performance broken down by user location",
                "fields": [
                    {"name": "geographic_view.location_type", "label": "Location Type", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "AREA_OF_INTEREST or LOCATION_OF_PRESENCE"},
                    {"name": "geographic_view.country_criterion_id", "label": "Country ID", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "Criterion ID for the country"},
                    {"name": "metrics.clicks", "label": "Clicks", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Clicks from this location"},
                    {"name": "metrics.impressions", "label": "Impressions", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Impressions from this location"},
                    {"name": "metrics.cost_micros", "label": "Cost (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Cost from this location"},
                    {"name": "metrics.conversions", "label": "Conversions", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Conversions from this location"},
                    {"name": "segments.date", "label": "Date", "data_type": "STRING", "category": "SEGMENT", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Date segment"},
                ],
                "gaql_example": "SELECT geographic_view.country_criterion_id, metrics.clicks, metrics.conversions FROM geographic_view ORDER BY metrics.clicks DESC"
            },
        ]
    },
    {
        "id": "account",
        "label": "Account",
        "description": "Customer account info, conversion actions, billing",
        "resources": [
            {
                "name": "customer",
                "label": "Customer (Account)",
                "category": "account",
                "description": "Top-level Google Ads account (customer) information",
                "fields": [
                    {"name": "customer.id", "label": "Customer ID", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "Google Ads customer/account ID"},
                    {"name": "customer.descriptive_name", "label": "Account Name", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Descriptive name of the account"},
                    {"name": "customer.currency_code", "label": "Currency", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "Currency code (USD, EUR, INR, etc.)"},
                    {"name": "customer.time_zone", "label": "Time Zone", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "Account time zone"},
                    {"name": "customer.status", "label": "Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "ENABLED, CANCELED, SUSPENDED, CLOSED"},
                    {"name": "customer.manager", "label": "Is Manager (MCC)", "data_type": "BOOLEAN", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "Whether this is a manager (MCC) account"},
                    {"name": "customer.auto_tagging_enabled", "label": "Auto-Tagging", "data_type": "BOOLEAN", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "Whether auto-tagging is enabled for tracking"},
                    {"name": "metrics.clicks", "label": "Clicks", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total account clicks"},
                    {"name": "metrics.cost_micros", "label": "Cost (micros)", "data_type": "INT64", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total account spend"},
                    {"name": "metrics.conversions", "label": "Conversions", "data_type": "DOUBLE", "category": "METRIC", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Total account conversions"},
                ],
                "gaql_example": "SELECT customer.id, customer.descriptive_name, customer.currency_code, metrics.clicks, metrics.cost_micros FROM customer"
            },
            {
                "name": "conversion_action",
                "label": "Conversion Action",
                "category": "account",
                "description": "Conversion tracking setup — purchases, sign-ups, calls, etc.",
                "fields": [
                    {"name": "conversion_action.id", "label": "Conversion ID", "data_type": "INT64", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Unique ID of the conversion action"},
                    {"name": "conversion_action.name", "label": "Conversion Name", "data_type": "STRING", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Name of the conversion action"},
                    {"name": "conversion_action.status", "label": "Status", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "ENABLED, REMOVED, HIDDEN"},
                    {"name": "conversion_action.type", "label": "Type", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "WEBPAGE, PHONE_CALL, IMPORT, APP_INSTALL, etc."},
                    {"name": "conversion_action.counting_type", "label": "Counting Type", "data_type": "ENUM", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": False, "is_repeated": False, "description": "ONE_PER_CLICK or MANY_PER_CLICK"},
                    {"name": "conversion_action.value_settings.default_value", "label": "Default Value", "data_type": "DOUBLE", "category": "ATTRIBUTE", "filterable": True, "selectable": True, "sortable": True, "is_repeated": False, "description": "Default conversion value"},
                    {"name": "conversion_action.tag_snippets", "label": "Tag Snippets", "data_type": "MESSAGE", "category": "ATTRIBUTE", "filterable": False, "selectable": True, "sortable": False, "is_repeated": True, "description": "Tracking tag snippets for this conversion"},
                ],
                "gaql_example": "SELECT conversion_action.id, conversion_action.name, conversion_action.type, conversion_action.status FROM conversion_action WHERE conversion_action.status = 'ENABLED'"
            },
        ]
    },
]

_ALL_RESOURCES: dict = {r["name"]: r for cat in DEMO_CATEGORIES for r in cat["resources"]}
_CATEGORY_MAP: dict = {c["id"]: c for c in DEMO_CATEGORIES}


# ─────────────────────────────────────────────────────────
# Real Google Ads REST API helpers
# ─────────────────────────────────────────────────────────

def _is_demo_mode() -> bool:
    return not bool(settings.GADS_DEVELOPER_TOKEN)


def _get_access_token() -> str:
    resp = requests.post(
        GADS_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": settings.GADS_CLIENT_ID,
            "client_secret": settings.GADS_CLIENT_SECRET,
            "refresh_token": settings.GADS_REFRESH_TOKEN,
        },
        timeout=30,
    )
    if not resp.ok:
        raise ConnectionError(f"Google OAuth failed [{resp.status_code}]: {resp.text[:300]}")
    return resp.json()["access_token"]


def _headers() -> dict:
    token = _get_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "developer-token": settings.GADS_DEVELOPER_TOKEN,
        "Content-Type": "application/json",
    }


def _search_fields(query: str) -> list:
    resp = requests.post(
        GADS_FIELD_SEARCH_URL,
        headers=_headers(),
        json={"query": query},
        timeout=30,
    )
    if resp.status_code == 401:
        raise ConnectionError("Google Ads authentication failed. Check credentials in .env")
    if not resp.ok:
        raise RuntimeError(f"Google Ads API error [{resp.status_code}]: {resp.text[:400]}")
    return resp.json().get("googleAdsFields", [])


# ─────────────────────────────────────────────────────────
# Public service functions
# ─────────────────────────────────────────────────────────

def test_connection() -> dict:
    if _is_demo_mode():
        total_resources = sum(len(c["resources"]) for c in DEMO_CATEGORIES)
        total_fields = sum(len(r["fields"]) for c in DEMO_CATEGORIES for r in c["resources"])
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Running in Demo Mode — showing real Google Ads API v17 field schema. "
                "Set GADS_DEVELOPER_TOKEN, GADS_CLIENT_ID, GADS_CLIENT_SECRET, "
                "GADS_REFRESH_TOKEN, GADS_CUSTOMER_ID in .env to connect to a real account."
            ),
            "categories_count": len(DEMO_CATEGORIES),
            "total_resources": total_resources,
            "total_fields": total_fields,
            "api_version": "v17",
        }

    fields = _search_fields(
        "SELECT name FROM google_ads_field WHERE category = 'RESOURCE' LIMIT 1"
    )
    return {
        "connected": True,
        "mode": "live",
        "customer_id": settings.GADS_CUSTOMER_ID,
        "sample_resources": len(fields),
    }


def list_categories() -> list[dict]:
    return [
        {
            "id": c["id"],
            "label": c["label"],
            "description": c["description"],
            "resources_count": len(c["resources"]),
        }
        for c in DEMO_CATEGORIES
    ]


def list_resources(category_id: str = None) -> dict:
    if category_id:
        if category_id not in _CATEGORY_MAP:
            raise LookupError(f"Category '{category_id}' not found.")
        resources = _CATEGORY_MAP[category_id]["resources"]
    else:
        resources = [r for c in DEMO_CATEGORIES for r in c["resources"]]

    return {
        "total": len(resources),
        "resources": [
            {
                "name": r["name"],
                "label": r["label"],
                "category": r["category"],
                "description": r["description"],
                "fields_count": len(r["fields"]),
                "gaql_example": r.get("gaql_example", ""),
            }
            for r in resources
        ],
        "mode": "demo" if _is_demo_mode() else "live",
    }


def get_resource_fields(resource_name: str) -> dict:
    if _is_demo_mode():
        if resource_name not in _ALL_RESOURCES:
            raise LookupError(
                f"Resource '{resource_name}' not found. Available: {list(_ALL_RESOURCES.keys())}"
            )
        r = _ALL_RESOURCES[resource_name]
        return {
            **r,
            "fields_count": len(r["fields"]),
            "mode": "demo",
        }

    # Live: query GoogleAdsFieldService
    query = (
        f"SELECT name, category_type, data_type, filterable, selectable, sortable, is_repeated, description "
        f"FROM google_ads_field WHERE resource_name = '{resource_name}' ORDER BY name"
    )
    raw_fields = _search_fields(query)
    fields = [
        {
            "name": f.get("name", ""),
            "label": f.get("name", "").replace(f"{resource_name}.", "").replace("_", " ").title(),
            "data_type": f.get("dataType", "STRING"),
            "category": f.get("categoryType", "ATTRIBUTE"),
            "filterable": f.get("filterable", False),
            "selectable": f.get("selectable", False),
            "sortable": f.get("sortable", False),
            "is_repeated": f.get("isRepeated", False),
            "description": f.get("description", ""),
        }
        for f in raw_fields
    ]
    return {
        "name": resource_name,
        "label": resource_name.replace("_", " ").title(),
        "category": "",
        "description": "",
        "fields": fields,
        "fields_count": len(fields),
        "gaql_example": f"SELECT {', '.join(f['name'] for f in fields[:5] if f['category'] == 'ATTRIBUTE')} FROM {resource_name} LIMIT 10",
        "mode": "live",
    }
