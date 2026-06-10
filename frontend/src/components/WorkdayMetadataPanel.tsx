import { useQuery } from "@tanstack/react-query";
import { workdayApi, WorkdayField, WorkdayRelated } from "../api/workday";

interface Props {
  objectName: string;
}

const TYPE_COLORS: Record<string, string> = {
  string: "#00b894",
  integer: "#6c5ce7",
  number: "#0984e3",
  boolean: "#e17055",
  date: "#fdcb6e",
  object: "#a29bfe",
  array: "#fd79a8",
};

function TypeBadge({ type }: { type: string }) {
  const color = TYPE_COLORS[type] ?? "#636e72";
  return (
    <span
      style={{
        backgroundColor: color,
        color: "#fff",
        borderRadius: 4,
        padding: "1px 7px",
        fontSize: 11,
        fontWeight: 600,
        fontFamily: "monospace",
        whiteSpace: "nowrap",
      }}
    >
      {type}
    </span>
  );
}

function Flag({ label, active }: { label: string; active: boolean }) {
  if (!active) return null;
  return (
    <span
      style={{
        border: "1px solid #b2bec3",
        borderRadius: 4,
        padding: "1px 6px",
        fontSize: 10,
        color: "#636e72",
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </span>
  );
}

function FieldRow({ field }: { field: WorkdayField }) {
  return (
    <tr
      style={{
        borderBottom: "1px solid #f1f3f5",
        background: field.is_key ? "#fff9e6" : "transparent",
      }}
    >
      <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 13 }}>
        {field.is_key && (
          <span style={{ marginRight: 4, color: "#f9a825" }} title="Primary Key">
            🔑
          </span>
        )}
        {field.name}
      </td>
      <td style={{ padding: "8px 12px", fontSize: 13, color: "#636e72" }}>
        {field.title !== field.name ? field.title : ""}
      </td>
      <td style={{ padding: "8px 12px" }}>
        <TypeBadge type={field.type} />
      </td>
      <td style={{ padding: "8px 12px", fontSize: 12, color: "#555", maxWidth: 220 }}>
        {field.description}
      </td>
      <td style={{ padding: "8px 6px" }}>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          <Flag label="required" active={field.required} />
          <Flag label="filterable" active={field.filterable} />
        </div>
      </td>
    </tr>
  );
}

function RelatedRow({ rel }: { rel: WorkdayRelated }) {
  return (
    <tr style={{ borderBottom: "1px solid #f1f3f5" }}>
      <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 12, color: "#0984e3" }}>
        {rel.name}
      </td>
      <td style={{ padding: "8px 12px", fontSize: 13 }}>{rel.title}</td>
      <td style={{ padding: "8px 12px", fontSize: 12, color: "#636e72" }}>{rel.description}</td>
    </tr>
  );
}

export function WorkdayMetadataPanel({ objectName }: Props) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["workday-describe", objectName],
    queryFn: () => workdayApi.describeObject(objectName),
    enabled: !!objectName,
  });

  if (isLoading) {
    return (
      <div style={{ padding: 32, textAlign: "center", color: "#636e72" }}>
        Loading metadata for <strong>{objectName}</strong>…
      </div>
    );
  }

  if (isError) {
    return (
      <div
        style={{
          padding: 20,
          background: "#fff5f5",
          borderRadius: 8,
          color: "#c0392b",
          border: "1px solid #fab1a0",
        }}
      >
        <strong>Error:</strong>{" "}
        {(error as { message?: string })?.message ?? "Failed to load object metadata"}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div style={{ fontFamily: "system-ui, sans-serif" }}>
      {/* Object header */}
      <div
        style={{
          background: "linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%)",
          borderRadius: 10,
          padding: "20px 24px",
          color: "#fff",
          marginBottom: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <span style={{ fontSize: 22 }}>🔵</span>
          <span style={{ fontSize: 20, fontWeight: 700 }}>{data.title}</span>
          {data.mode === "demo" && (
            <span
              style={{
                background: "rgba(255,255,255,0.2)",
                borderRadius: 4,
                padding: "2px 8px",
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              DEMO
            </span>
          )}
        </div>
        <div style={{ fontSize: 13, opacity: 0.9, marginBottom: 10 }}>{data.description}</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 20, fontSize: 13, opacity: 0.85 }}>
          <span>
            <strong>{data.fields_count}</strong> fields
          </span>
          <span>
            <strong>{data.related_count}</strong> related resources
          </span>
          <span style={{ fontFamily: "monospace" }}>
            Module: <strong>{data.module}</strong>
          </span>
          <span style={{ fontFamily: "monospace" }}>
            REST: <strong>{data.rest_path}</strong>
          </span>
        </div>
      </div>

      {/* Fields table */}
      <div
        style={{
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e9ecef",
          overflow: "hidden",
          marginBottom: 20,
        }}
      >
        <div
          style={{
            padding: "12px 16px",
            background: "#f8f9fa",
            borderBottom: "1px solid #e9ecef",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          Fields ({data.fields_count})
          <span style={{ fontWeight: 400, fontSize: 12, color: "#636e72", marginLeft: 8 }}>
            Columns / attributes of this business object
          </span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8f9fa", borderBottom: "2px solid #e9ecef" }}>
                {["Field Name", "Display Title", "Type", "Description", "Flags"].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "8px 12px",
                      textAlign: "left",
                      fontSize: 12,
                      color: "#636e72",
                      fontWeight: 600,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.fields.map((f) => (
                <FieldRow key={f.name} field={f} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Related resources */}
      {data.related.length > 0 && (
        <div
          style={{
            background: "#fff",
            borderRadius: 8,
            border: "1px solid #e9ecef",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "12px 16px",
              background: "#f8f9fa",
              borderBottom: "1px solid #e9ecef",
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            Related Resources ({data.related_count})
            <span style={{ fontWeight: 400, fontSize: 12, color: "#636e72", marginLeft: 8 }}>
              Sub-collections accessible via REST path
            </span>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8f9fa", borderBottom: "2px solid #e9ecef" }}>
                {["REST Path", "Title", "Description"].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "8px 12px",
                      textAlign: "left",
                      fontSize: 12,
                      color: "#636e72",
                      fontWeight: 600,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.related.map((r) => (
                <RelatedRow key={r.name} rel={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
