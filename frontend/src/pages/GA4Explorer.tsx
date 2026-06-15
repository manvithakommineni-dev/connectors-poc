import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ga4Api, GA4Category, GA4Item } from "../api/ga4";
import { GA4MetadataPanel } from "../components/GA4MetadataPanel";

const CATEGORY_ICONS: Record<string, string> = {
  dimensions: "📐",
  metrics: "📊",
  custom_dimensions: "🏷️",
  custom_metrics: "🔢",
  data_streams: "🌐",
};

export function GA4Explorer() {
  const [selectedCategory, setSelectedCategory] = useState<string>("dimensions");
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const connectQuery = useQuery({
    queryKey: ["ga4-connect"],
    queryFn: ga4Api.connect,
    retry: false,
  });

  const categoriesQuery = useQuery({
    queryKey: ["ga4-categories"],
    queryFn: ga4Api.categories,
    enabled: connectQuery.isSuccess,
  });

  const itemsQuery = useQuery({
    queryKey: ["ga4-items", selectedCategory],
    queryFn: () => ga4Api.items(selectedCategory),
    enabled: connectQuery.isSuccess && !!selectedCategory,
  });

  const detailQuery = useQuery({
    queryKey: ["ga4-detail", selectedCategory, selectedItem],
    queryFn: () => ga4Api.itemDetail(selectedItem!, selectedCategory),
    enabled: !!selectedItem && !!selectedCategory,
  });

  const filteredItems = (itemsQuery.data?.items ?? []).filter(
    (item: GA4Item) =>
      !search ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.label.toLowerCase().includes(search.toLowerCase())
  );

  const setupError =
    connectQuery.error &&
    (connectQuery.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

  return (
    <div style={{ display: "flex", height: "100%", fontFamily: "system-ui, sans-serif" }}>
      {/* Sidebar — categories */}
      <div
        style={{
          width: 210,
          background: "#f8f9fa",
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "14px 16px", borderBottom: "1px solid #e0e0e0", background: "#fff" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 18 }}>📈</span>
            <span style={{ fontWeight: 700, fontSize: 15, color: "#E37400" }}>GA4</span>
          </div>
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

        {(categoriesQuery.data ?? []).map((cat: GA4Category) => (
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
              background: selectedCategory === cat.id ? "#fef7e0" : "transparent",
              color: selectedCategory === cat.id ? "#E37400" : "#333",
              fontWeight: selectedCategory === cat.id ? 600 : 400,
              fontSize: 13,
            }}
          >
            <span style={{ marginRight: 6 }}>{CATEGORY_ICONS[cat.id] ?? "📁"}</span>
            {cat.label}
            <span style={{ float: "right", fontSize: 11, color: "#888" }}>{cat.items_count}</span>
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
            <div style={{ fontWeight: 600, marginBottom: 4 }}>{connectQuery.data.property_name}</div>
            <div>ID: {connectQuery.data.property_id}</div>
            <div>{connectQuery.data.dimensions_count} dimensions</div>
            <div>{connectQuery.data.metrics_count} metrics</div>
          </div>
        )}
      </div>

      {/* Item list */}
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
              <strong>Setup required for live GA4 data:</strong>
              <ol style={{ paddingLeft: 18, marginTop: 8 }}>
                <li>Create GA4 property at analytics.google.com</li>
                <li>Google Cloud → enable Analytics Data + Admin APIs</li>
                <li>Create service account → download JSON key</li>
                <li>Add service account email to GA4 Property Access (Viewer)</li>
                <li>Set GA4_PROPERTY_ID and GA4_SERVICE_ACCOUNT_FILE in backend/.env</li>
              </ol>
              {setupError && (
                <div style={{ marginTop: 10, padding: 8, background: "#fff3e0", borderRadius: 6 }}>
                  {setupError}
                </div>
              )}
            </div>
          )}

          {filteredItems.map((item: GA4Item) => (
            <button
              key={item.name}
              onClick={() => setSelectedItem(item.name)}
              style={{
                display: "block",
                width: "100%",
                padding: "10px 14px",
                border: "none",
                borderBottom: "1px solid #f0f0f0",
                background: selectedItem === item.name ? "#fef7e0" : "#fff",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  fontSize: 13,
                  color: selectedItem === item.name ? "#E37400" : "#1a1a1a",
                }}
              >
                {item.label || item.name}
              </div>
              <code style={{ fontSize: 11, color: "#666" }}>{item.name}</code>
              {item.description && (
                <div style={{ fontSize: 11, color: "#888", marginTop: 3, lineHeight: 1.4 }}>
                  {item.description.length > 80 ? item.description.slice(0, 80) + "…" : item.description}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Detail panel */}
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
            <div style={{ fontSize: 48, marginBottom: 16 }}>📈</div>
            <div style={{ fontSize: 18, fontWeight: 600, color: "#333", marginBottom: 8 }}>
              Google Analytics 4 Metadata Explorer
            </div>
            <div style={{ fontSize: 13, maxWidth: 420, lineHeight: 1.6 }}>
              Live metadata from your GA4 property — dimensions, metrics, custom definitions, and data streams.
              No demo mode: configure credentials in .env to connect.
            </div>
          </div>
        )}

        {detailQuery.data && <GA4MetadataPanel item={detailQuery.data} />}
      </div>
    </div>
  );
}
