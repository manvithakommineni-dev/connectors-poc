import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { facebookApi } from "../api/facebook";
import type { FacebookCategory, FacebookItem } from "../api/facebook";
import { FacebookMetadataPanel } from "../components/FacebookMetadataPanel";

const CATEGORY_ICONS: Record<string, string> = {
  page: "👤",
  posts: "📝",
  photos: "🖼️",
  videos: "🎬",
  page_fields: "📐",
  post_fields: "📐",
  photo_fields: "📐",
  video_fields: "📐",
  insights_metrics: "📊",
};

export function FacebookExplorer() {
  const [selectedCategory, setSelectedCategory] = useState<string>("post_fields");
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const connectQuery = useQuery({
    queryKey: ["facebook-connect"],
    queryFn: facebookApi.connect,
    retry: false,
  });

  const categoriesQuery = useQuery({
    queryKey: ["facebook-categories"],
    queryFn: facebookApi.categories,
    enabled: connectQuery.isSuccess,
  });

  const itemsQuery = useQuery({
    queryKey: ["facebook-items", selectedCategory],
    queryFn: () => facebookApi.items(selectedCategory),
    enabled: connectQuery.isSuccess && !!selectedCategory,
  });

  const detailQuery = useQuery({
    queryKey: ["facebook-detail", selectedCategory, selectedItem],
    queryFn: () => facebookApi.itemDetail(selectedItem!, selectedCategory),
    enabled: !!selectedItem && !!selectedCategory,
  });

  const filteredItems = (itemsQuery.data?.items ?? []).filter(
    (item: FacebookItem) =>
      !search ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.label.toLowerCase().includes(search.toLowerCase())
  );

  const isDemo = connectQuery.data?.mode === "demo";
  const isLive = connectQuery.data?.mode === "live";

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
            <span style={{ fontSize: 18 }}>📘</span>
            <span style={{ fontWeight: 700, fontSize: 14, color: "#1877F2" }}>Facebook</span>
          </div>
          <div style={{ fontSize: 10, color: "#0d5dbf", marginTop: 2 }}>Organic Page · Graph API</div>
          {isLive && (
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
          {isDemo && (
            <div
              style={{
                marginTop: 6,
                background: "#fff3e0",
                color: "#e65100",
                borderRadius: 6,
                padding: "4px 8px",
                fontSize: 11,
                fontWeight: 600,
                border: "1px solid #ffcc80",
              }}
            >
              DEMO
            </div>
          )}
        </div>

        <div style={{ padding: "10px 8px 6px", fontSize: 11, color: "#888", fontWeight: 600 }}>
          CATEGORIES
        </div>

        {(categoriesQuery.data ?? []).map((cat: FacebookCategory) => (
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
              background: selectedCategory === cat.id ? "#e7f0fd" : "transparent",
              color: selectedCategory === cat.id ? "#1877F2" : "#333",
              fontWeight: selectedCategory === cat.id ? 600 : 400,
              fontSize: 12,
            }}
          >
            <span style={{ marginRight: 6 }}>{CATEGORY_ICONS[cat.id] ?? "📁"}</span>
            {cat.label}
            <span style={{ float: "right", fontSize: 10, color: "#888" }}>{cat.items_count}</span>
          </button>
        ))}

        {connectQuery.data && isLive && (
          <div
            style={{
              margin: "auto 8px 12px",
              padding: "10px",
              background: "#fff",
              borderRadius: 8,
              border: "1px solid #e0e0e0",
              fontSize: 11,
            }}
          >
            <div style={{ fontWeight: 600 }}>{connectQuery.data.page_name}</div>
            <div>{connectQuery.data.page_id}</div>
            <div>
              {connectQuery.data.fan_count} likes · {connectQuery.data.followers_count} followers
            </div>
          </div>
        )}
      </div>

      <div
        style={{
          width: 280,
          background: "#fff",
          borderRight: "1px solid #e0e0e0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "12px 14px", borderBottom: "1px solid #e0e0e0" }}>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search…"
            style={{
              width: "100%",
              padding: "7px 10px",
              border: "1px solid #dadce0",
              borderRadius: 6,
              fontSize: 13,
              boxSizing: "border-box",
            }}
          />
          {itemsQuery.data && (
            <div style={{ fontSize: 11, color: "#888", marginTop: 6 }}>
              {filteredItems.length} of {itemsQuery.data.total}
              {itemsQuery.data.message && (
                <div style={{ marginTop: 4, color: "#e65100" }}>{itemsQuery.data.message}</div>
              )}
            </div>
          )}
        </div>

        <div style={{ overflowY: "auto", flex: 1 }}>
          {isDemo && (
            <div style={{ padding: 16, fontSize: 12, color: "#555", lineHeight: 1.6 }}>
              <strong>Demo mode — field schemas available now.</strong>
              <ol style={{ paddingLeft: 18, marginTop: 8 }}>
                <li>Create a <b>Facebook Page</b> (free)</li>
                <li>Meta Developer app → get <b>Page access token</b></li>
                <li>Scopes: <code>pages_read_engagement</code>, <code>pages_show_list</code></li>
                <li>Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID in backend/.env</li>
              </ol>
            </div>
          )}

          {filteredItems.map((item: FacebookItem) => (
            <button
              key={item.name}
              onClick={() => setSelectedItem(item.name)}
              style={{
                display: "block",
                width: "100%",
                padding: "10px 14px",
                border: "none",
                borderBottom: "1px solid #f0f0f0",
                background: selectedItem === item.name ? "#e7f0fd" : "#fff",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  fontSize: 13,
                  color: selectedItem === item.name ? "#1877F2" : "#1a1a1a",
                }}
              >
                {item.label || item.name}
              </div>
              <code style={{ fontSize: 11, color: "#666" }}>{item.name}</code>
              {item.description && (
                <div style={{ fontSize: 11, color: "#888", marginTop: 3 }}>{item.description}</div>
              )}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: 20, background: "#f8f9fa" }}>
        {!selectedItem && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "60%",
              color: "#888",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 48, marginBottom: 16 }}>📘</div>
            <div style={{ fontSize: 18, fontWeight: 600, color: "#333", marginBottom: 8 }}>
              Facebook Page Metadata Explorer
            </div>
            <div style={{ fontSize: 13, maxWidth: 440, lineHeight: 1.6 }}>
              Organic Facebook Page content — posts, photos, videos, and field schemas.
              Demo mode works now; add Page credentials in .env for live data.
            </div>
          </div>
        )}

        {detailQuery.data && <FacebookMetadataPanel item={detailQuery.data} />}
      </div>
    </div>
  );
}
