import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { hubspotApi } from "../api/hubspot";
import type { HSProperty, HSPropertiesResponse } from "../api/hubspot";

interface Props {
  objectType: string;
  properties: HSPropertiesResponse | undefined;
  loading: boolean;
  error: string | null;
}

const TYPE_COLORS: Record<string, string> = {
  string: "#60a5fa",
  enumeration: "#4ade80",
  bool: "#34d399",
  number: "#fbbf24",
  date: "#fb923c",
  datetime: "#fb923c",
  phone_number: "#94a3b8",
  object_coordinates: "#a78bfa",
};

function PropTypeBadge({ type }: { type: string }) {
  const color = TYPE_COLORS[type] ?? "#94a3b8";
  return (
    <span
      style={{
        fontSize: 11,
        padding: "1px 8px",
        borderRadius: 10,
        border: `1px solid ${color}`,
        color,
        fontFamily: "monospace",
      }}
    >
      {type}
    </span>
  );
}

function FieldTypeBadge({ fieldType }: { fieldType: string }) {
  return (
    <span
      style={{
        fontSize: 11,
        padding: "1px 8px",
        borderRadius: 10,
        background: "#1e293b",
        color: "#94a3b8",
        fontFamily: "monospace",
        border: "1px solid #334155",
      }}
    >
      {fieldType}
    </span>
  );
}

