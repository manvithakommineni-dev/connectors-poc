import type { SFObject } from "../api/salesforce";

interface Props {
  objects: SFObject[];
  loading: boolean;
  selected: string | null;
  onSelect: (name: string) => void;
}

export default function ObjectList({ objects, loading, selected, onSelect }: Props) {
  if (loading) {
    return (
      <div style={{ padding: 16, color: "#94a3b8", fontSize: 13 }}>
        Loading objects...
      </div>
    );
  }

  if (objects.length === 0) {
    return (
      <div style={{ padding: 16, color: "#475569", fontSize: 13 }}>
        No objects found.
      </div>
    );
  }

  return (
    <div style={{ overflowY: "auto", flex: 1 }}>
      {objects.map((obj) => (
        <div
          key={obj.name}
          onClick={() => onSelect(obj.name)}
          style={{
            padding: "10px 16px",
            cursor: "pointer",
            borderBottom: "1px solid #1e293b",
            background: selected === obj.name ? "#1e3a5f" : "transparent",
            transition: "background 0.15s",
          }}
          onMouseEnter={(e) => {
            if (selected !== obj.name)
              (e.currentTarget as HTMLDivElement).style.background = "#1e293b";
          }}
          onMouseLeave={(e) => {
            if (selected !== obj.name)
              (e.currentTarget as HTMLDivElement).style.background = "transparent";
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: selected === obj.name ? "#38bdf8" : "#e2e8f0" }}>
              {obj.label}
            </span>
            {obj.custom && (
              <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 10, background: "#312e81", color: "#a5b4fc" }}>
                Custom
              </span>
            )}
          </div>
          <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{obj.name}</div>
        </div>
      ))}
    </div>
  );
}
