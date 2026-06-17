import type { WorkatoItemDetail, WorkatoJobLine } from "../api/workato";

interface Props {
  detail: WorkatoItemDetail | undefined;
  loading: boolean;
  category: string;
}

export function WorkatoMetadataPanel({ detail, loading, category }: Props) {
  if (loading) {
    return (
      <div style={{ padding: 24, color: "#64748b", fontSize: 14 }}>Loading Workato data…</div>
    );
  }

  if (!detail) {
    return (
      <div style={{ padding: 24, color: "#64748b", fontSize: 14 }}>
        Select a {category === "job_runs" ? "job run" : category.slice(0, -1)} to view live data.
      </div>
    );
  }

  return (
    <div style={{ padding: "16px 20px", overflow: "auto", height: "100%" }}>
      <h2 style={{ margin: "0 0 4px", fontSize: 18, color: "#1e293b" }}>{detail.label}</h2>
      <p style={{ margin: "0 0 16px", fontSize: 13, color: "#64748b" }}>{detail.description}</p>

      {detail.fields && (
        <section style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 13, color: "#475569", marginBottom: 8 }}>Summary</h3>
          <div
            style={{
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: 8,
              padding: 12,
              fontSize: 12,
              fontFamily: "monospace",
            }}
          >
            <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {JSON.stringify(detail.fields, null, 2)}
            </pre>
          </div>
        </section>
      )}

      {category === "job_runs" && detail.lines && detail.lines.length > 0 && (
        <section style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 13, color: "#475569", marginBottom: 8 }}>
            Recipe step data (compare with direct connector output)
          </h3>
          {detail.lines.map((line: WorkatoJobLine, idx: number) => (
            <div
              key={idx}
              style={{
                marginBottom: 12,
                border: "1px solid #e2e8f0",
                borderRadius: 8,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  padding: "8px 12px",
                  background: "#4f46e5",
                  color: "#fff",
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                Step {line.recipe_line_number}: {line.adapter_name} → {line.adapter_operation}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0 }}>
                <div style={{ padding: 10, borderRight: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 4 }}>
                    INPUT
                  </div>
                  <pre
                    style={{
                      margin: 0,
                      fontSize: 11,
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                      maxHeight: 240,
                      overflow: "auto",
                    }}
                  >
                    {JSON.stringify(line.input, null, 2)}
                  </pre>
                </div>
                <div style={{ padding: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", marginBottom: 4 }}>
                    OUTPUT (live data)
                  </div>
                  <pre
                    style={{
                      margin: 0,
                      fontSize: 11,
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                      maxHeight: 240,
                      overflow: "auto",
                    }}
                  >
                    {JSON.stringify(line.output, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </section>
      )}

      {category === "recipes" && detail.recent_jobs && detail.recent_jobs.length > 0 && (
        <section style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 13, color: "#475569", marginBottom: 8 }}>Recent jobs</h3>
          <pre
            style={{
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: 8,
              padding: 12,
              fontSize: 11,
              overflow: "auto",
              maxHeight: 200,
            }}
          >
            {JSON.stringify(detail.recent_jobs, null, 2)}
          </pre>
        </section>
      )}

      <section>
        <h3 style={{ fontSize: 13, color: "#475569", marginBottom: 8 }}>Raw API response</h3>
        <pre
          style={{
            background: "#0f172a",
            color: "#e2e8f0",
            borderRadius: 8,
            padding: 12,
            fontSize: 11,
            overflow: "auto",
            maxHeight: 360,
          }}
        >
          {JSON.stringify(detail.raw, null, 2)}
        </pre>
      </section>
    </div>
  );
}
