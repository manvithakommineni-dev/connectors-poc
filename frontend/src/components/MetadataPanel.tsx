import { useState } from "react";
import { SFObjectMetadata, SFField } from "../api/salesforce";
import { useQuery } from "@tanstack/react-query";
import { salesforceApi } from "../api/salesforce";

interface Props {
  objectName: string;
  metadata: SFObjectMetadata | undefined;
  loading: boolean;
  error: string | null;
}

const TYPE_COLORS: Record<string, string> = {
  string: "#60a5fa",
  textarea: "#60a5fa",
  id: "#a78bfa",
  reference: "#f472b6",
  boolean: "#34d399",
  double: "#fbbf24",
  int: "#fbbf24",
  currency: "#fbbf24",
  percent: "#fbbf24",
  date: "#fb923c",
  datetime: "#fb923c",
  picklist: "#4ade80",
  multipicklist: "#4ade80",
  phone: "#94a3b8",
  email: "#94a3b8",
  url: "#94a3b8",
};

function FieldTypeBadge({ type }: { type: string }) {
  const color = TYPE_COLORS[type] ?? "#94a3b8";
  return (
    <span style={{ fontSize: 11, padding: "1px 8px", borderRadius: 10, border: `1px solid ${color}`, color, fontFamily: "monospace" }}>
      {type}
    </span>
  );
}

