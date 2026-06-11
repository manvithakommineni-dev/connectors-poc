import { GAdsResourceDetail, GAdsField } from "../api/googleads";

interface Props {
  resource: GAdsResourceDetail;
}

const CATEGORY_COLORS: Record<string, string> = {
  ATTRIBUTE: "#4285F4",  // Google Blue
  METRIC:    "#34A853",  // Google Green
  SEGMENT:   "#FBBC05",  // Google Yellow
  RESOURCE:  "#EA4335",  // Google Red
};

const DATA_TYPE_COLORS: Record<string, string> = {
  INT64:   "#1a73e8",
  INT32:   "#1a73e8",
  DOUBLE:  "#137333",
  STRING:  "#b5610f",
  BOOLEAN: "#7b1fa2",
  ENUM:    "#e8710a",
  MESSAGE: "#5f6368",
};

function CategoryBadge({ cat }: { cat: string }) {
  const color = CATEGORY_COLORS[cat] ?? "#5f6368";
  return (
    <span
      style={{
        background: color + "18",
        color,
        border: `1px solid ${color}44`,
        borderRadius: 4,
        padding: "1px 7px",
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.03em",
        textTransform: "uppercase",
      }}
    >
      {cat}
    </span>
  );
}

function DataTypeBadge({ type }: { type: string }) {
  const color = DATA_TYPE_COLORS[type] ?? "#5f6368";
  return (
    <span
      style={{
        background: color + "14",
        color,
        border: `1px solid ${color}33`,
        borderRadius: 3,
        padding: "1px 6px",
        fontSize: 11,
        fontFamily: "monospace",
      }}
    >
      {type}
    </span>
  );
}

function Flag({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      style={{
        fontSize: 10,
        padding: "1px 6px",
        borderRadius: 3,
        background: active ? "#e8f5e9" : "#f5f5f5",
        color: active ? "#2e7d32" : "#9e9e9e",
        border: `1px solid ${active ? "#a5d6a7" : "#e0e0e0"}`,
        fontWeight: active ? 600 : 400,
      }}
    >
      {label}
    </span>
  );
}

export function GoogleAdsMetadataPanel({ resource }: Props) {
  const byCategory: Record<string, GAdsField[]> = {};
  for (const f of resource.fields) {
    if (!byCategory[f.category]) byCategory[f.category] = [];
    byCategory[f.category].push(f);
  }

  const categoryOrder = ["ATTRIBUTE", "METRIC", "SEGMENT", "RESOURCE"];

  return (
    <div style={{ padding: "0 4px" }}>
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #4285F4 0%, #1a73e8 100%)",
          borderRadius: 10,
          padding: "18px 20px",
          marginBottom: 16,
          color: "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>📊</span>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{resource.label}</div>
            <div style={{ fontSize: 12, opacity: 0.85, fontFamily: "monospace" }}>
              {resource.name}
            </div>
          </div>
        </div>
        {resource.description && (
          <div style={{ marginTop: 8, fontSize: 13, opacity: 0.9 }}>{resource.description}</div>
        )}
        <div style={{ marginTop: 10, display: "flex", gap: 12, flexWrap: "wrap", fontSize: 12 }}>
          <span style={{ background: "rgba(255,255,255,0.2)", padding: "3px 10px", borderRadius: 12 }}>
            {resource.fields_count} fields
          </span>
          <span style={{ background: "rgba(255,255,255,0.2)", padding: "3px 10px", borderRadius: 12 }}>
            {resource.mode === "demo" ? "Demo Mode" : "Live"}
          </span>
        </div>
      </div>

      {/* GAQL Example */}
      {resource.gaql_example && (
        <div
          style={{
            background: "#1e1e2e",
            borderRadius: 8,
            padding: "12px 14px",
            marginBottom: 16,
          }}
        >
          <div style={{ color: "#6272a4", fontSize: 11, marginBottom: 6, fontWeight: 600 }}>
            GAQL EXAMPLE QUERY
          </div>
          <code style={{ color: "#cdd6f4", fontSize: 12, wordBreak: "break-all", lineHeight: 1.6 }}>
            {resource.gaql_example}
          </code>
        </div>
      )}

      {/* Fields by category */}
      {categoryOrder.map((cat) => {
        const fields = byCategory[cat];
        if (!fields?.length) return null;
        return (
          <div key={cat} style={{ marginBottom: 20 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 8,
                borderBottom: `2px solid ${CATEGORY_COLORS[cat]}33`,
                paddingBottom: 6,
              }}
            >
              <CategoryBadge cat={cat} />
              <span style={{ fontSize: 12, color: "#666" }}>{fields.length} fields</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {fields.map((f) => (
                <div
                  key={f.name}
                  style={{
                    background: "#fff",
                    border: "1px solid #e8eaed",
                    borderRadius: 8,
                    padding: "10px 14px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <code style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a" }}>{f.name}</code>
                    <DataTypeBadge type={f.data_type} />
                    {f.is_repeated && (
                      <span style={{ fontSize: 11, color: "#0d47a1", background: "#e3f2fd", padding: "1px 6px", borderRadius: 3, border: "1px solid #90caf9" }}>
                        REPEATED
                      </span>
                    )}
                  </div>
                  {f.label && f.label !== f.name && (
                    <div style={{ fontSize: 12, color: "#444", marginTop: 3 }}>{f.label}</div>
                  )}
                  {f.description && (
                    <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>{f.description}</div>
                  )}
                  <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <Flag label="filterable" active={f.filterable} />
                    <Flag label="selectable" active={f.selectable} />
                    <Flag label="sortable" active={f.sortable} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
