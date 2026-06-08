import { useQuery } from "@tanstack/react-query";
import { salesforceApi } from "../api/salesforce";

interface Props {
  error: string;
}

export default function SetupGuide({ error }: Props) {
  const guideQuery = useQuery({
    queryKey: ["sf-setup-guide"],
    queryFn: () => salesforceApi.getSetupGuide().then((r) => r.data),
  });

  return (
    <div style={{ margin: "24px", padding: "20px", background: "#0f1f35", border: "1px solid #991b1b", borderRadius: 10 }}>
      {/* Error banner */}
      <div style={{ padding: "12px 16px", background: "#450a0a", borderRadius: 8, marginBottom: 20 }}>
        <span style={{ color: "#f87171", fontWeight: 700, fontSize: 14 }}>Connection Failed</span>
        <div style={{ color: "#fca5a5", fontSize: 12, marginTop: 4, fontFamily: "monospace", wordBreak: "break-all" }}>
          {error.replace(/^Error: /, "").replace(/^AxiosError: /, "").substring(0, 300)}
        </div>
      </div>

      {/* Setup steps */}
      <div style={{ color: "#f59e0b", fontWeight: 700, fontSize: 14, marginBottom: 12 }}>
        Required Setup Steps to Fix This
      </div>

      {guideQuery.isLoading && (
        <div style={{ color: "#94a3b8", fontSize: 13 }}>Loading setup guide...</div>
      )}

      {guideQuery.data && (
        <div>
          {guideQuery.data.steps.map((s: any) => (
            <div key={s.step} style={{ display: "flex", gap: 12, marginBottom: 14, alignItems: "flex-start" }}>
              <div style={{
                minWidth: 26, height: 26, borderRadius: "50%", background: "#1e3a5f",
                color: "#38bdf8", fontWeight: 700, fontSize: 13,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {s.step}
              </div>
              <div>
                <div style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600 }}>{s.action}</div>
                <div style={{ color: "#60a5fa", fontSize: 12, marginTop: 2 }}>📍 {s.where}</div>
                <div style={{ color: "#94a3b8", fontSize: 11, marginTop: 2 }}>💡 {s.note}</div>
              </div>
            </div>
          ))}

          <div style={{ marginTop: 16, padding: "10px 14px", background: "#0d2136", borderRadius: 8, fontSize: 12, color: "#94a3b8" }}>
            <b style={{ color: "#a3e635" }}>Required .env keys: </b>
            {guideQuery.data.env_keys_needed.join(", ")}
          </div>

          <a
            href={guideQuery.data.docs}
            target="_blank"
            rel="noreferrer"
            style={{ display: "inline-block", marginTop: 12, color: "#38bdf8", fontSize: 12 }}
          >
            📖 Salesforce OAuth Username-Password Flow docs →
          </a>
        </div>
      )}
    </div>
  );
}