export default function MetadataPanel({ objectName, metadata, loading, error }: Props) {
  const [tab, setTab] = useState<"fields" | "relationships" | "sample">("fields");
  const [fieldSearch, setFieldSearch] = useState("");

  const sampleQuery = useQuery({
    queryKey: ["sf-sample", objectName],
    queryFn: () => salesforceApi.getSampleData(objectName, 5).then((r) => r.data),
    enabled: tab === "sample",
  });

  if (loading) {
    return <div style={{ color: "#94a3b8", padding: 16 }}>Loading metadata for <b>{objectName}</b>...</div>;
  }
  if (error) {
    return <div style={{ color: "#f87171", padding: 16 }}>Error: {error}</div>;
  }
  if (!metadata) return null;

  const filteredFields: SFField[] = metadata.fields.filter(
    (f) =>
      f.name.toLowerCase().includes(fieldSearch.toLowerCase()) ||
      f.label.toLowerCase().includes(fieldSearch.toLowerCase()) ||
      f.type.toLowerCase().includes(fieldSearch.toLowerCase())
  );

  return (
    <div>
      {/* Object header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <h2 style={{ margin: 0, fontSize: 22, color: "#f1f5f9" }}>{metadata.label}</h2>
          {metadata.custom && (
            <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 10, background: "#312e81", color: "#a5b4fc" }}>Custom Object</span>
          )}
        </div>
        <div style={{ fontSize: 13, color: "#64748b" }}>
          API Name: <code style={{ color: "#94a3b8" }}>{metadata.name}</code>
          &nbsp;·&nbsp;{metadata.fields_count} fields
          &nbsp;·&nbsp;{metadata.child_relationships.length} child relationships
          &nbsp;·&nbsp;{metadata.record_types.length} record types
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, marginBottom: 16, borderBottom: "1px solid #1e293b" }}>
        {(["fields", "relationships", "sample"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: "8px 20px",
              background: "transparent",
              border: "none",
              borderBottom: tab === t ? "2px solid #38bdf8" : "2px solid transparent",
              color: tab === t ? "#38bdf8" : "#64748b",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: tab === t ? 600 : 400,
              textTransform: "capitalize",
            }}
          >
            {t === "fields" ? `Fields (${metadata.fields_count})` : t === "relationships" ? `Relationships (${metadata.child_relationships.length})` : "Sample Data"}
          </button>
        ))}
      </div>

      {/* Fields tab */}
      {tab === "fields" && (
        <>
          <input
            placeholder="Search fields..."
            value={fieldSearch}
            onChange={(e) => setFieldSearch(e.target.value)}
            style={{ width: 300, padding: "7px 12px", borderRadius: 6, border: "1px solid #334155", background: "#1e293b", color: "#e2e8f0", fontSize: 13, marginBottom: 12 }}
          />
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #334155", color: "#64748b", textAlign: "left" }}>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Field Name</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Label</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Type</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Length</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Nillable</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Custom</th>
                  <th style={{ padding: "8px 12px", fontWeight: 600 }}>Reference To</th>
                </tr>
              </thead>
              <tbody>
                {filteredFields.map((field) => (
                  <tr
                    key={field.name}
                    style={{ borderBottom: "1px solid #1e293b" }}
                    onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "#1e293b")}
                    onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")}
                  >
                    <td style={{ padding: "8px 12px", fontFamily: "monospace", color: "#94a3b8" }}>{field.name}</td>
                    <td style={{ padding: "8px 12px", color: "#e2e8f0" }}>{field.label}</td>
                    <td style={{ padding: "8px 12px" }}><FieldTypeBadge type={field.type} /></td>
                    <td style={{ padding: "8px 12px", color: "#64748b" }}>{field.length ?? "—"}</td>
                    <td style={{ padding: "8px 12px", color: field.nillable ? "#4ade80" : "#f87171" }}>
                      {field.nillable ? "Yes" : "No"}
                    </td>
                    <td style={{ padding: "8px 12px", color: field.custom ? "#a5b4fc" : "#475569" }}>
                      {field.custom ? "Yes" : "No"}
                    </td>
                    <td style={{ padding: "8px 12px", color: "#f472b6", fontFamily: "monospace", fontSize: 12 }}>
                      {field.reference_to.length > 0 ? field.reference_to.join(", ") : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Relationships tab */}
      {tab === "relationships" && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #334155", color: "#64748b", textAlign: "left" }}>
              <th style={{ padding: "8px 12px" }}>Child Object</th>
              <th style={{ padding: "8px 12px" }}>Field</th>
              <th style={{ padding: "8px 12px" }}>Relationship Name</th>
              <th style={{ padding: "8px 12px" }}>Cascade Delete</th>
            </tr>
          </thead>
          <tbody>
            {metadata.child_relationships.map((rel, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #1e293b" }}>
                <td style={{ padding: "8px 12px", color: "#f472b6", fontFamily: "monospace" }}>{rel.child_sobject}</td>
                <td style={{ padding: "8px 12px", color: "#94a3b8", fontFamily: "monospace" }}>{rel.field}</td>
                <td style={{ padding: "8px 12px", color: "#60a5fa" }}>{rel.relationship_name ?? "—"}</td>
                <td style={{ padding: "8px 12px", color: rel.cascade_delete ? "#f87171" : "#4ade80" }}>
                  {rel.cascade_delete ? "Yes" : "No"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Sample Data tab */}
      {tab === "sample" && (
        <div>
          {sampleQuery.isLoading && <div style={{ color: "#94a3b8" }}>Fetching sample rows...</div>}
          {sampleQuery.isError && <div style={{ color: "#f87171" }}>Could not fetch sample: {String(sampleQuery.error)}</div>}
          {sampleQuery.data && (
            <>
              <div style={{ marginBottom: 8, fontSize: 12, color: "#64748b" }}>
                SOQL: <code style={{ color: "#a3e635" }}>{sampleQuery.data.soql}</code>
                &nbsp;·&nbsp; Total rows in org: <b style={{ color: "#f59e0b" }}>{sampleQuery.data.total_size}</b>
              </div>
              <div style={{ overflowX: "auto" }}>
                {sampleQuery.data.records.length === 0 ? (
                  <div style={{ color: "#475569" }}>No records found.</div>
                ) : (
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid #334155", color: "#64748b", textAlign: "left" }}>
                        {Object.keys(sampleQuery.data.records[0])
                          .filter((k) => k !== "attributes")
                          .map((col) => (
                            <th key={col} style={{ padding: "6px 10px", whiteSpace: "nowrap" }}>{col}</th>
                          ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sampleQuery.data.records.map((row: any, i: number) => (
                        <tr key={i} style={{ borderBottom: "1px solid #1e293b" }}>
                          {Object.entries(row)
                            .filter(([k]) => k !== "attributes")
                            .map(([k, v]) => (
                              <td key={k} style={{ padding: "6px 10px", color: "#94a3b8", whiteSpace: "nowrap", fontFamily: "monospace" }}>
                                {v === null ? <span style={{ color: "#475569" }}>null</span> : String(v)}
                              </td>
                            ))}
                        </tr>
                      ))}
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
