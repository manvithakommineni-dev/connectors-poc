import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { workdayApi, WorkdayObjectSummary } from "../api/workday";
import { WorkdayMetadataPanel } from "../components/WorkdayMetadataPanel";

const MODULE_COLORS: Record<string, string> = {
  humanResources: "#0d6efd",
  payroll: "#6f42c1",
  recruiting: "#198754",
  benefits: "#d63384",
  timeAndAbsence: "#fd7e14",
  learning: "#0dcaf0",
};

const MODULE_ICONS: Record<string, string> = {
  humanResources: "👥",
  payroll: "💵",
  recruiting: "🎯",
  benefits: "🏥",
  timeAndAbsence: "🕐",
  learning: "📚",
};

export default function WorkdayExplorer() {
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showAll, setShowAll] = useState(false);

  const connectQuery = useQuery({
    queryKey: ["workday-connect"],
    queryFn: workdayApi.connect,
    retry: 1,
  });

  const modulesQuery = useQuery({
    queryKey: ["workday-modules"],
    queryFn: workdayApi.listModules,
    enabled: connectQuery.isSuccess,
  });

  const objectsQuery = useQuery({
    queryKey: ["workday-module-objects", selectedModule],
    queryFn: () => workdayApi.getModuleObjects(selectedModule!),
    enabled: !!selectedModule && !showAll,
  });

  const allObjectsQuery = useQuery({
    queryKey: ["workday-all-objects"],
    queryFn: workdayApi.getAllObjects,
    enabled: showAll,
  });

  const activeObjects: WorkdayObjectSummary[] = showAll
    ? (allObjectsQuery.data?.objects ?? [])
    : (objectsQuery.data?.objects ?? []);

  const filtered = activeObjects.filter(
    (o) =>
      o.name.toLowerCase().includes(search.toLowerCase()) ||
      o.title.toLowerCase().includes(search.toLowerCase()) ||
      o.description.toLowerCase().includes(search.toLowerCase())
  );

  const isDemo = connectQuery.data?.mode === "demo";

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%)",
          borderRadius: 12,
          padding: "24px 28px",
          color: "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <span style={{ fontSize: 32 }}>🔵</span>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>Workday</div>
            <div style={{ fontSize: 13, opacity: 0.85 }}>
              Human Resources · Payroll · Recruiting · Benefits · Time & Absence · Learning
            </div>
          </div>
          {isDemo && (
            <span
              style={{
                marginLeft: "auto",
                background: "rgba(255,255,255,0.25)",
                borderRadius: 6,
                padding: "4px 12px",
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: 1,
              }}
            >
              DEMO MODE
            </span>
          )}
        </div>

        {connectQuery.isLoading && (
          <div style={{ fontSize: 13, opacity: 0.8 }}>Connecting…</div>
        )}
        {connectQuery.isError && (
          <div
            style={{
              background: "rgba(255,255,255,0.2)",
              borderRadius: 6,
              padding: "8px 14px",
              fontSize: 13,
            }}
          >
            ❌ Connection failed — check backend is running on port 8000
          </div>
        )}
        {connectQuery.isSuccess && connectQuery.data && (
          <div
            style={{
              background: "rgba(255,255,255,0.2)",
              borderRadius: 6,
              padding: "10px 14px",
              fontSize: 13,
              display: "flex",
              flexWrap: "wrap",
              gap: 18,
            }}
          >
            <span>✅ Connected</span>
            {connectQuery.data.modules_count != null && (
              <span>Modules: <strong>{connectQuery.data.modules_count}</strong></span>
            )}
            {connectQuery.data.total_objects != null && (
              <span>Objects: <strong>{connectQuery.data.total_objects}</strong></span>
            )}
            {connectQuery.data.total_fields != null && (
              <span>Total Fields: <strong>{connectQuery.data.total_fields}</strong></span>
            )}
            {isDemo && (
              <span style={{ opacity: 0.85 }}>
                Built-in Workday REST API schema · No credentials required
              </span>
            )}
          </div>
        )}
      </div>

      {/* Demo mode banner */}
      {isDemo && (
        <div
          style={{
            background: "#e7f3ff",
            border: "1px solid #b6d4fe",
            borderRadius: 8,
            padding: "12px 16px",
            fontSize: 13,
            color: "#084298",
          }}
        >
          <strong>Demo Mode Active</strong> — Shows real Workday REST API metadata structure
          (Modules, Business Objects, Fields) without needing a Workday account.
          To connect a real tenant: add <code>WORKDAY_TENANT</code>,{" "}
          <code>WORKDAY_CLIENT_ID</code>, <code>WORKDAY_CLIENT_SECRET</code> to{" "}
          <code>backend/.env</code> then restart the backend.
        </div>
      )}

      <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
        {/* Left: Modules + Objects */}
        <div
          style={{
            width: 300,
            minWidth: 300,
            background: "#fff",
            borderRadius: 10,
            border: "1px solid #e9ecef",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "12px 16px",
              background: "#f8f9fa",
              borderBottom: "1px solid #e9ecef",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontWeight: 600, fontSize: 13 }}>
              Modules ({modulesQuery.data?.total ?? 0})
            </span>
            <button
              onClick={() => {
                setShowAll((v) => !v);
                setSelectedObject(null);
              }}
              style={{
                border: "1px solid #e9ecef",
                borderRadius: 4,
                padding: "3px 8px",
                fontSize: 11,
                background: showAll ? "#0d6efd" : "#fff",
                color: showAll ? "#fff" : "#636e72",
                cursor: "pointer",
              }}
            >
              {showAll ? "By Module" : "All Objects"}
            </button>
          </div>

          {/* Module list */}
          {!showAll && (
            <div>
              {modulesQuery.isLoading && (
                <div style={{ padding: 16, color: "#636e72", fontSize: 13 }}>Loading…</div>
              )}
              {modulesQuery.data?.modules.map((mod) => {
                const color = MODULE_COLORS[mod.id] ?? "#0d6efd";
                return (
                  <div
                    key={mod.id}
                    onClick={() => {
                      setSelectedModule(mod.id);
                      setSelectedObject(null);
                      setSearch("");
                    }}
                    style={{
                      padding: "10px 16px",
                      cursor: "pointer",
                      borderBottom: "1px solid #f1f3f5",
                      background: selectedModule === mod.id ? "#f0f7ff" : "transparent",
                      borderLeft: `3px solid ${selectedModule === mod.id ? color : "transparent"}`,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                      <span>{MODULE_ICONS[mod.id] ?? "📁"}</span>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{mod.label}</span>
                      <span
                        style={{
                          marginLeft: "auto",
                          background: "#f1f3f5",
                          borderRadius: 10,
                          padding: "1px 7px",
                          fontSize: 11,
                          color: "#636e72",
                        }}
                      >
                        {mod.objects_count}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: "#888", lineHeight: 1.4 }}>
                      {mod.description.split(",")[0]}…
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Object list */}
          {(selectedModule || showAll) && (
            <div style={{ borderTop: "2px solid #e9ecef" }}>
              <div
                style={{
                  padding: "10px 12px",
                  background: "#f8f9fa",
                  borderBottom: "1px solid #e9ecef",
                }}
              >
                <input
                  type="text"
                  placeholder="Search objects…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px 10px",
                    border: "1px solid #dee2e6",
                    borderRadius: 6,
                    fontSize: 12,
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div style={{ maxHeight: 300, overflowY: "auto" }}>
                {(objectsQuery.isLoading || allObjectsQuery.isLoading) && (
                  <div style={{ padding: 12, fontSize: 12, color: "#636e72" }}>Loading objects…</div>
                )}
                {filtered.map((obj) => {
                  const color = MODULE_COLORS[obj.module] ?? "#0d6efd";
                  return (
                    <div
                      key={obj.name}
                      onClick={() => setSelectedObject(obj.name)}
                      style={{
                        padding: "9px 14px",
                        cursor: "pointer",
                        borderBottom: "1px solid #f1f3f5",
                        background: selectedObject === obj.name ? "#f0f7ff" : "transparent",
                        borderLeft: `3px solid ${selectedObject === obj.name ? color : "transparent"}`,
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: 12 }}>{obj.title}</div>
                      <div style={{ fontSize: 11, color: "#888", fontFamily: "monospace" }}>
                        {obj.name}
                      </div>
                      <div style={{ display: "flex", gap: 8, marginTop: 3, fontSize: 10, color: "#aaa" }}>
                        <span>{obj.fields_count} fields</span>
                        {obj.related_count > 0 && <span>{obj.related_count} related</span>}
                        {showAll && (
                          <span
                            style={{
                              background: color,
                              color: "#fff",
                              borderRadius: 3,
                              padding: "0 5px",
                            }}
                          >
                            {obj.module}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
                {filtered.length === 0 && !objectsQuery.isLoading && !allObjectsQuery.isLoading && (
                  <div style={{ padding: 16, color: "#aaa", fontSize: 12, textAlign: "center" }}>
                    No objects found
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right: Metadata */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selectedObject ? (
            <div
              style={{
                background: "#fff",
                borderRadius: 10,
                border: "1px solid #e9ecef",
                padding: 40,
                textAlign: "center",
                color: "#aaa",
              }}
            >
              <div style={{ fontSize: 48, marginBottom: 12 }}>🔵</div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
                {!selectedModule && !showAll
                  ? "Select a module to browse Workday business objects"
                  : "Select an object to view its fields and metadata"}
              </div>
              <div style={{ fontSize: 13 }}>
                {!selectedModule && !showAll
                  ? "Or click 'All Objects' to see everything at once"
                  : "Field names, data types, required flags, and related resources appear here"}
              </div>
            </div>
          ) : (
            <WorkdayMetadataPanel objectName={selectedObject} />
          )}
        </div>
      </div>
    </div>
  );
}
