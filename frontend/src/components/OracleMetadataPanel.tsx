import { useQuery } from "@tanstack/react-query";
import { oracleApi, OracleAttribute, OracleChildResource } from "../api/oracle";

interface Props {
  resourceName: string;
}

const TYPE_COLORS: Record<string, string> = {
  integer: "#6c5ce7",
  number: "#0984e3",
  string: "#00b894",
  boolean: "#e17055",
  "date-time": "#fdcb6e",
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

function FlagBadge({ label, active }: { label: string; active: boolean }) {
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

function AttributeRow({ attr }: { attr: OracleAttribute }) {
  return (
    <tr
      style={{
        borderBottom: "1px solid #f1f3f5",
        background: attr.is_key ? "#fff9e6" : "transparent",
      }}
    >
      <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 13 }}>
        {attr.is_key && (
          <span style={{ marginRight: 4, color: "#f9a825" }} title="Primary Key">
            🔑
          </span>
        )}
        {attr.name}
      </td>
      <td style={{ padding: "8px 12px", color: "#636e72", fontSize: 13 }}>
        {attr.title !== attr.name ? attr.title : ""}
      </td>
      <td style={{ padding: "8px 12px" }}>
        <TypeBadge type={attr.type} />
      </td>
      <td style={{ padding: "8px 12px" }}>
        {attr.max_length != null && (
          <span style={{ fontSize: 12, color: "#636e72" }}>{attr.max_length}</span>
        )}
      </td>
      <td style={{ padding: "8px 6px", display: "flex", gap: 4, flexWrap: "wrap" }}>
        {attr.required && <FlagBadge label="required" active />}
        {attr.queryable && <FlagBadge label="queryable" active />}
        {attr.updatable && <FlagBadge label="updatable" active />}
      </td>
    </tr>
  );
}

function ChildRow({ child }: { child: OracleChildResource }) {
  return (
    <tr style={{ borderBottom: "1px solid #f1f3f5" }}>
      <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 13, color: "#0984e3" }}>
        {child.name}
      </td>
      <td style={{ padding: "8px 12px", fontSize: 13 }}>{child.title}</td>
      <td style={{ padding: "8px 12px", fontSize: 12, color: "#636e72" }}>{child.description}</td>
    </tr>
  );
}

export function OracleMetadataPanel({ resourceName }: Props) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["oracle-describe", resourceName],
    queryFn: () => oracleApi.describeResource(resourceName),
    enabled: !!resourceName,
  });

  if (isLoading) {
    return (
      <div style={{ padding: 32, textAlign: "center", color: "#636e72" }}>
        Loading metadata for <strong>{resourceName}</strong>…
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
        {(error as { message?: string })?.message ?? "Failed to load resource metadata"}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div style={{ fontFamily: "system-ui, sans-serif" }}>
      {/* Resource header */}
      <div
        style={{
          background: "linear-gradient(135deg, #c0392b 0%, #e74c3c 100%)",
          borderRadius: 10,
          padding: "20px 24px",
          color: "#fff",
          marginBottom: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <span style={{ fontSize: 22 }}>⚙️</span>
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
        <div style={{ fontSize: 13, opacity: 0.9 }}>{data.description}</div>
        <div
          style={{
            marginTop: 12,
            display: "flex",
            gap: 20,
            fontSize: 13,
            opacity: 0.85,
          }}
        >
          <span>
            <strong>{data.attributes_count}</strong> attributes
          </span>
          <span>
            <strong>{data.children_count}</strong> child resources
          </span>
          <span style={{ fontFamily: "monospace" }}>
            Module: <strong>{data.module}</strong>
          </span>
          <span style={{ fontFamily: "monospace" }}>
            Resource: <strong>{data.name}</strong>
          </span>
        </div>
      </div>

      {/* Attributes table */}
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
          Attributes ({data.attributes_count})
          <span
            style={{ fontWeight: 400, fontSize: 12, color: "#636e72", marginLeft: 8 }}
          >
            Fields / Columns of this resource
          </span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8f9fa", borderBottom: "2px solid #e9ecef" }}>
                <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600 }}>
                  Attribute Name
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600 }}>
                  Display Title
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600 }}>
                  Type
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600 }}>
                  Max Length
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600 }}>
                  Flags
                </th>
              </tr>
            </thead>
            <tbody>
              {data.attributes.map((attr) => (
                <AttributeRow key={attr.name} attr={attr} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Child resources */}
      {data.children.length > 0 && (
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
            Child Resources ({data.children_count})
            <span
              style={{ fontWeight: 400, fontSize: 12, color: "#636e72", marginLeft: 8 }}
            >
              Related sub-tables / nested collections
            </span>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8f9fa", borderBottom: "2px solid #e9ecef" }}>
                <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600 }}>
                  Resource Name
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600 }}>
                  Title
                </th>
                <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 12, color: "#636e72", fontWeight: 600 }}>
                  Description
                </th>
              </tr>
            </thead>
            <tbody>
              {data.children.map((child) => (
                <ChildRow key={child.name} child={child} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
