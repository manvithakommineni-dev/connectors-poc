import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { workatoApi } from "../api/workato";
import type { WorkatoCategory, WorkatoItem } from "../api/workato";
import { WorkatoMetadataPanel } from "../components/WorkatoMetadataPanel";

const CATEGORY_ICONS: Record<string, string> = {
  connections: "🔌",
  recipes: "⚙️",
  job_runs: "▶️",
};

export function WorkatoExplorer() {
  const [selectedCategory, setSelectedCategory] = useState<string>("connections");
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const connectQuery = useQuery({
    queryKey: ["workato-connect"],
    queryFn: workatoApi.connect,
    retry: false,
  });

  const setupQuery = useQuery({
    queryKey: ["workato-setup"],
    queryFn: workatoApi.setupGuide,
    enabled: connectQuery.isError,
  });

  const categoriesQuery = useQuery({
    queryKey: ["workato-categories"],
    queryFn: workatoApi.categories,
    enabled: connectQuery.isSuccess,
  });

  const itemsQuery = useQuery({
    queryKey: ["workato-items", selectedCategory],
    queryFn: () => workatoApi.items(selectedCategory),
    enabled: connectQuery.isSuccess && !!selectedCategory,
  });

  const detailQuery = useQuery({
    queryKey: ["workato-detail", selectedCategory, selectedItem],
    queryFn: () => workatoApi.itemDetail(selectedItem!, selectedCategory),
    enabled: !!selectedItem && !!selectedCategory,
  });

  const filteredItems = (itemsQuery.data?.items ?? []).filter(
    (item: WorkatoItem) =>
      !search ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.label.toLowerCase().includes(search.toLowerCase()) ||
      item.description.toLowerCase().includes(search.toLowerCase())
  );

  const setupError =
    connectQuery.error &&
    (connectQuery.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

  return (
    <div style={{ display: "flex", height: "100%", fontFamily: "system-ui, sans-serif" }}>
      <div
        style={{
          width: 220,
          background: "#f8f9fa",
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "14px 16px", borderBottom: "1px solid #e0e0e0", background: "#fff" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 18 }}>🔄</span>
            <span style={{ fontWeight: 700, fontSize: 14, color: "#4f46e5" }}>Workato</span>
          </div>
          <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>iPaaS cross-check</div>
          {connectQuery.isSuccess && (
            <div
              style={{
                marginTop: 6,
                background: "#e8f5e9",
                color: "#2e7d32",
                borderRadius: 6,
                padding: "4px 8px",
                fontSize: 11,
                fontWeight: 600,
                border: "1px solid #a5d6a7",
              }}
            >
              LIVE
            </div>
          )}
          {connectQuery.isError && (
            <div
              style={{
                marginTop: 6,
                background: "#ffebee",
                color: "#c62828",
                borderRadius: 6,
                padding: "4px 8px",
                fontSize: 11,
                fontWeight: 600,
                border: "1px solid #ffcdd2",
              }}
            >
              NOT CONNECTED
            </div>
          )}
        </div>

        {connectQuery.isSuccess && connectQuery.data && (
          <div
            style={{
              padding: "8px 12px",
              fontSize: 10,
              color: "#64748b",
              borderBottom: "1px solid #e0e0e0",
              lineHeight: 1.5,
            }}
          >
            <div>
              <b>{connectQuery.data.connections_count}</b> connections
            </div>
            <div>
              <b>{connectQuery.data.recipes_count}</b> recipes
            </div>
          </div>
        )}

        <div style={{ padding: "10px 8px 6px", fontSize: 11, color: "#888", fontWeight: 600 }}>
          CATEGORIES
        </div>

        {(categoriesQuery.data ?? []).map((cat: WorkatoCategory) => (
          <button
            key={cat.id}
            onClick={() => {
              setSelectedCategory(cat.id);
              setSelectedItem(null);
            }}
            style={{
              margin: "0 8px 2px",
              padding: "8px 10px",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
              textAlign: "left",
              background: selectedCategory === cat.id ? "#ede9fe" : "transparent",
              color: selectedCategory === cat.id ? "#4f46e5" : "#334155",
              fontSize: 12,
              fontWeight: selectedCategory === cat.id ? 600 : 400,
            }}
          >
            {CATEGORY_ICONS[cat.id] ?? "📁"} {cat.label}
            <span style={{ float: "right", opacity: 0.6 }}>{cat.items_count}</span>
          </button>
        ))}
      </div>

      <div
        style={{
          width: 300,
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
          background: "#fff",
        }}
      >
        <div style={{ padding: 12, borderBottom: "1px solid #e0e0e0" }}>
          <input
            placeholder="Search…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              padding: "8px 10px",
              borderRadius: 6,
              border: "1px solid #ddd",
              fontSize: 13,
              boxSizing: "border-box",
            }}
          />
        </div>
        <div style={{ flex: 1, overflow: "auto" }}>
          {connectQuery.isError ? (
            <div style={{ padding: 16, fontSize: 12, color: "#64748b" }}>
              Connect Workato API to browse items.
            </div>
          ) : itemsQuery.isLoading ? (
            <div style={{ padding: 16, fontSize: 12, color: "#888" }}>Loading…</div>
          ) : filteredItems.length === 0 ? (
            <div style={{ padding: 16, fontSize: 12, color: "#888" }}>
              No items. Create connections and run recipe tests in Workato UI first.
            </div>
          ) : (
            filteredItems.map((item: WorkatoItem) => (
              <button
                key={item.name}
                onClick={() => setSelectedItem(item.name)}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "10px 14px",
                  border: "none",
                  borderBottom: "1px solid #f0f0f0",
                  background: selectedItem === item.name ? "#f5f3ff" : "#fff",
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 600, color: "#1e293b" }}>{item.label}</div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{item.description}</div>
              </button>
            ))
          )}
        </div>
      </div>

      <div style={{ flex: 1, background: "#fff", overflow: "hidden" }}>
        {connectQuery.isError ? (
          <div style={{ padding: 24 }}>
            <div
              style={{
                padding: 14,
                background: "#fef2f2",
                border: "1px solid #fecaca",
                borderRadius: 8,
                marginBottom: 20,
                fontSize: 13,
                color: "#b91c1c",
              }}
            >
              {setupError || "Workato API not connected"}
            </div>
            {setupQuery.data && (
              <>
                <h3 style={{ fontSize: 15, color: "#4f46e5", marginBottom: 12 }}>
                  {setupQuery.data.title}
                </h3>
                {setupQuery.data.steps.map((s) => (
                  <div key={s.step} style={{ display: "flex", gap: 12, marginBottom: 14 }}>
                    <div
                      style={{
                        minWidth: 24,
                        height: 24,
                        borderRadius: "50%",
                        background: "#ede9fe",
                        color: "#4f46e5",
                        fontWeight: 700,
                        fontSize: 12,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {s.step}
                    </div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>{s.action}</div>
                      <div style={{ fontSize: 12, color: "#4f46e5" }}>{s.where}</div>
                      <div style={{ fontSize: 11, color: "#64748b" }}>{s.note}</div>
                    </div>
                  </div>
                ))}
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 12 }}>
                  <b>.env keys:</b> {setupQuery.data.env_keys_needed.join(", ")}
                </div>
                <a
                  href={setupQuery.data.docs}
                  target="_blank"
                  rel="noreferrer"
                  style={{ display: "inline-block", marginTop: 12, color: "#4f46e5", fontSize: 12 }}
                >
                  Workato Developer API docs →
                </a>
              </>
            )}
          </div>
        ) : (
          <WorkatoMetadataPanel
            detail={detailQuery.data}
            loading={detailQuery.isLoading}
            category={selectedCategory}
          />
        )}
      </div>
    </div>
  );
}

export default WorkatoExplorer;
