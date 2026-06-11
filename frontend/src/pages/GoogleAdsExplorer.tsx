import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { googleAdsApi, GAdsCategory, GAdsResourceSummary, GAdsResourceDetail } from "../api/googleads";
import { GoogleAdsMetadataPanel } from "../components/GoogleAdsMetadataPanel";

const CATEGORY_ICONS: Record<string, string> = {
  campaigns: "📣",
  adGroups:  "🗂️",
  ads:       "🖼️",
  performance: "📈",
  account:   "👤",
};

const FIELD_CATEGORY_COLORS: Record<string, string> = {
  ATTRIBUTE: "#4285F4",
  METRIC:    "#34A853",
  SEGMENT:   "#FBBC05",
  RESOURCE:  "#EA4335",
};

export function GoogleAdsExplorer() {
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [selectedResource, setSelectedResource] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const connectQuery = useQuery({
    queryKey: ["googleads-connect"],
    queryFn: googleAdsApi.connect,
    retry: 1,
  });

  const categoriesQuery = useQuery({
    queryKey: ["googleads-categories"],
    queryFn: googleAdsApi.categories,
    enabled: connectQuery.data?.connected === true,
  });

  const resourcesQuery = useQuery({
    queryKey: ["googleads-resources", selectedCategoryId],
    queryFn: () => googleAdsApi.resources(selectedCategoryId ?? undefined),
    enabled: connectQuery.data?.connected === true,
  });

  const fieldsQuery = useQuery({
    queryKey: ["googleads-fields", selectedResource],
    queryFn: () => googleAdsApi.resourceFields(selectedResource!),
    enabled: !!selectedResource,
  });

  const filteredResources = (resourcesQuery.data?.resources ?? []).filter(
    (r: GAdsResourceSummary) =>
      !search || r.label.toLowerCase().includes(search.toLowerCase()) || r.name.toLowerCase().includes(search.toLowerCase())
  );

  const isDemo = connectQuery.data?.mode === "demo";

  return (
    <div style={{ display: "flex", height: "100%", fontFamily: "system-ui, sans-serif" }}>
      {/* Left sidebar — categories */}
      <div
        style={{
          width: 200,
          background: "#f8f9fa",
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            padding: "14px 16px 10px",
            borderBottom: "1px solid #e0e0e0",
            background: "#fff",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 18 }}>📊</span>
            <span style={{ fontWeight: 700, fontSize: 15, color: "#4285F4" }}>Google Ads</span>
          </div>
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
                border: "1px solid #ffe0b2",
              }}
            >
              DEMO MODE
            </div>
          )}
          {connectQuery.data && !isDemo && (
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
              LIVE · CID {connectQuery.data.customer_id}
            </div>
          )}
        </div>

        <div style={{ padding: "10px 8px 6px", fontSize: 11, color: "#888", fontWeight: 600, textTransform: "uppercase" }}>
          Categories
        </div>

        {/* All resources option */}
        <button
          onClick={() => { setSelectedCategoryId(null); setSelectedResource(null); }}
          style={{
            margin: "0 8px 2px",
            padding: "8px 10px",
            border: "none",
            borderRadius: 6,
            cursor: "pointer",
            textAlign: "left",
            background: selectedCategoryId === null ? "#e8f0fe" : "transparent",
            color: selectedCategoryId === null ? "#1a73e8" : "#333",
            fontWeight: selectedCategoryId === null ? 600 : 400,
            fontSize: 13,
          }}
        >
          🗃️ All Resources
        </button>

        {(categoriesQuery.data ?? []).map((cat: GAdsCategory) => (
          <button
            key={cat.id}
            onClick={() => { setSelectedCategoryId(cat.id); setSelectedResource(null); }}
            style={{
              margin: "0 8px 2px",
              padding: "8px 10px",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
              textAlign: "left",
              background: selectedCategoryId === cat.id ? "#e8f0fe" : "transparent",
              color: selectedCategoryId === cat.id ? "#1a73e8" : "#333",
              fontWeight: selectedCategoryId === cat.id ? 600 : 400,
              fontSize: 13,
            }}
          >
            <span style={{ marginRight: 6 }}>{CATEGORY_ICONS[cat.id] ?? "📁"}</span>
            {cat.label}
            <span style={{ float: "right", fontSize: 11, color: "#888", marginTop: 1 }}>
              {cat.resources_count}
            </span>
          </button>
        ))}

        {/* Connection info */}
        {connectQuery.data && (
          <div style={{ margin: "auto 8px 12px", padding: "10px", background: "#fff", borderRadius: 8, border: "1px solid #e0e0e0", fontSize: 11 }}>
            <div style={{ color: "#666", marginBottom: 4 }}>API v{connectQuery.data.api_version ?? "17"}</div>
            <div style={{ color: "#333" }}>{connectQuery.data.total_resources} resources</div>
            <div style={{ color: "#333" }}>{connectQuery.data.total_fields} total fields</div>
          </div>
        )}
      </div>

      {/* Middle panel — resource list */}
      <div
        style={{
          width: 260,
          background: "#fff",
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "12px 14px 10px", borderBottom: "1px solid #e0e0e0" }}>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search resources…"
            style={{
              width: "100%",
              padding: "7px 10px",
              border: "1px solid #dadce0",
              borderRadius: 6,
              fontSize: 13,
              outline: "none",
              boxSizing: "border-box",
            }}
          />
          {resourcesQuery.data && (
            <div style={{ fontSize: 11, color: "#888", marginTop: 6 }}>
              {filteredResources.length} of {resourcesQuery.data.total} resources
            </div>
          )}
        </div>

        <div style={{ overflowY: "auto", flex: 1 }}>
          {connectQuery.isLoading && (
            <div style={{ padding: 20, color: "#888", textAlign: "center" }}>Connecting…</div>
          )}
          {connectQuery.isError && (
            <div style={{ padding: 16, color: "#c62828", fontSize: 12 }}>
              Backend error. Is the FastAPI server running on port 8000?
            </div>
          )}
          {filteredResources.map((r: GAdsResourceSummary) => (
            <button
              key={r.name}
              onClick={() => setSelectedResource(r.name)}
              style={{
                display: "block",
                width: "100%",
                padding: "10px 14px",
                border: "none",
                borderBottom: "1px solid #f0f0f0",
                background: selectedResource === r.name ? "#e8f0fe" : "#fff",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 13, color: selectedResource === r.name ? "#1a73e8" : "#1a1a1a" }}>
                {r.label}
              </div>
              <code style={{ fontSize: 11, color: "#666" }}>{r.name}</code>
              {r.description && (
                <div style={{ fontSize: 11, color: "#888", marginTop: 3, lineHeight: 1.4 }}>
                  {r.description.length > 70 ? r.description.slice(0, 70) + "…" : r.description}
                </div>
              )}
              <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
                <span style={{ fontSize: 10, color: "#666", background: "#f1f3f4", padding: "2px 6px", borderRadius: 10 }}>
                  {r.fields_count} fields
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Right panel — field detail */}
      <div style={{ flex: 1, overflowY: "auto", padding: 20, background: "#f8f9fa" }}>
        {!selectedResource && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "60%",
              color: "#888",
            }}
          >
            <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
            <div style={{ fontSize: 18, fontWeight: 600, color: "#333", marginBottom: 8 }}>
              Google Ads Metadata Explorer
            </div>
            <div style={{ fontSize: 13, maxWidth: 400, textAlign: "center", lineHeight: 1.6 }}>
              Select a resource from the left to explore its fields, metrics, and segments.
              Google Ads uses GAQL (Google Ads Query Language) to query any field.
            </div>

            {/* Field category legend */}
            <div
              style={{
                marginTop: 28,
                background: "#fff",
                borderRadius: 10,
                padding: "16px 20px",
                border: "1px solid #e0e0e0",
                width: "100%",
                maxWidth: 420,
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10, color: "#333" }}>
                Google Ads Field Categories
              </div>
              {Object.entries(FIELD_CATEGORY_COLORS).map(([cat, color]) => (
                <div key={cat} style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 8 }}>
                  <span
                    style={{
                      display: "inline-block",
                      minWidth: 80,
                      padding: "2px 8px",
                      borderRadius: 4,
                      fontSize: 11,
                      fontWeight: 700,
                      background: color + "18",
                      color,
                      border: `1px solid ${color}44`,
                      textTransform: "uppercase",
                    }}
                  >
                    {cat}
                  </span>
                  <span style={{ fontSize: 12, color: "#666", lineHeight: 1.5 }}>
                    {cat === "ATTRIBUTE" && "Descriptive fields — campaign.name, status, budget"}
                    {cat === "METRIC" && "Performance numbers — clicks, impressions, cost, conversions"}
                    {cat === "SEGMENT" && "Grouping dimensions — date, device, ad_network_type"}
                    {cat === "RESOURCE" && "Related resource references"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {fieldsQuery.isLoading && selectedResource && (
          <div style={{ padding: 40, textAlign: "center", color: "#888" }}>
            Loading fields for <strong>{selectedResource}</strong>…
          </div>
        )}

        {fieldsQuery.data && (
          <GoogleAdsMetadataPanel resource={fieldsQuery.data as GAdsResourceDetail} />
        )}
      </div>
    </div>
  );
}
