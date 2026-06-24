import type { InstagramItemDetail } from "../api/instagram";

interface Props {
  item: InstagramItemDetail;
}

export function InstagramMetadataPanel({ item }: Props) {
  const isFieldCatalog = !!item.data_type || !!item.type;
  const rawFields = item.fields || item.raw;

  return (
    <div style={{ padding: "0 4px" }}>
      <div
        style={{
          background: "linear-gradient(135deg, #E1306C 0%, #C13584 50%, #833AB4 100%)",
          borderRadius: 10,
          padding: "18px 20px",
          marginBottom: 16,
          color: "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>📸</span>
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
            {item.mode === "demo" ? "Demo" : "Live"} · {item.category}
          </span>
          {(item.data_type || item.type) && (
            <span
              style={{
                marginLeft: 8,
                background: "rgba(255,255,255,0.2)",
                padding: "3px 10px",
                borderRadius: 12,
                fontSize: 12,
              }}
            >
              {item.data_type || item.type}
            </span>
          )}
        </div>
      </div>

      {rawFields && (
        <div
          style={{
            background: "#1e1e2e",
            borderRadius: 8,
            padding: "14px 16px",
            marginBottom: 12,
          }}
        >
          <div style={{ color: "#6272a4", fontSize: 11, marginBottom: 8, fontWeight: 600 }}>
            {item.mode === "demo" ? "SCHEMA" : "LIVE API DATA"}
          </div>
          <pre
            style={{
              color: "#cdd6f4",
              fontSize: 12,
              margin: 0,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              lineHeight: 1.5,
            }}
          >
            {JSON.stringify(rawFields, null, 2)}
          </pre>
        </div>
      )}

      {isFieldCatalog && !rawFields && (
        <div style={{ background: "#fff", border: "1px solid #e8eaed", borderRadius: 8, padding: 16, fontSize: 13 }}>
          Official Instagram Graph API field — use in fields= query on IG User or Media objects.
        </div>
      )}
    </div>
  );
}
