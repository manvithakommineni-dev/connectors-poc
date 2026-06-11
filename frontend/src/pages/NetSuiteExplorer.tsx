import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { netsuiteApi, NSRecordSummary } from "../api/netsuite";
import { NetSuiteMetadataPanel } from "../components/NetSuiteMetadataPanel";

const MODULE_COLORS: Record<string, string> = {
  accounting: "#e67e22", customers: "#2980b9", vendors: "#8e44ad",
  inventory: "#27ae60", sales: "#c0392b", employees: "#16a085", projects: "#d35400",
};
const MODULE_ICONS: Record<string, string> = {
  accounting: "📊", customers: "👥", vendors: "🏪",
  inventory: "📦", sales: "💰", employees: "👤", projects: "📋",
};

export default function NetSuiteExplorer() {
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showAll, setShowAll] = useState(false);

  const connectQuery = useQuery({ queryKey: ["ns-connect"], queryFn: netsuiteApi.connect, retry: 1 });
  const modulesQuery = useQuery({ queryKey: ["ns-modules"], queryFn: netsuiteApi.listModules, enabled: connectQuery.isSuccess });
  const recordsQuery = useQuery({
    queryKey: ["ns-module-records", selectedModule],
    queryFn: () => netsuiteApi.getModuleRecords(selectedModule!),
    enabled: !!selectedModule && !showAll,
  });
  const allRecordsQuery = useQuery({ queryKey: ["ns-all-records"], queryFn: netsuiteApi.getAllRecords, enabled: showAll });

  const activeRecords: NSRecordSummary[] = showAll ? (allRecordsQuery.data?.records ?? []) : (recordsQuery.data?.records ?? []);
  const filtered = activeRecords.filter(r =>
    r.name.toLowerCase().includes(search.toLowerCase()) ||
    r.label.toLowerCase().includes(search.toLowerCase())
  );

  const isDemo = connectQuery.data?.mode === "demo";
  const isLive = connectQuery.data?.mode === "live";

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div style={{ background: "linear-gradient(135deg, #1a1a2e 0%, #e67e22 100%)", borderRadius: 12, padding: "24px 28px", color: "#fff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <span style={{ fontSize: 32 }}>🟠</span>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>NetSuite (Oracle)</div>
            <div style={{ fontSize: 13, opacity: 0.85 }}>Accounting · Customers · Vendors · Inventory · Sales · Employees · Projects</div>
          </div>
          {isDemo && <span style={{ marginLeft: "auto", background: "rgba(255,255,255,0.25)", borderRadius: 6, padding: "4px 12px", fontSize: 12, fontWeight: 700 }}>DEMO MODE</span>}
          {isLive && <span style={{ marginLeft: "auto", background: "#27ae60", borderRadius: 6, padding: "4px 12px", fontSize: 12, fontWeight: 700 }}>LIVE ✓</span>}
        </div>
        {connectQuery.isLoading && <div style={{ fontSize: 13, opacity: 0.8 }}>Connecting…</div>}
        {connectQuery.isError && <div style={{ background: "rgba(255,255,255,0.2)", borderRadius: 6, padding: "8px 14px", fontSize: 13 }}>❌ Connection failed</div>}
        {connectQuery.isSuccess && connectQuery.data && (
          <div style={{ background: "rgba(255,255,255,0.2)", borderRadius: 6, padding: "10px 14px", fontSize: 13, display: "flex", flexWrap: "wrap", gap: 18 }}>
            <span>✅ Connected</span>
            {connectQuery.data.modules_count != null && <span>Modules: <strong>{connectQuery.data.modules_count}</strong></span>}
            {connectQuery.data.total_record_types != null && <span>Record Types: <strong>{connectQuery.data.total_record_types}</strong></span>}
            {connectQuery.data.total_fields != null && <span>Total Fields: <strong>{connectQuery.data.total_fields}</strong></span>}
            {connectQuery.data.account_id && <span style={{ fontFamily: "monospace", fontSize: 12 }}>Account: {connectQuery.data.account_id}</span>}
          </div>
        )}
      </div>

      {isDemo && (
        <div style={{ background: "#fff3e0", border: "1px solid #ffcc02", borderRadius: 8, padding: "12px 16px", fontSize: 13, color: "#e65100" }}>
          <strong>Demo Mode</strong> — Shows real NetSuite REST Metadata Catalog schema without credentials.
          To connect live: get a free 30-day trial at{" "}
          <a href="https://www.netsuite.com" target="_blank" rel="noreferrer" style={{ color: "#bf360c" }}>netsuite.com</a>
          {" "}→ Setup &gt; Integration &gt; Manage Integrations → add <code>NS_ACCOUNT_ID</code>, <code>NS_CLIENT_ID</code>, <code>NS_CLIENT_SECRET</code> to <code>backend/.env</code>.
        </div>
      )}

      <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
        {/* Left panel */}
        <div style={{ width: 300, minWidth: 300, background: "#fff", borderRadius: 10, border: "1px solid #e9ecef", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", background: "#f8f9fa", borderBottom: "1px solid #e9ecef", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 600, fontSize: 13 }}>Modules ({modulesQuery.data?.total ?? 0})</span>
            <button onClick={() => { setShowAll(v => !v); setSelectedRecord(null); }}
              style={{ border: "1px solid #e9ecef", borderRadius: 4, padding: "3px 8px", fontSize: 11, background: showAll ? "#e67e22" : "#fff", color: showAll ? "#fff" : "#636e72", cursor: "pointer" }}>
              {showAll ? "By Module" : "All Records"}
            </button>
          </div>

          {!showAll && (
            <div>
              {modulesQuery.data?.modules.map(mod => {
                const color = MODULE_COLORS[mod.id] ?? "#e67e22";
                return (
                  <div key={mod.id} onClick={() => { setSelectedModule(mod.id); setSelectedRecord(null); setSearch(""); }}
                    style={{ padding: "10px 16px", cursor: "pointer", borderBottom: "1px solid #f1f3f5", background: selectedModule === mod.id ? "#fff8f0" : "transparent", borderLeft: `3px solid ${selectedModule === mod.id ? color : "transparent"}` }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                      <span>{MODULE_ICONS[mod.id] ?? "📁"}</span>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{mod.label}</span>
                      <span style={{ marginLeft: "auto", background: "#f1f3f5", borderRadius: 10, padding: "1px 7px", fontSize: 11, color: "#636e72" }}>{mod.records_count}</span>
                    </div>
                    <div style={{ fontSize: 11, color: "#888" }}>{mod.description.split(",")[0]}…</div>
                  </div>
                );
              })}
            </div>
          )}

          {(selectedModule || showAll) && (
            <div style={{ borderTop: "2px solid #e9ecef" }}>
              <div style={{ padding: "10px 12px", background: "#f8f9fa", borderBottom: "1px solid #e9ecef" }}>
                <input type="text" placeholder="Search record types…" value={search} onChange={e => setSearch(e.target.value)}
                  style={{ width: "100%", padding: "6px 10px", border: "1px solid #dee2e6", borderRadius: 6, fontSize: 12, boxSizing: "border-box" }} />
              </div>
              <div style={{ maxHeight: 300, overflowY: "auto" }}>
                {(recordsQuery.isLoading || allRecordsQuery.isLoading) && <div style={{ padding: 12, fontSize: 12, color: "#636e72" }}>Loading…</div>}
                {filtered.map(rec => {
                  const color = MODULE_COLORS[rec.module] ?? "#e67e22";
                  return (
                    <div key={rec.name} onClick={() => setSelectedRecord(rec.name)}
                      style={{ padding: "9px 14px", cursor: "pointer", borderBottom: "1px solid #f1f3f5", background: selectedRecord === rec.name ? "#fff8f0" : "transparent", borderLeft: `3px solid ${selectedRecord === rec.name ? color : "transparent"}` }}>
                      <div style={{ fontWeight: 600, fontSize: 12 }}>{rec.label}</div>
                      <div style={{ fontSize: 11, color: "#888", fontFamily: "monospace" }}>{rec.name}</div>
                      <div style={{ display: "flex", gap: 8, marginTop: 3, fontSize: 10, color: "#aaa" }}>
                        <span>{rec.fields_count} fields</span>
                        {showAll && <span style={{ background: color, color: "#fff", borderRadius: 3, padding: "0 5px" }}>{rec.module}</span>}
                      </div>
                    </div>
                  );
                })}
                {filtered.length === 0 && !recordsQuery.isLoading && !allRecordsQuery.isLoading && (
                  <div style={{ padding: 16, color: "#aaa", fontSize: 12, textAlign: "center" }}>No records found</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selectedRecord ? (
            <div style={{ background: "#fff", borderRadius: 10, border: "1px solid #e9ecef", padding: 40, textAlign: "center", color: "#aaa" }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>🟠</div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
                {!selectedModule && !showAll ? "Select a module to browse NetSuite record types" : "Select a record type to view its fields"}
              </div>
              <div style={{ fontSize: 13 }}>Field names, types, references, and constraints appear here</div>
            </div>
          ) : (
            <NetSuiteMetadataPanel recordType={selectedRecord} />
          )}
        </div>
      </div>
    </div>
  );
}
