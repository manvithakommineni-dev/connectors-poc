import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { sapApi } from "../api/sap";
import type { SAPService, SAPEntitySummary } from "../api/sap";
import SAPMetadataPanel from "../components/SAPMetadataPanel";

export default function SAPExplorer() {
  const [selectedService, setSelectedService] = useState<string>("API_BUSINESS_PARTNER");
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const connectionQuery = useQuery({
    queryKey: ["sap-connection"],
    queryFn: () => sapApi.connect().then((r) => r.data),
    retry: false,
  });

  const servicesQuery = useQuery({
    queryKey: ["sap-services"],
    queryFn: () => sapApi.listServices().then((r) => r.data),
  });

  const entitiesQuery = useQuery({
    queryKey: ["sap-entities", selectedService],
    queryFn: () => sapApi.getEntities(selectedService).then((r) => r.data),
    enabled: !!selectedService && connectionQuery.isSuccess,
  });

  const fieldsQuery = useQuery({
    queryKey: ["sap-fields", selectedService, selectedEntity],
    queryFn: () =>
      sapApi.getEntityFields(selectedService, selectedEntity!).then((r) => r.data),
    enabled: !!selectedEntity,
  });

  const filteredEntities: SAPEntitySummary[] = (
    entitiesQuery.data?.entities ?? []
  ).filter(
    (e) =>
      e.name.toLowerCase().includes(search.toLowerCase()) ||
      e.entity_set_name.toLowerCase().includes(search.toLowerCase())
  );

  const handleServiceChange = (svc: string) => {
    setSelectedService(svc);
    setSelectedEntity(null);
    setSearch("");
  };

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
              background: "#1a0a2e",
              color: "#c084fc",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            SAP
          </span>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <SAPConnectionBadge connected={connectionQuery.isSuccess} loading={connectionQuery.isLoading} error={connectionQuery.isError} />
        </div>
      </header>

      {/* Connection info bar */}
      {connectionQuery.data && (
        <div
          style={{
            padding: "8px 24px",
            background: "#130a1f",
            borderBottom: "1px solid #1e293b",
            fontSize: 12,
            color: "#94a3b8",
            display: "flex",
            gap: 24,
            flexWrap: "wrap",
          }}
        >
          <span>
            🔗 Auth: <b style={{ color: "#c084fc" }}>{connectionQuery.data.auth_type}</b>
          </span>
          <span>
            Namespace: <b style={{ color: "#a3e635" }}>{connectionQuery.data.namespace}</b>
          </span>
          <span>
            Entity Types:{" "}
            <b style={{ color: "#f59e0b" }}>{connectionQuery.data.entity_types_found}</b>
          </span>
          <span>
            Entity Sets:{" "}
            <b style={{ color: "#34d399" }}>{connectionQuery.data.entity_sets_found}</b>
          </span>
          <span>
            Service:{" "}
            <b style={{ color: "#60a5fa" }}>{connectionQuery.data.test_service}</b>
          </span>
        </div>
      )}

      {/* Error / setup guide */}
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
            ✗ SAP Connection Failed
          </div>
          <div style={{ fontSize: 13, color: "#fca5a5", marginBottom: 12 }}>
            {String(connectionQuery.error)}
          </div>
          <div style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.8 }}>
            <b style={{ color: "#e2e8f0" }}>Setup (free — no SAP license needed):</b>
            <ol style={{ margin: "8px 0 0 0", paddingLeft: 20 }}>
              <li>
                Go to{" "}
                <a href="https://api.sap.com" target="_blank" style={{ color: "#c084fc" }}>
                  https://api.sap.com
                </a>{" "}
                and create a <b>free account</b>
              </li>
              <li>Log in → click your avatar (top right) → <b>"Settings"</b></li>
              <li>Click <b>"Show API Key"</b> → copy the key</li>
              <li>
                Add to <code>backend/.env</code>:{" "}
                <code style={{ color: "#c084fc" }}>SAP_API_KEY=your_key_here</code>
              </li>
              <li>Restart the backend server</li>
            </ol>
          </div>
        </div>
      )}

      {/* Service selector + main layout */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left panel */}
        <aside
          style={{
            width: 320,
            borderRight: "1px solid #1e293b",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          {/* Service selector */}
          <div
            style={{
              padding: "12px 16px",
              borderBottom: "1px solid #1e293b",
              background: "#020617",
            }}
          >
            <div style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
              OData Service
            </div>
            <select
              value={selectedService}
              onChange={(e) => handleServiceChange(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 10px",
                borderRadius: 6,
                border: "1px solid #334155",
                background: "#1e293b",
                color: "#e2e8f0",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              {(servicesQuery.data?.services ?? []).map((svc: SAPService) => (
                <option key={svc.name} value={svc.name}>
                  {svc.label} ({svc.name})
                </option>
              ))}
            </select>
            {entitiesQuery.data && (
              <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>
                {entitiesQuery.data.total} entity types · namespace:{" "}
                <span style={{ color: "#94a3b8" }}>{entitiesQuery.data.namespace}</span>
              </div>
            )}
          </div>

          {/* Search */}
          <div style={{ padding: "10px 16px", borderBottom: "1px solid #1e293b" }}>
            <input
              placeholder="Search entity types..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: "100%",
                padding: "7px 12px",
                borderRadius: 6,
                border: "1px solid #334155",
                background: "#1e293b",
                color: "#e2e8f0",
                fontSize: 13,
                boxSizing: "border-box",
              }}
            />
          </div>

          {/* Entity list */}
          <div style={{ overflowY: "auto", flex: 1 }}>
            {entitiesQuery.isLoading && (
              <div style={{ padding: 16, color: "#94a3b8", fontSize: 13 }}>
                ⏳ Loading entities...
              </div>
            )}
            {filteredEntities.map((entity) => (
              <div
                key={entity.name}
                onClick={() => setSelectedEntity(entity.name)}
                style={{
                  padding: "10px 16px",
                  cursor: "pointer",
                  borderBottom: "1px solid #1e293b",
                  background:
                    selectedEntity === entity.name ? "#1a0a2e" : "transparent",
                  transition: "background 0.1s",
                }}
                onMouseEnter={(e) => {
                  if (selectedEntity !== entity.name)
                    (e.currentTarget as HTMLDivElement).style.background = "#1e293b";
                }}
                onMouseLeave={(e) => {
                  if (selectedEntity !== entity.name)
                    (e.currentTarget as HTMLDivElement).style.background = "transparent";
                }}
              >
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: selectedEntity === entity.name ? "#c084fc" : "#e2e8f0",
                    fontFamily: "monospace",
                  }}
                >
                  {entity.entity_set_name || entity.name}
                </div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 2, display: "flex", gap: 8 }}>
                  <span>{entity.fields_count} fields</span>
                  {entity.key_fields.length > 0 && (
                    <span>🔑 {entity.key_fields.join(", ")}</span>
                  )}
                  {entity.nav_properties_count > 0 && (
                    <span>↗ {entity.nav_properties_count} rels</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Right panel: fields */}
        <main style={{ flex: 1, overflow: "auto", padding: 24 }}>
          {!selectedEntity ? (
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
              <span style={{ fontSize: 48 }}>🏢</span>
              <span style={{ fontSize: 16 }}>Select an entity type to explore its fields</span>
              <span style={{ fontSize: 13 }}>
                Field names, OData types, key fields, navigation properties
              </span>
            </div>
          ) : (
            <SAPMetadataPanel
              entityName={selectedEntity}
              data={fieldsQuery.data}
              loading={fieldsQuery.isLoading}
              error={fieldsQuery.isError ? String(fieldsQuery.error) : null}
            />
          )}
        </main>
      </div>
    </div>
  );
}

function SAPConnectionBadge({
  connected,
  loading,
  error,
}: {
  connected: boolean;
  loading: boolean;
  error: boolean;
}) {
  if (loading)
    return (
      <span style={{ padding: "4px 12px", borderRadius: 20, background: "#1e293b", color: "#94a3b8", fontSize: 12, fontWeight: 600 }}>
        ⏳ Connecting...
      </span>
    );
  if (error)
    return (
      <span style={{ padding: "4px 12px", borderRadius: 20, background: "#450a0a", color: "#f87171", fontSize: 12, fontWeight: 600 }}>
        ✗ Not Connected
      </span>
    );
  if (connected)
    return (
      <span style={{ padding: "4px 12px", borderRadius: 20, background: "#1a0a2e", color: "#c084fc", fontSize: 12, fontWeight: 600 }}>
        ✓ Connected to SAP
      </span>
    );
  return null;
}
