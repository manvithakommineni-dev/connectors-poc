import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { servicenowApi, SNTableSummary } from "../api/servicenow";
import { ServiceNowMetadataPanel } from "../components/ServiceNowMetadataPanel";

const CAT_COLORS: Record<string, string> = {
  itsm: "#e74c3c",
  cmdb: "#8e44ad",
  users: "#2980b9",
  catalog: "#27ae60",
};
const CAT_ICONS: Record<string, string> = {
  itsm: "🎫",
  cmdb: "🖥️",
  users: "👤",
  catalog: "🛍️",
};

export default function ServiceNowExplorer() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [liveSearch, setLiveSearch] = useState("");
  const [showAll, setShowAll] = useState(false);

  const connectQuery = useQuery({
    queryKey: ["sn-connect"],
    queryFn: servicenowApi.connect,
    retry: 1,
  });

  const categoriesQuery = useQuery({
    queryKey: ["sn-categories"],
    queryFn: servicenowApi.listCategories,
    enabled: connectQuery.isSuccess,
  });

  const tablesQuery = useQuery({
    queryKey: ["sn-tables", selectedCategory, showAll, liveSearch],
    queryFn: () =>
      servicenowApi.listTables(
        showAll ? undefined : selectedCategory ?? undefined,
        liveSearch || undefined,
        200
      ),
    enabled: !!(selectedCategory || showAll),
  });

  const activeTables: SNTableSummary[] = tablesQuery.data?.tables ?? [];

  const filtered = activeTables.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.label.toLowerCase().includes(search.toLowerCase())
  );

  const isDemo = connectQuery.data?.mode === "demo";
  const isLive = connectQuery.data?.mode === "live";

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #293241 0%, #3d5a80 100%)",
          borderRadius: 12,
          padding: "24px 28px",
          color: "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <span style={{ fontSize: 32 }}>🟣</span>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>ServiceNow</div>
            <div style={{ fontSize: 13, opacity: 0.85 }}>
              ITSM · CMDB · Users & Access · Service Catalog
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
              }}
            >
              DEMO MODE
            </span>
          )}
          {isLive && (
            <span
              style={{
                marginLeft: "auto",
                background: "#27ae60",
                borderRadius: 6,
                padding: "4px 12px",
                fontSize: 12,
                fontWeight: 700,
              }}
            >
              LIVE ✓
            </span>
          )}
        </div>

        {connectQuery.isLoading && <div style={{ fontSize: 13, opacity: 0.8 }}>Connecting…</div>}
        {connectQuery.isError && (
          <div style={{ background: "rgba(255,255,255,0.2)", borderRadius: 6, padding: "8px 14px", fontSize: 13 }}>
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
              gap: 18,
            }}
          >
            <span>✅ Connected</span>
            {connectQuery.data.categories_count != null && (
              <span>Categories: <strong>{connectQuery.data.categories_count}</strong></span>
            )}
            {connectQuery.data.total_tables != null && (
              <span>Tables: <strong>{connectQuery.data.total_tables}</strong></span>
            )}
            {connectQuery.data.total_fields != null && (
              <span>Total Fields: <strong>{connectQuery.data.total_fields}</strong></span>
            )}
            {connectQuery.data.instance_url && (
              <span style={{ fontFamily: "monospace", fontSize: 12 }}>
                {connectQuery.data.instance_url}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Demo banner */}
      {isDemo && (
        <div
          style={{
            background: "#f3e5f5",
            border: "1px solid #ce93d8",
            borderRadius: 8,
            padding: "12px 16px",
            fontSize: 13,
            color: "#4a148c",
          }}
        >
          <strong>Demo Mode</strong> — Showing real ServiceNow table/field schema without credentials.
          To connect live: sign up free at{" "}
          <a href="https://developer.servicenow.com" target="_blank" rel="noreferrer" style={{ color: "#7b1fa2" }}>
            developer.servicenow.com
          </a>{" "}
          → get a Personal Developer Instance → add <code>SN_INSTANCE_URL</code>,{" "}
          <code>SN_USERNAME</code>, <code>SN_PASSWORD</code> to <code>backend/.env</code>.
        </div>
      )}

      {/* Live search bar (shown when in live mode) */}
      {isLive && (
        <div style={{ display: "flex", gap: 10 }}>
          <input
            type="text"
            placeholder="Search tables in your instance (e.g. incident, task, user)…"
            value={liveSearch}
            onChange={(e) => {
              setLiveSearch(e.target.value);
              setShowAll(true);
              setSelectedTable(null);
            }}
            style={{
              flex: 1,
              padding: "10px 14px",
              border: "1px solid #dee2e6",
              borderRadius: 8,
              fontSize: 14,
            }}
          />
        </div>
      )}

      <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
        {/* Left panel */}
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
              Categories ({categoriesQuery.data?.total ?? 0})
            </span>
            <button
              onClick={() => {
                setShowAll((v) => !v);
                setSelectedTable(null);
                setSearch("");
              }}
              style={{
                border: "1px solid #e9ecef",
                borderRadius: 4,
                padding: "3px 8px",
                fontSize: 11,
                background: showAll ? "#293241" : "#fff",
                color: showAll ? "#fff" : "#636e72",
                cursor: "pointer",
              }}
            >
              {showAll ? "By Category" : "All Tables"}
            </button>
          </div>

          {/* Category list */}
          {!showAll && (
            <div>
              {categoriesQuery.isLoading && (
                <div style={{ padding: 16, color: "#636e72", fontSize: 13 }}>Loading…</div>
              )}
              {categoriesQuery.data?.categories.map((cat) => {
                const color = CAT_COLORS[cat.id] ?? "#293241";
                return (
                  <div
                    key={cat.id}
                    onClick={() => {
                      setSelectedCategory(cat.id);
                      setSelectedTable(null);
                      setSearch("");
                    }}
                    style={{
                      padding: "10px 16px",
                      cursor: "pointer",
                      borderBottom: "1px solid #f1f3f5",
                      background: selectedCategory === cat.id ? "#f8f5ff" : "transparent",
                      borderLeft: `3px solid ${selectedCategory === cat.id ? color : "transparent"}`,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                      <span>{CAT_ICONS[cat.id] ?? "📁"}</span>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{cat.label}</span>
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
                        {cat.tables_count}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: "#888" }}>
                      {cat.description.split(",")[0]}…
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Table list */}
          {(selectedCategory || showAll) && (
            <div style={{ borderTop: "2px solid #e9ecef" }}>
              <div style={{ padding: "10px 12px", background: "#f8f9fa", borderBottom: "1px solid #e9ecef" }}>
                <input
                  type="text"
                  placeholder="Filter tables…"
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
              <div style={{ maxHeight: 320, overflowY: "auto" }}>
                {tablesQuery.isLoading && (
                  <div style={{ padding: 12, fontSize: 12, color: "#636e72" }}>Loading tables…</div>
                )}
                {filtered.map((tbl) => {
                  const color = CAT_COLORS[tbl.category] ?? "#293241";
                  return (
                    <div
                      key={tbl.name}
                      onClick={() => setSelectedTable(tbl.name)}
                      style={{
                        padding: "9px 14px",
                        cursor: "pointer",
                        borderBottom: "1px solid #f1f3f5",
                        background: selectedTable === tbl.name ? "#f8f5ff" : "transparent",
                        borderLeft: `3px solid ${selectedTable === tbl.name ? color : "transparent"}`,
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: 12 }}>{tbl.label}</div>
                      <div style={{ fontSize: 11, color: "#888", fontFamily: "monospace" }}>{tbl.name}</div>
                      <div style={{ display: "flex", gap: 8, marginTop: 3, fontSize: 10, color: "#aaa" }}>
                        {tbl.fields_count != null && <span>{tbl.fields_count} fields</span>}
                        {tbl.is_extendable && <span>extendable</span>}
                        {showAll && tbl.category && (
                          <span style={{ background: color, color: "#fff", borderRadius: 3, padding: "0 5px" }}>
                            {tbl.category}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
                {filtered.length === 0 && !tablesQuery.isLoading && (
                  <div style={{ padding: 16, color: "#aaa", fontSize: 12, textAlign: "center" }}>
                    No tables found
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selectedTable ? (
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
              <div style={{ fontSize: 48, marginBottom: 12 }}>🟣</div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
                {!selectedCategory && !showAll
                  ? "Select a category to browse ServiceNow tables"
                  : "Select a table to view its fields"}
              </div>
              <div style={{ fontSize: 13 }}>
                Field names, data types, reference links, and constraints will appear here
              </div>
            </div>
          ) : (
            <ServiceNowMetadataPanel tableName={selectedTable} />
          )}
        </div>
      </div>
    </div>
  );
}
