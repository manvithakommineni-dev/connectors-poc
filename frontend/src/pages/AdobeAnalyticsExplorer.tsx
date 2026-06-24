import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { adobeAnalyticsApi } from "../api/adobeanalytics";
import type { AdobeAnalyticsCategory, AdobeAnalyticsItem } from "../api/adobeanalytics";
import { AdobeAnalyticsMetadataPanel } from "../components/AdobeAnalyticsMetadataPanel";

const CATEGORY_ICONS: Record<string, string> = {
  report_suite: "🏢",
  dimensions: "📐",
  metrics: "📊",
  segments: "🎯",
  dimension_fields: "📋",
  metric_fields: "📋",
  segment_fields: "📋",
  report_fields: "📄",
};

export function AdobeAnalyticsExplorer() {
  const [selectedCategory, setSelectedCategory] = useState<string>("dimension_fields");
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const connectQuery = useQuery({
    queryKey: ["adobeanalytics-connect"],
    queryFn: adobeAnalyticsApi.connect,
    retry: false,
  });

  const categoriesQuery = useQuery({
    queryKey: ["adobeanalytics-categories"],
    queryFn: adobeAnalyticsApi.categories,
    enabled: connectQuery.isSuccess,
  });

  const itemsQuery = useQuery({
    queryKey: ["adobeanalytics-items", selectedCategory],
    queryFn: () => adobeAnalyticsApi.items(selectedCategory),
    enabled: connectQuery.isSuccess && !!selectedCategory,
  });

  const detailQuery = useQuery({
    queryKey: ["adobeanalytics-detail", selectedCategory, selectedItem],
    queryFn: () => adobeAnalyticsApi.itemDetail(selectedItem!, selectedCategory),
    enabled: !!selectedItem && !!selectedCategory,
  });

  const filteredItems = (itemsQuery.data?.items ?? []).filter(
    (item: AdobeAnalyticsItem) =>
      !search ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.label.toLowerCase().includes(search.toLowerCase())
  );

  const isDemo = connectQuery.data?.mode === "demo";
  const isLive = connectQuery.data?.mode === "live";

  return (
    <div style={{ display: "flex", height: "100%", fontFamily: "system-ui, sans-serif" }}>
      <div
        style={{
          width: 230,
          background: "#f8f9fa",
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "14px 16px", borderBottom: "1px solid #e0e0e0", background: "#fff" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 18 }}>📊</span>
            <span style={{ fontWeight: 700, fontSize: 14, color: "#EB1000" }}>Adobe Analytics</span>
          </div>
          <div style={{ fontSize: 10, color: "#B80000", marginTop: 2 }}>Analytics 2.0 API</div>
          {isLive && (
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
          {isDemo && (
            <div
              style={{
                marginTop: 6,
                background: "#fff3e0",
                color: "#e65100",
                borderRadius: 6,
                padding: "4px 8px",
                fontSize: 11,
                fontWeight: 600,
                border: "1px solid #ffcc80",
              }}
            >
              DEMO
            </div>
          )}
        </div>

        <div style={{ padding: "10px 8px 6px", fontSize: 11, color: "#888", fontWeight: 600 }}>
          CATEGORIES
        </div>

        {(categoriesQuery.data ?? []).map((cat: AdobeAnalyticsCategory) => (
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
              background: selectedCategory === cat.id ? "#fde8e8" : "transparent",
              color: selectedCategory === cat.id ? "#EB1000" : "#333",
              fontWeight: selectedCategory === cat.id ? 600 : 400,
              fontSize: 12,
            }}
          >
            <span style={{ marginRight: 6 }}>{CATEGORY_ICONS[cat.id] ?? "📁"}</span>
            {cat.label}
            <span style={{ float: "right", fontSize: 10, color: "#888" }}>{cat.items_count}</span>
          </button>
        ))}

        {connectQuery.data && isLive && (
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
            <div style={{ fontWeight: 600 }}>{connectQuery.data.report_suite_name}</div>
            <div>{connectQuery.data.report_suite_id}</div>
            <div>{connectQuery.data.company_id}</div>
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
              {itemsQuery.data.message && (
                <div style={{ marginTop: 4, color: "#e65100" }}>{itemsQuery.data.message}</div>
              )}
            </div>
          )}
        </div>

        <div style={{ overflowY: "auto", flex: 1 }}>
          {isDemo && (
            <div style={{ padding: 16, fontSize: 12, color: "#555", lineHeight: 1.6 }}>
              <strong>Demo mode — Analytics 2.0 schemas available now.</strong>
              <ol style={{ paddingLeft: 18, marginTop: 8 }}>
                <li>Adobe Developer Console → OAuth Server-to-Server</li>
                <li>Add Adobe Analytics API + product profile</li>
                <li>Set ADOBE_CLIENT_ID, ADOBE_CLIENT_SECRET</li>
                <li>Set ADOBE_GLOBAL_COMPANY_ID + ADOBE_REPORT_SUITE_ID</li>
                <li>Requires paid Analytics license for live data</li>
              </ol>
            </div>
          )}

          {filteredItems.map((item: AdobeAnalyticsItem) => (
            <button
              key={item.name}
              onClick={() => setSelectedItem(item.name)}
              style={{
                display: "block",
                width: "100%",
                padding: "10px 14px",
                border: "none",
                borderBottom: "1px solid #f0f0f0",
                background: selectedItem === item.name ? "#fde8e8" : "#fff",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  fontSize: 13,
                  color: selectedItem === item.name ? "#EB1000" : "#1a1a1a",
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
            <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
            <div style={{ fontSize: 18, fontWeight: 600, color: "#333", marginBottom: 8 }}>
              Adobe Analytics Metadata Explorer
            </div>
            <div style={{ fontSize: 13, maxWidth: 440, lineHeight: 1.6 }}>
              Dimensions, metrics, segments, and report suite metadata via Analytics 2.0 API.
              Demo mode works now; add Adobe credentials in .env for live data (license required).
            </div>
          </div>
        )}

        {detailQuery.data && <AdobeAnalyticsMetadataPanel item={detailQuery.data} />}
      </div>
    </div>
  );
}
