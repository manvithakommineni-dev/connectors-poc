import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { salesforceApi } from "../api/salesforce";
import type { SFObject, SFObjectMetadata } from "../api/salesforce";
import ObjectList from "../components/ObjectList";
import MetadataPanel from "../components/MetadataPanel";
import ConnectionBadge from "../components/ConnectionBadge";
import SetupGuide from "../components/SetupGuide";

export default function SalesforceExplorer() {
  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [queryableOnly, setQueryableOnly] = useState(true);
  const [customOnly, setCustomOnly] = useState(false);
  const [search, setSearch] = useState("");

  const connectionQuery = useQuery({
    queryKey: ["sf-connection"],
    queryFn: () => salesforceApi.connect().then((r) => r.data),
    retry: false,
  });

  const objectsQuery = useQuery({
    queryKey: ["sf-objects", queryableOnly, customOnly],
    queryFn: () =>
      salesforceApi.listObjects(queryableOnly, customOnly).then((r) => r.data),
    enabled: connectionQuery.isSuccess,
  });

  const metadataQuery = useQuery({
    queryKey: ["sf-metadata", selectedObject],
    queryFn: () =>
      salesforceApi.getMetadata(selectedObject!).then((r) => r.data as SFObjectMetadata),
    enabled: !!selectedObject,
  });

  const filteredObjects: SFObject[] = ((objectsQuery.data?.objects ?? []) as SFObject[]).filter(
    (o: SFObject) =>
      o.name.toLowerCase().includes(search.toLowerCase()) ||
      o.label.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0f172a", color: "#e2e8f0", fontFamily: "Inter, system-ui, sans-serif" }}>
      {/* Header */}
      <header style={{ padding: "16px 24px", borderBottom: "1px solid #1e293b", display: "flex", alignItems: "center", gap: 16, background: "#0f172a" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: "#38bdf8" }}>⚡ Connectors POC</span>
          <span style={{ padding: "2px 10px", borderRadius: 20, background: "#1e3a5f", color: "#60a5fa", fontSize: 12, fontWeight: 600 }}>Salesforce</span>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <ConnectionBadge query={connectionQuery} />
        </div>
      </header>

      {/* Connection info bar */}
      {connectionQuery.data && (
        <div style={{ padding: "8px 24px", background: "#0d2136", borderBottom: "1px solid #1e293b", fontSize: 12, color: "#94a3b8", display: "flex", gap: 24 }}>
          <span>🔗 <b style={{ color: "#60a5fa" }}>{connectionQuery.data.username}</b></span>
          <span>API: <b style={{ color: "#a3e635" }}>{connectionQuery.data.api_version}</b></span>
          <span>Objects: <b style={{ color: "#f59e0b" }}>{connectionQuery.data.org_objects_count}</b></span>
          <span>Filtered: <b style={{ color: "#34d399" }}>{objectsQuery.data?.total ?? "—"}</b></span>
        </div>
      )}

      {/* Error state */}
      {connectionQuery.isError && <SetupGuide error={String(connectionQuery.error)} />}

      {/* Main layout */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left panel: object list */}
        <aside style={{ width: 320, borderRight: "1px solid #1e293b", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e293b" }}>
            <input
              placeholder="Search objects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid #334155", background: "#1e293b", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }}
            />
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <label style={{ fontSize: 12, color: "#94a3b8", display: "flex", alignItems: "center", gap: 4, cursor: "pointer" }}>
                <input type="checkbox" checked={queryableOnly} onChange={(e) => setQueryableOnly(e.target.checked)} />
                Queryable only
              </label>
              <label style={{ fontSize: 12, color: "#94a3b8", display: "flex", alignItems: "center", gap: 4, cursor: "pointer" }}>
                <input type="checkbox" checked={customOnly} onChange={(e) => setCustomOnly(e.target.checked)} />
                Custom only
              </label>
            </div>
          </div>
          <ObjectList
            objects={filteredObjects}
            loading={objectsQuery.isLoading}
            selected={selectedObject}
            onSelect={setSelectedObject}
          />
        </aside>

        {/* Right panel: metadata */}
        <main style={{ flex: 1, overflow: "auto", padding: 24 }}>
          {!selectedObject ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "#475569", gap: 8 }}>
              <span style={{ fontSize: 48 }}>🗂️</span>
              <span style={{ fontSize: 16 }}>Select an object to explore its metadata</span>
              <span style={{ fontSize: 13 }}>Fields, types, relationships, record types</span>
            </div>
          ) : (
            <MetadataPanel
              objectName={selectedObject}
              metadata={metadataQuery.data as SFObjectMetadata | undefined}
              loading={metadataQuery.isLoading}
              error={metadataQuery.isError ? String(metadataQuery.error) : null}
            />
          )}
        </main>
      </div>
    </div>
  );
}
