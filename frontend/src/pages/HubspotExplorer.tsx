import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { hubspotApi } from "../api/hubspot";
import type { HSObjectType } from "../api/hubspot";
import HubspotPropertiesPanel from "../components/HubspotPropertiesPanel";
import ConnectionBadge from "../components/ConnectionBadge";

export default function HubspotExplorer() {
  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | "standard" | "custom">("all");

  const connectionQuery = useQuery({
    queryKey: ["hs-connection"],
    queryFn: () => hubspotApi.connect().then((r) => r.data),
    retry: false,
  });

  const objectsQuery = useQuery({
    queryKey: ["hs-objects"],
    queryFn: () => hubspotApi.listObjects().then((r) => r.data),
    enabled: connectionQuery.isSuccess,
  });

  const propertiesQuery = useQuery({
    queryKey: ["hs-properties", selectedObject],
    queryFn: () =>
      hubspotApi.getProperties(selectedObject!).then((r) => r.data),
    enabled: !!selectedObject,
  });

  const allObjects: HSObjectType[] = objectsQuery.data?.objects ?? [];
  const filteredObjects = allObjects.filter((o) => {
    const matchSearch =
      o.name.toLowerCase().includes(search.toLowerCase()) ||
      o.label.toLowerCase().includes(search.toLowerCase());
    const matchType = typeFilter === "all" || o.type === typeFilter;
    return matchSearch && matchType;
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "#0f172a",
        color: "#e2e8f0",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "16px 24px",
          borderBottom: "1px solid #1e293b",
          display: "flex",
          alignItems: "center",
          gap: 16,
          background: "#0f172a",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: "#38bdf8" }}>
            ⚡ Connectors POC
          </span>
          <span
            style={{
              padding: "2px 10px",
              borderRadius: 20,
              background: "#431407",
              color: "#fb923c",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            HubSpot
          </span>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <HubspotConnectionBadge query={connectionQuery} />
        </div>
      </header>

      {/* Connection info bar */}
      {connectionQuery.data && (
        <div
          style={{
            padding: "8px 24px",
            background: "#1c0f05",
            borderBottom: "1px solid #1e293b",
            fontSize: 12,
            color: "#94a3b8",
            display: "flex",
            gap: 24,
          }}
        >
          <span>
            🔗 Portal ID:{" "}
            <b style={{ color: "#fb923c" }}>{connectionQuery.data.portal_id}</b>
          </span>
          <span>
            Type:{" "}
            <b style={{ color: "#a3e635" }}>{connectionQuery.data.account_type}</b>
          </span>
          <span>
            Currency:{" "}
            <b style={{ color: "#fbbf24" }}>{connectionQuery.data.company_currency}</b>
          </span>
          <span>
            Timezone:{" "}
            <b style={{ color: "#60a5fa" }}>{connectionQuery.data.time_zone}</b>
          </span>
          <span>
            Objects:{" "}
            <b style={{ color: "#34d399" }}>{objectsQuery.data?.total ?? "—"}</b>
          </span>
          <span>
            Auth:{" "}
            <b style={{ color: "#a5b4fc" }}>{connectionQuery.data.auth_method}</b>
          </span>
        </div>
      )}

      {/* Error state */}
      {connectionQuery.isError && (
        <div
          style={{
            margin: 24,
            padding: 20,
            background: "#1c0505",
            border: "1px solid #450a0a",
            borderRadius: 8,
            color: "#f87171",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 8 }}>
            ✗ HubSpot Connection Failed
          </div>
          <div style={{ fontSize: 13, color: "#fca5a5", marginBottom: 12 }}>
            {String(connectionQuery.error)}
          </div>
          <div style={{ fontSize: 12, color: "#94a3b8" }}>
            <b>Setup:</b> Add <code>HS_ACCESS_TOKEN=your_token</code> to{" "}
            <code>backend/.env</code>
            <br />
            Get a token at:{" "}
            <a
              href="https://app.hubspot.com/private-apps"
              target="_blank"
              style={{ color: "#fb923c" }}
            >
              HubSpot Private Apps
            </a>
          </div>
        </div>
      )}

      {/* Main layout */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left panel: object list */}
        <aside
          style={{
            width: 300,
            borderRight: "1px solid #1e293b",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e293b" }}>
            <input
              placeholder="Search objects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 6,
                border: "1px solid #334155",
                background: "#1e293b",
                color: "#e2e8f0",
                fontSize: 13,
                boxSizing: "border-box",
              }}
            />
            <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
              {(["all", "standard", "custom"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setTypeFilter(f)}
                  style={{
                    padding: "3px 10px",
                    borderRadius: 20,
                    border: "none",
                    cursor: "pointer",
                    fontSize: 11,
                    fontWeight: 600,
                    background:
                      typeFilter === f
                        ? f === "custom"
                          ? "#312e81"
                          : "#1e3a5f"
                        : "#1e293b",
                    color:
                      typeFilter === f
                        ? f === "custom"
                          ? "#a5b4fc"
                          : "#60a5fa"
                        : "#64748b",
                  }}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Object list */}
          <div style={{ overflowY: "auto", flex: 1 }}>
            {objectsQuery.isLoading && (
              <div style={{ padding: 16, color: "#94a3b8", fontSize: 13 }}>
                Loading objects...
              </div>
            )}
            {filteredObjects.map((obj) => (
              <div
                key={obj.name}
                onClick={() => setSelectedObject(obj.name)}
                style={{
                  padding: "10px 16px",
                  cursor: "pointer",
                  borderBottom: "1px solid #1e293b",
                  background:
                    selectedObject === obj.name ? "#2c1406" : "transparent",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (selectedObject !== obj.name)
                    (e.currentTarget as HTMLDivElement).style.background =
                      "#1e293b";
                }}
                onMouseLeave={(e) => {
                  if (selectedObject !== obj.name)
                    (e.currentTarget as HTMLDivElement).style.background =
                      "transparent";
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color:
                        selectedObject === obj.name ? "#fb923c" : "#e2e8f0",
                    }}
                  >
                    {obj.label}
                  </span>
                  {obj.type === "custom" && (
                    <span
                      style={{
                        fontSize: 10,
                        padding: "1px 6px",
                        borderRadius: 10,
                        background: "#312e81",
                        color: "#a5b4fc",
                      }}
                    >
                      Custom
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
                  {obj.name}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Right panel: properties */}
        <main style={{ flex: 1, overflow: "auto", padding: 24 }}>
          {!selectedObject ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                color: "#475569",
                gap: 8,
              }}
            >
              <span style={{ fontSize: 48 }}>🗂️</span>
              <span style={{ fontSize: 16 }}>
                Select an object to explore its properties
              </span>
              <span style={{ fontSize: 13 }}>
                Property names, types, field types, groups, picklist options
              </span>
            </div>
          ) : (
            <HubspotPropertiesPanel
              objectType={selectedObject}
              properties={propertiesQuery.data}
              loading={propertiesQuery.isLoading}
              error={propertiesQuery.isError ? String(propertiesQuery.error) : null}
            />
          )}
        </main>
      </div>
    </div>
  );
}

function HubspotConnectionBadge({ query }: { query: ReturnType<typeof useQuery> }) {
  if (query.isLoading) {
    return (
      <span
        style={{
          padding: "4px 12px",
          borderRadius: 20,
          background: "#1e293b",
          color: "#94a3b8",
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        ⏳ Connecting...
      </span>
    );
  }
  if (query.isError) {
    return (
      <span
        style={{
          padding: "4px 12px",
          borderRadius: 20,
          background: "#450a0a",
          color: "#f87171",
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        ✗ Not Connected
      </span>
    );
  }
  if (query.isSuccess) {
    return (
      <span
        style={{
          padding: "4px 12px",
          borderRadius: 20,
          background: "#1c1408",
          color: "#fb923c",
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        ✓ Connected to HubSpot
      </span>
    );
  }
  return null;
}