export default function HubspotPropertiesPanel({
  objectType,
  properties,
  loading,
  error,
}: Props) {
  const [tab, setTab] = useState<"properties" | "sample">("properties");
  const [search, setSearch] = useState("");
  const [groupFilter, setGroupFilter] = useState("");

  const sampleQuery = useQuery({
    queryKey: ["hs-sample", objectType],
    queryFn: () =>
      hubspotApi.getSampleData(objectType, 5).then((r) => r.data as Record<string, unknown>),
    enabled: tab === "sample",
  });

  if (loading) {
    return (
      <div style={{ color: "#94a3b8", padding: 16 }}>
        Loading properties for <b>{objectType}</b>...
      </div>
    );
  }
  if (error) {
    return <div style={{ color: "#f87171", padding: 16 }}>Error: {error}</div>;
  }
  if (!properties) return null;

  const groups = Array.from(new Set(properties.properties.map((p) => p.group_name))).sort();

  const filtered: HSProperty[] = properties.properties.filter((p) => {
    const matchSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.label.toLowerCase().includes(search.toLowerCase()) ||
      p.type.toLowerCase().includes(search.toLowerCase());
    const matchGroup = groupFilter === "" || p.group_name === groupFilter;
    return matchSearch && matchGroup;
  });

  return (
    <div>
      {/* Object header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <h2 style={{ margin: 0, fontSize: 22, color: "#f1f5f9" }}>
            {objectType.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </h2>
        </div>
        <div style={{ fontSize: 13, color: "#64748b" }}>
          API Name: <code style={{ color: "#94a3b8" }}>{objectType}</code>
          &nbsp;·&nbsp;
          <b style={{ color: "#f59e0b" }}>{properties.properties_count}</b> properties
          &nbsp;·&nbsp;
          <b style={{ color: "#a3e635" }}>{groups.length}</b> groups
        </div>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          gap: 0,
          marginBottom: 16,
          borderBottom: "1px solid #1e293b",
        }}
      >
        {(["properties", "sample"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: "8px 20px",
              background: "transparent",
              border: "none",
              borderBottom: tab === t ? "2px solid #f97316" : "2px solid transparent",
              color: tab === t ? "#f97316" : "#64748b",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: tab === t ? 600 : 400,
              textTransform: "capitalize",
            }}
          >
            {t === "properties"
              ? `Properties (${properties.properties_count})`
              : "Sample Data"}
          </button>
        ))}
      </div>

      {/* Properties tab */}
      {tab === "properties" && (
        <>
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            <input
              placeholder="Search properties..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: 260,
                padding: "7px 12px",
                borderRadius: 6,
                border: "1px solid #334155",
                background: "#1e293b",
                color: "#e2e8f0",
                fontSize: 13,
              }}
            />
            <select
              value={groupFilter}
              onChange={(e) => setGroupFilter(e.target.value)}
              style={{
                padding: "7px 12px",
                borderRadius: 6,
                border: "1px solid #334155",
                background: "#1e293b",
                color: "#94a3b8",
                fontSize: 13,
                minWidth: 180,
              }}
            >
              <option value="">All groups</option>
              {groups.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr
                  style={{
                    borderBottom: "1px solid #334155",
                    color: "#64748b",
                    textAlign: "left",
                  }}
                >
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Property Name</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Label</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Type</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Field Type</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Group</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>HS Defined</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Options</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((prop) => (
                  <tr
                    key={prop.name}
                    style={{ borderBottom: "1px solid #1e293b" }}
                    onMouseEnter={(e) =>
                      ((e.currentTarget as HTMLTableRowElement).style.background = "#1e293b")
                    }
                    onMouseLeave={(e) =>
                      ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")
                    }
                  >
                    <td
                      style={{
                        padding: "8px 12px",
                        fontFamily: "monospace",
                        color: "#94a3b8",
                      }}
                    >
                      {prop.name}
                    </td>
                    <td style={{ padding: "8px 12px", color: "#e2e8f0" }}>{prop.label}</td>
                    <td style={{ padding: "8px 12px" }}>
                      <PropTypeBadge type={prop.type} />
                    </td>
                    <td style={{ padding: "8px 12px" }}>
                      <FieldTypeBadge fieldType={prop.field_type} />
                    </td>
                    <td style={{ padding: "8px 12px", color: "#64748b", fontSize: 12 }}>
                      {prop.group_name}
                    </td>
                    <td
                      style={{
                        padding: "8px 12px",
                        color: prop.hubspot_defined ? "#4ade80" : "#a5b4fc",
                      }}
                    >
                      {prop.hubspot_defined ? "Yes" : "No"}
                    </td>
                    <td
                      style={{
                        padding: "8px 12px",
                        color: "#f59e0b",
                        fontSize: 12,
                        maxWidth: 200,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {prop.options.length > 0 ? prop.options.join(", ") : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Sample Data tab */}
      {tab === "sample" && (
        <div>
          {sampleQuery.isLoading && (
            <div style={{ color: "#94a3b8" }}>Fetching sample records...</div>
          )}
          {sampleQuery.isError && (
            <div style={{ color: "#f87171" }}>
              Could not fetch sample: {String(sampleQuery.error)}
            </div>
          )}
          {sampleQuery.data && (
            <>
              <div style={{ marginBottom: 8, fontSize: 12, color: "#64748b" }}>
                Total records in portal:{" "}
                <b style={{ color: "#f59e0b" }}>{sampleQuery.data.total ?? "—"}</b>
              </div>
              <div style={{ overflowX: "auto" }}>
                {(sampleQuery.data.records as unknown[]).length === 0 ? (
                  <div style={{ color: "#475569" }}>No records found.</div>
                ) : (
                  <table
                    style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}
                  >
                    <thead>
                      <tr
                        style={{
                          borderBottom: "1px solid #334155",
                          color: "#64748b",
                          textAlign: "left",
                        }}
                      >
                        {["id", "createdAt", "updatedAt", "archived"].map((col) => (
                          <th key={col} style={{ padding: "6px 10px", whiteSpace: "nowrap" }}>
                            {col}
                          </th>
                        ))}
                        {Object.keys(
                          (sampleQuery.data.records[0] as Record<string, unknown>).properties as Record<string, unknown> ?? {}
                        ).map((col) => (
                          <th key={col} style={{ padding: "6px 10px", whiteSpace: "nowrap" }}>
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(sampleQuery.data.records as Record<string, unknown>[]).map(
                        (row, i) => (
                          <tr key={i} style={{ borderBottom: "1px solid #1e293b" }}>
                            {["id", "createdAt", "updatedAt", "archived"].map((col) => (
                              <td
                                key={col}
                                style={{
                                  padding: "6px 10px",
                                  color: "#94a3b8",
                                  whiteSpace: "nowrap",
                                  fontFamily: "monospace",
                                }}
                              >
                                {row[col] === null || row[col] === undefined ? (
                                  <span style={{ color: "#475569" }}>null</span>
                                ) : (
                                  String(row[col])
                                )}
                              </td>
                            ))}
                            {Object.entries(
                              (row.properties as Record<string, unknown>) ?? {}
                            ).map(([k, v]) => (
                              <td
                                key={k}
                                style={{
                                  padding: "6px 10px",
                                  color: "#94a3b8",
                                  whiteSpace: "nowrap",
                                  fontFamily: "monospace",
                                }}
                              >
                                {v === null || v === undefined ? (
                                  <span style={{ color: "#475569" }}>null</span>
                                ) : (
                                  String(v)
                                )}
                              </td>
                            ))}
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
