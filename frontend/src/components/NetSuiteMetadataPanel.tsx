import { useQuery } from "@tanstack/react-query";
import { netsuiteApi, NSField } from "../api/netsuite";

interface Props { recordType: string; }

const TYPE_COLORS: Record<string, string> = {
  string: "#00b894", integer: "#6c5ce7", float: "#0984e3",
  boolean: "#e17055", date: "#fdcb6e", dateTime: "#f0932b",
  select: "#a29bfe", enum: "#fd79a8",
};

function TypeBadge({ type }: { type: string }) {
  const color = TYPE_COLORS[type] ?? "#636e72";
  return (
    <span style={{ backgroundColor: color, color: "#fff", borderRadius: 4, padding: "1px 7px", fontSize: 11, fontWeight: 600, fontFamily: "monospace", whiteSpace: "nowrap" }}>
      {type}
    </span>
  );
}

function FieldRow({ field }: { field: NSField }) {
  return (
    <tr style={{ borderBottom: "1px solid #f1f3f5", background: field.is_key ? "#fff9e6" : "transparent" }}>
      <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 13 }}>
        {field.is_key && <span style={{ marginRight: 4, color: "#f9a825" }}>🔑</span>}
        {field.name}
      </td>
      <td style={{ padding: "8px 12px", fontSize: 13, color: "#444" }}>{field.label}</td>
      <td style={{ padding: "8px 12px" }}><TypeBadge type={field.type} /></td>
      <td style={{ padding: "8px 12px" }}>
        {field.referenceType && (
          <span style={{ background: "#e8f4fd", color: "#1565c0", borderRadius: 4, padding: "1px 7px", fontSize: 11, fontFamily: "monospace" }}>
            → {field.referenceType}
          </span>
        )}
      </td>
      <td style={{ padding: "8px 6px" }}>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {!field.nullable && <span style={{ border: "1px solid #e74c3c", color: "#e74c3c", borderRadius: 4, padding: "1px 6px", fontSize: 10 }}>required</span>}
          {field.readOnly && <span style={{ border: "1px solid #b2bec3", color: "#636e72", borderRadius: 4, padding: "1px 6px", fontSize: 10 }}>readOnly</span>}
        </div>
      </td>
      <td style={{ padding: "8px 12px", fontSize: 12, color: "#636e72", maxWidth: 220 }}>{field.description}</td>
    </tr>
  );
}

export function NetSuiteMetadataPanel({ recordType }: Props) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["ns-fields", recordType],
    queryFn: () => netsuiteApi.getRecordFields(recordType),
    enabled: !!recordType,
  });

  if (isLoading) return <div style={{ padding: 32, textAlign: "center", color: "#636e72" }}>Loading fields for <strong>{recordType}</strong>…</div>;
  if (isError) return (
    <div style={{ padding: 20, background: "#fff5f5", borderRadius: 8, color: "#c0392b", border: "1px solid #fab1a0" }}>
      <strong>Error:</strong> {(error as { message?: string })?.message ?? "Failed to load"}
    </div>
  );
  if (!data) return null;

  return (
    <div style={{ fontFamily: "system-ui, sans-serif" }}>
      <div style={{ background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)", borderRadius: 10, padding: "20px 24px", color: "#fff", marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <span style={{ fontSize: 22 }}>🟠</span>
          <span style={{ fontSize: 20, fontWeight: 700 }}>{data.label}</span>
          <span style={{ background: data.mode === "live" ? "#27ae60" : "rgba(255,255,255,0.2)", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600 }}>
            {data.mode === "live" ? "LIVE" : "DEMO"}
          </span>
        </div>
        {data.description && <div style={{ fontSize: 13, opacity: 0.9, marginBottom: 10 }}>{data.description}</div>}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 20, fontSize: 13, opacity: 0.85 }}>
          <span><strong>{data.fields_count}</strong> fields</span>
          <span style={{ fontFamily: "monospace" }}>Record Type: <strong>{data.name}</strong></span>
          {data.module && <span>Module: <strong>{data.module}</strong></span>}
        </div>
      </div>

      <div style={{ background: "#fff", borderRadius: 8, border: "1px solid #e9ecef", overflow: "hidden" }}>
        <div style={{ padding: "12px 16px", background: "#f8f9fa", borderBottom: "1px solid #e9ecef", fontWeight: 600, fontSize: 14 }}>
          Fields ({data.fields_count})
          <span style={{ fontWeight: 400, fontSize: 12, color: "#636e72", marginLeft: 8 }}>
            NetSuite Metadata Catalog properties
          </span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8f9fa", borderBottom: "2px solid #e9ecef" }}>
                {["Field Name", "Label", "Type", "Reference", "Flags", "Description"].map(h => (
                  <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600, whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>{data.fields.map(f => <FieldRow key={f.name} field={f} />)}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
