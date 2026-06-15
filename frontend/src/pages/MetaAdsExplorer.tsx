import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { metaAdsApi, MetaCategory, MetaItem } from "../api/metaads";
import { MetaAdsMetadataPanel } from "../components/MetaAdsMetadataPanel";

const CATEGORY_ICONS: Record<string, string> = {
  account: "👤",
  campaigns: "📣",
  adsets: "🎯",
  ads: "🖼️",
  campaign_fields: "📐",
  adset_fields: "📐",
  ad_fields: "📐",
  insights_metrics: "📊",
  insights_breakdowns: "🔀",
};

export function MetaAdsExplorer() {
  const [selectedCategory, setSelectedCategory] = useState<string>("campaigns");
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const connectQuery = useQuery({
    queryKey: ["metaads-connect"],
    queryFn: metaAdsApi.connect,
    retry: false,
  });

  const categoriesQuery = useQuery({
    queryKey: ["metaads-categories"],
    queryFn: metaAdsApi.categories,
    enabled: connectQuery.isSuccess,
  });

  const itemsQuery = useQuery({
    queryKey: ["metaads-items", selectedCategory],
    queryFn: () => metaAdsApi.items(selectedCategory),
    enabled: connectQuery.isSuccess && !!selectedCategory,
  });

  const detailQuery = useQuery({
    queryKey: ["metaads-detail", selectedCategory, selectedItem],
    queryFn: () => metaAdsApi.itemDetail(selectedItem!, selectedCategory),
    enabled: !!selectedItem && !!selectedCategory,
  });

  const filteredItems = (itemsQuery.data?.items ?? []).filter(
    (item: MetaItem) =>
      !search ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.label.toLowerCase().includes(search.toLowerCase())
  );

  const setupError =
    connectQuery.error &&
    (connectQuery.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

  return (
    <div style={{ display: "flex", height: "100%", fontFamily: "system-ui, sans-serif" }}>
      <div
        style={{
          width: 220,
          background: "#f8f9fa",
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "14px 16px", borderBottom: "1px solid #e0e0e0", background: "#fff" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 18 }}>📱</span>
            <span style={{ fontWeight: 700, fontSize: 14, color: "#1877F2" }}>Meta Ads</span>
          </div>
          <div style={{ fontSize: 10, color: "#E1306C", marginTop: 2 }}>Facebook + Instagram</div>
          {connectQuery.isSuccess && (
            <div
              style={{
                marginTop: 6,
                background: "#e8f5e9",
                color: "#2e7d32",
                borderRadius: 6,
                padding: "4px 8px",
                fontSize: 11,
                fontWeight: 600,
                border: "1px solid #a5d6a7",
              }}
            >
              LIVE
            </div>
          )}
          {connectQuery.isError && (
            <div
              style={{
                marginTop: 6,
                background: "#ffebee",
                color: "#c62828",
                borderRadius: 6,
                padding: "4px 8px",
                fontSize: 11,
                fontWeight: 600,
                border: "1px solid #ffcdd2",
              }}
            >
              NOT CONNECTED
            </div>
          )}
        </div>

        <div style={{ padding: "10px 8px 6px", fontSize: 11, color: "#888", fontWeight: 600 }}>
          CATEGORIES
        </div>

        {(categoriesQuery.data ?? []).map((cat: MetaCategory) => (
          <button
            key={cat.id}
            onClick={() => {
              setSelectedCategory(cat.id);
              setSelectedItem(null);
            }}
            style={{
              margin: "0 8px 2px",
              padding: "8px 10px",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
              textAlign: "left",
              background: selectedCategory === cat.id ? "#e7f3ff" : "transparent",
              color: selectedCategory === cat.id ? "#1877F2" : "#333",
              fontWeight: selectedCategory === cat.id ? 600 : 400,
              fontSize: 12,
            }}
          >
            <span style={{ marginRight: 6 }}>{CATEGORY_ICONS[cat.id] ?? "📁"}</span>
            {cat.label}
            <span style={{ float: "right", fontSize: 10, color: "#888" }}>{cat.items_count}</span>
          </button>
        ))}

        {connectQuery.data && (
          <div
            style={{
              margin: "auto 8px 12px",
              padding: "10px",
              background: "#fff",
              borderRadius: 8,
              border: "1px solid #e0e0e0",
              fontSize: 11,
            }}
          >
            <div style={{ fontWeight: 600 }}>{connectQuery.data.ad_account_name}</div>
            <div>act_{connectQuery.data.ad_account_id}</div>
            <div>{connectQuery.data.currency} · {connectQuery.data.timezone}</div>
          </div>
        )}
      </div>

      <div
        style={{
          width: 280,
          background: "#fff",
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "12px 14px", borderBottom: "1px solid #e0e0e0" }}>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search…"
            disabled={connectQuery.isError}
            style={{
              width: "100%",
              padding: "7px 10px",
              border: "1px solid #dadce0",
              borderRadius: 6,
              fontSize: 13,
              boxSizing: "border-box",
            }}
          />
          {itemsQuery.data && (
            <div style={{ fontSize: 11, color: "#888", marginTop: 6 }}>
              {filteredItems.length} of {itemsQuery.data.total}
            </div>
          )}
        </div>

        <div style={{ overflowY: "auto", flex: 1 }}>
          {connectQuery.isError && (
            <div style={{ padding: 16, fontSize: 12, color: "#c62828", lineHeight: 1.6 }}>
              <strong>Setup required for live Meta Ads data:</strong>
              <ol style={{ paddingLeft: 18, marginTop: 8 }}>
                <li>Create Meta Developer app → Business type → Marketing API</li>
                <li>Generate access token with <code>ads_read</code></li>
                <li>Get Ad Account ID from Business Manager</li>
                <li>Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID in backend/.env</li>
              </ol>
              {setupError && (
                <div style={{ marginTop: 10, padding: 8, background: "#fff3e0", borderRadius: 6 }}>
                  {setupError}
                </div>
              )}
            </div>
          )}

          {filteredItems.map((item: MetaItem) => (
            <button
              key={item.name}
              onClick={() => setSelectedItem(item.name)}
              style={{
                display: "block",
                width: "100%",
                padding: "10px 14px",
                border: "none",
                borderBottom: "1px solid #f0f0f0",
                background: selectedItem === item.name ? "#e7f3ff" : "#fff",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  fontSize: 13,
                  color: selectedItem === item.name ? "#1877F2" : "#1a1a1a",
                }}
              >
                {item.label || item.name}
              </div>
              <code style={{ fontSize: 11, color: "#666" }}>{item.name}</code>
              {item.description && (
                <div style={{ fontSize: 11, color: "#888", marginTop: 3 }}>{item.description}</div>
              )}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: 20, background: "#f8f9fa" }}>
        {!selectedItem && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "60%",
              color: "#888",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 48, marginBottom: 16 }}>📱</div>
            <div style={{ fontSize: 18, fontWeight: 600, color: "#333", marginBottom: 8 }}>
              Meta Ads Metadata Explorer
            </div>
            <div style={{ fontSize: 13, maxWidth: 440, lineHeight: 1.6 }}>
              Live data from Facebook + Instagram via Marketing API — campaigns, ad sets, ads,
              field schemas, and insights metrics. No demo mode.
            </div>
          </div>
        )}

        {detailQuery.data && <MetaAdsMetadataPanel item={detailQuery.data} />}
      </div>
    </div>
  );
}
