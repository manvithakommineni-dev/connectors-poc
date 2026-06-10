import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { oracleApi, OracleResourceSummary } from "../api/oracle";
import { OracleMetadataPanel } from "../components/OracleMetadataPanel";

const MODULE_COLORS: Record<string, string> = {
  financials: "#c0392b",
  procurement: "#8e44ad",
  orderManagement: "#2980b9",
  hcm: "#27ae60",
  projects: "#d35400",
  supplyChain: "#16a085",
};

const MODULE_ICONS: Record<string, string> = {
  financials: "💰",
  procurement: "🛒",
  orderManagement: "📦",
  hcm: "👥",
  projects: "📋",
  supplyChain: "🏭",
};

export default function OracleExplorer() {
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [selectedResource, setSelectedResource] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showAllResources, setShowAllResources] = useState(false);

  const connectQuery = useQuery({
    queryKey: ["oracle-connect"],
    queryFn: oracleApi.connect,
    retry: 1,
  });

  const modulesQuery = useQuery({
    queryKey: ["oracle-modules"],
    queryFn: oracleApi.listModules,
    enabled: connectQuery.isSuccess,
  });

  const resourcesQuery = useQuery({
    queryKey: ["oracle-module-resources", selectedModule],
    queryFn: () => oracleApi.getModuleResources(selectedModule!),
    enabled: !!selectedModule && !showAllResources,
  });

  const allResourcesQuery = useQuery({
    queryKey: ["oracle-all-resources"],
    queryFn: oracleApi.getAllResources,
    enabled: showAllResources,
  });

  const activeResources: OracleResourceSummary[] = showAllResources
    ? (allResourcesQuery.data?.resources ?? [])
    : (resourcesQuery.data?.resources ?? []);

  const filteredResources = activeResources.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.description.toLowerCase().includes(search.toLowerCase())
  );

  const isDemo = connectQuery.data?.mode === "demo";

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #c0392b 0%, #e74c3c 100%)",
          borderRadius: 12,
          padding: "24px 28px",
          color: "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <span style={{ fontSize: 32 }}>⚙️</span>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>Oracle Fusion ERP</div>
            <div style={{ fontSize: 13, opacity: 0.85 }}>
              Financials · Procurement · Order Management · HCM · Projects · Supply Chain
            </div>
          </div>
          {isDemo && (
            <span
              style={{
                marginLeft: "auto",
                background: "rgba(255,255,255,0.25)",
                borderRadius: 6,
                padding: "4px 12px",
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: 1,
              }}
            >
              DEMO MODE
            </span>
          )}
        </div>

        {/* Connection status */}
        {connectQuery.isLoading && (
          <div style={{ fontSize: 13, opacity: 0.8 }}>Connecting…</div>
        )}
        {connectQuery.isError && (
          <div
            style={{
              background: "rgba(255,255,255,0.2)",
              borderRadius: 6,
              padding: "8px 14px",
              fontSize: 13,
            }}
          >
            ❌ Connection failed — check backend is running on port 8000
          </div>
        )}
        {connectQuery.isSuccess && connectQuery.data && (
          <div
            style={{
              background: "rgba(255,255,255,0.2)",
              borderRadius: 6,
              padding: "10px 14px",
              fontSize: 13,
              display: "flex",
              flexWrap: "wrap",
              gap: 16,
            }}
          >
            <span>✅ Connected</span>
            {connectQuery.data.modules_count != null && (
              <span>Modules: <strong>{connectQuery.data.modules_count}</strong></span>
            )}
            {connectQuery.data.total_resources != null && (
              <span>Resources: <strong>{connectQuery.data.total_resources}</strong></span>
            )}
            {connectQuery.data.message && !isDemo && (
              <span>{connectQuery.data.message}</span>
            )}
            {isDemo && (
              <span style={{ opacity: 0.8 }}>
                Built-in Oracle Fusion ERP schema · No credentials required
              </span>
            )}
          </div>
        )}
      </div>

      {/* Demo mode info banner */}
      {isDemo && (
        <div
          style={{
            background: "#fff9e6",
            border: "1px solid #ffeaa7",
            borderRadius: 8,
            padding: "12px 16px",
            fontSize: 13,
            color: "#6c5c00",
          }}
        >
          <strong>Demo Mode Active</strong> — This shows the real Oracle Fusion Cloud ERP metadata structure
          (Modules, Resources, Attributes) without needing an Oracle account.
          To connect a real Oracle Cloud instance, add <code>ORACLE_BASE_URL</code>,{" "}
          <code>ORACLE_USERNAME</code>, <code>ORACLE_PASSWORD</code> to <code>backend/.env</code>.
        </div>
      )}

      <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
        {/* Left panel: Modules + Resources */}
        <div
          style={{
            width: 300,
            minWidth: 300,
            background: "#fff",
            borderRadius: 10,
            border: "1px solid #e9ecef",
            overflow: "hidden",
          }}
        >
          {/* Module selector */}
          <div
            style={{
              padding: "12px 16px",
              background: "#f8f9fa",
              borderBottom: "1px solid #e9ecef",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontWeight: 600, fontSize: 13 }}>
              Modules ({modulesQuery.data?.total ?? 0})
            </span>
            <button
              onClick={() => {
                setShowAllResources((v) => !v);
                setSelectedResource(null);
              }}
              style={{
                border: "1px solid #e9ecef",
                borderRadius: 4,
                padding: "3px 8px",
                fontSize: 11,
                background: showAllResources ? "#e74c3c" : "#fff",
                color: showAllResources ? "#fff" : "#636e72",
                cursor: "pointer",
              }}
            >
              {showAllResources ? "By Module" : "All Resources"}
            </button>
          </div>

          {/* Module list */}
          {!showAllResources && (
            <div>
              {modulesQuery.isLoading && (
                <div style={{ padding: 16, color: "#636e72", fontSize: 13 }}>Loading modules…</div>
              )}
              {modulesQuery.data?.modules.map((mod) => (
                <div
                  key={mod.id}
                  onClick={() => {
                    setSelectedModule(mod.id);
                    setSelectedResource(null);
                    setSearch("");
                  }}
                  style={{
                    padding: "10px 16px",
                    cursor: "pointer",
                    borderBottom: "1px solid #f1f3f5",
                    background: selectedModule === mod.id ? "#fff5f5" : "transparent",
                    borderLeft: `3px solid ${selectedModule === mod.id ? MODULE_COLORS[mod.id] ?? "#e74c3c" : "transparent"}`,
                    transition: "background 0.15s",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                    <span>{MODULE_ICONS[mod.id] ?? "📁"}</span>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>{mod.label}</span>
                    <span
                      style={{
                        marginLeft: "auto",
                        background: "#f1f3f5",
                        borderRadius: 10,
                        padding: "1px 7px",
                        fontSize: 11,
                        color: "#636e72",
                      }}
                    >
                      {mod.resources_count}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: "#888", lineHeight: 1.4 }}>
                    {mod.description.split(",")[0]}…
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Resource search */}
          {(selectedModule || showAllResources) && (
            <div style={{ borderTop: "2px solid #e9ecef" }}>
              <div style={{ padding: "10px 12px", background: "#f8f9fa", borderBottom: "1px solid #e9ecef" }}>
                <input
                  type="text"
                  placeholder="Search resources…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px 10px",
                    border: "1px solid #dee2e6",
                    borderRadius: 6,
                    fontSize: 12,
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div style={{ maxHeight: 280, overflowY: "auto" }}>
                {(resourcesQuery.isLoading || allResourcesQuery.isLoading) && (
                  <div style={{ padding: 12, color: "#636e72", fontSize: 12 }}>Loading resources…</div>
                )}
                {filteredResources.map((res) => {
                  const modColor = MODULE_COLORS[res.module] ?? "#e74c3c";
                  return (
                    <div
                      key={res.name}
                      onClick={() => setSelectedResource(res.name)}
                      style={{
                        padding: "9px 14px",
                        cursor: "pointer",
                        borderBottom: "1px solid #f1f3f5",
                        background: selectedResource === res.name ? "#fff5f5" : "transparent",
                        borderLeft: `3px solid ${selectedResource === res.name ? modColor : "transparent"}`,
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: 12, fontFamily: "monospace" }}>
                        {res.title}
                      </div>
                      <div
                        style={{
                          fontSize: 11,
                          color: "#888",
                          fontFamily: "monospace",
                          marginBottom: 2,
                        }}
                      >
                        {res.name}
                      </div>
                      <div style={{ display: "flex", gap: 8, fontSize: 10, color: "#aaa" }}>
                        <span>{res.attributes_count} attrs</span>
                        {res.children_count > 0 && <span>{res.children_count} children</span>}
                        {showAllResources && res.module && (
                          <span
                            style={{
                              background: modColor,
                              color: "#fff",
                              borderRadius: 3,
                              padding: "0 5px",
                            }}
                          >
                            {res.module}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
                {filteredResources.length === 0 && !resourcesQuery.isLoading && !allResourcesQuery.isLoading && (
                  <div style={{ padding: 16, color: "#aaa", fontSize: 12, textAlign: "center" }}>
                    No resources found
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right panel: Metadata */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selectedResource && (
            <div
              style={{
                background: "#fff",
                borderRadius: 10,
                border: "1px solid #e9ecef",
                padding: 40,
                textAlign: "center",
                color: "#aaa",
              }}
            >
              <div style={{ fontSize: 48, marginBottom: 12 }}>⚙️</div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
                {!selectedModule && !showAllResources
                  ? "Select a module to browse Oracle ERP resources"
                  : "Select a resource to view its metadata"}
              </div>
              <div style={{ fontSize: 13 }}>
                {!selectedModule && !showAllResources
                  ? "Or click 'All Resources' to see everything at once"
                  : "Attributes, data types, required flags, child resources will appear here"}
              </div>
            </div>
          )}
          {selectedResource && <OracleMetadataPanel resourceName={selectedResource} />}
        </div>
      </div>
    </div>
  );
}
