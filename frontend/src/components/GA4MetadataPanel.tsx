import type { GA4ItemDetail } from "../api/ga4";

interface Props {
  item: GA4ItemDetail;
}

function Field({ label, value }: { label: string; value: string | boolean | undefined }) {
  if (value === undefined || value === "") return null;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 11, color: "#888", fontWeight: 600, textTransform: "uppercase", marginBottom: 3 }}>
        {label}
      </div>
      <div style={{ fontSize: 13, color: "#1a1a1a", wordBreak: "break-word" }}>
        {typeof value === "boolean" ? (value ? "Yes" : "No") : value}
      </div>
    </div>
  );
}

export function GA4MetadataPanel({ item }: Props) {
  return (
    <div style={{ padding: "0 4px" }}>
      <div
        style={{
          background: "linear-gradient(135deg, #E37400 0%, #F9AB00 100%)",
          borderRadius: 10,
          padding: "18px 20px",
          marginBottom: 16,
          color: "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>📈</span>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{item.label || item.name}</div>
            <code style={{ fontSize: 12, opacity: 0.9 }}>{item.name}</code>
          </div>
        </div>
        {item.description && (
          <div style={{ marginTop: 8, fontSize: 13, opacity: 0.95 }}>{item.description}</div>
        )}
        <div style={{ marginTop: 10 }}>
          <span style={{ background: "rgba(255,255,255,0.2)", padding: "3px 10px", borderRadius: 12, fontSize: 12 }}>
            Live · {item.category}
          </span>
        </div>
      </div>

      <div
        style={{
          background: "#fff",
          border: "1px solid #e8eaed",
          borderRadius: 8,
          padding: "16px 18px",
        }}
      >
        <Field label="API Name" value={item.name} />
        <Field label="Display Name" value={item.label} />
        <Field label="Description" value={item.description} />
        <Field label="Category" value={item.category} />
        <Field label="Data Type" value={item.type} />
        <Field label="Scope" value={item.scope} />
        <Field label="Expression" value={item.expression} />
        <Field label="Measurement Unit" value={item.measurement_unit} />
        <Field label="Measurement ID" value={item.measurement_id} />
        <Field label="Default URI" value={item.default_uri} />
        <Field label="Stream Type" value={item.type} />
        <Field label="Resource Name" value={item.resource_name} />
        <Field label="Custom Definition" value={item.custom_definition} />
        <Field label="Deprecated" value={item.deprecated} />
      </div>
    </div>
  );
}
