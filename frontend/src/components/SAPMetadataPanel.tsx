import type { SAPEntityFields, SAPField } from "../api/sap";

interface Props {
  entityName: string;
  data: SAPEntityFields | undefined;
  loading: boolean;
  error: string | null;
}

const TYPE_COLORS: Record<string, string> = {
  String: "#60a5fa",
  Decimal: "#34d399",
  Int16: "#34d399",
  Int32: "#34d399",
  Int64: "#34d399",
  Boolean: "#f59e0b",
  DateTime: "#a78bfa",
  DateTimeOffset: "#a78bfa",
  Date: "#a78bfa",
  Time: "#a78bfa",
  Guid: "#94a3b8",
  Binary: "#f87171",
  Byte: "#f87171",
};

function typeColor(simpleType: string): string {
  return TYPE_COLORS[simpleType] ?? "#94a3b8";
}

function FieldRow({ field }: { field: SAPField }) {
  return (
    <tr
      style={{
        borderBottom: "1px solid #1e293b",
        background: field.is_key ? "rgba(251,191,36,0.05)" : "transparent",
      }}
    >
      <td style={{ padding: "8px 12px", verticalAlign: "top" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {field.is_key && (
            <span title="Key field" style={{ fontSize: 11, color: "#fbbf24" }}>
              🔑
            </span>
          )}
          <span style={{ fontFamily: "monospace", fontSize: 13, color: "#e2e8f0" }}>
            {field.name}
          </span>
        </div>
        {field.label && field.label !== field.name && (
          <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
            {field.label}
          </div>
        )}
      </td>
      <td style={{ padding: "8px 12px", verticalAlign: "top" }}>
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: typeColor(field.simple_type),
            background: "rgba(0,0,0,0.3)",
            padding: "2px 7px",
            borderRadius: 4,
            fontFamily: "monospace",
          }}
        >
          {field.simple_type}
        </span>
      </td>
      <td style={{ padding: "8px 12px", verticalAlign: "top", fontSize: 12, color: "#64748b" }}>
        {field.max_length ? `len:${field.max_length}` : ""}
        {field.precision ? ` p:${field.precision}` : ""}
        {field.scale ? ` s:${field.scale}` : ""}
      </td>
      <td style={{ padding: "8px 12px", verticalAlign: "top" }}>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {field.nullable === false && (
            <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 3, background: "#450a0a", color: "#fca5a5" }}>
              required
            </span>
          )}
          {field.filterable === "true" && (
            <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 3, background: "#0f2d1a", color: "#86efac" }}>
              filterable
            </span>
          )}
          {field.sortable === "true" && (
            <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 3, background: "#0f1e2d", color: "#93c5fd" }}>
              sortable
            </span>
          )}
        </div>
      </td>
    </tr>
  );
}

export default function SAPMetadataPanel({ entityName, data, loading, error }: Props) {
  if (loading) {
    return (
      <div style={{ padding: 24, color: "#94a3b8", fontSize: 14 }}>
        ⏳ Loading fields for <b style={{ color: "#e2e8f0" }}>{entityName}</b>...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24, background: "#1c0505", border: "1px solid #450a0a", borderRadius: 8, color: "#fca5a5" }}>
        <b>Error loading entity fields</b>
        <br />
        <code style={{ fontSize: 12 }}>{error}</code>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div style={{ fontFamily: "Inter, system-ui, sans-serif" }}>
      {/* Entity header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <h2 style={{ margin: 0, fontSize: 18, color: "#e2e8f0", fontFamily: "monospace" }}>
            {data.entity_type}
          </h2>
          {data.entity_set && data.entity_set !== data.entity_type && (
            <span style={{ fontSize: 12, color: "#64748b" }}>
              EntitySet: <code style={{ color: "#94a3b8" }}>{data.entity_set}</code>
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 12, color: "#64748b" }}>
          <span>
            Fields:{" "}
            <b style={{ color: "#f59e0b" }}>{data.fields_count}</b>
          </span>
          <span>
            Keys:{" "}
            <b style={{ color: "#fbbf24" }}>{data.key_fields.join(", ") || "—"}</b>
          </span>
          <span>
            Relationships:{" "}
            <b style={{ color: "#a5b4fc" }}>{data.navigation_properties.length}</b>
          </span>
          <span>
            Service:{" "}
            <b style={{ color: "#34d399" }}>{data.service_name}</b>
          </span>
        </div>
      </div>

      {/* Fields table */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>
          Properties / Fields ({data.fields_count})
        </div>
        <div style={{ border: "1px solid #1e293b", borderRadius: 8, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: "#0f172a", borderBottom: "1px solid #334155" }}>
                <th style={{ padding: "8px 12px", textAlign: "left", color: "#475569", fontWeight: 600, fontSize: 11 }}>
                  Name / Label
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", color: "#475569", fontWeight: 600, fontSize: 11 }}>
                  Type
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", color: "#475569", fontWeight: 600, fontSize: 11 }}>
                  Length
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", color: "#475569", fontWeight: 600, fontSize: 11 }}>
                  Flags
                </th>
              </tr>
            </thead>
            <tbody>
              {data.fields.map((field) => (
                <FieldRow key={field.name} field={field} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Navigation Properties (Relationships) */}
      {data.navigation_properties.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>
            Navigation Properties / Relationships ({data.navigation_properties.length})
          </div>
          <div style={{ border: "1px solid #1e293b", borderRadius: 8, overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "#0f172a", borderBottom: "1px solid #334155" }}>
                  <th style={{ padding: "8px 12px", textAlign: "left", color: "#475569", fontWeight: 600, fontSize: 11 }}>
                    Name
                  </th>
                  <th style={{ padding: "8px 12px", textAlign: "left", color: "#475569", fontWeight: 600, fontSize: 11 }}>
                    Relationship
                  </th>
                  <th style={{ padding: "8px 12px", textAlign: "left", color: "#475569", fontWeight: 600, fontSize: 11 }}>
                    From → To
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.navigation_properties.map((nav) => (
                  <tr key={nav.name} style={{ borderBottom: "1px solid #1e293b" }}>
                    <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 13, color: "#a5b4fc" }}>
                      {nav.name}
                    </td>
                    <td style={{ padding: "8px 12px", fontSize: 12, color: "#64748b" }}>
                      {nav.relationship.split(".").pop()}
                    </td>
                    <td style={{ padding: "8px 12px", fontSize: 12, color: "#64748b" }}>
                      {nav.from_role} → {nav.to_role}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
