import axios from "axios";

const BASE = "http://localhost:8000/api/v1/youtube";

export interface YouTubeConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  categories_count?: number;
  total_fields?: number;
  api_version?: string;
  scopes_needed?: string;
  channel_id?: string;
  channel_title?: string;
  custom_url?: string;
  subscriber_count?: string;
  video_count?: string;
  view_count?: string;
  auth_method?: string;
}

export interface YouTubeCategory {
  id: string;
  label: string;
  description: string;
  items_count: number | string;
}

export interface YouTubeItem {
  name: string;
  label: string;
  description: string;
  data_type?: string;
  type?: string;
  raw?: Record<string, unknown>;
  fields?: Record<string, unknown>;
}

export interface YouTubeItemsResponse {
  category: string;
  total: number;
  items: YouTubeItem[];
  mode: "demo" | "live";
  message?: string;
}

export interface YouTubeItemDetail extends YouTubeItem {
  category: string;
  mode: "demo" | "live";
}

export const youtubeApi = {
  connect: () => axios.get<YouTubeConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () => axios.get<YouTubeCategory[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios.get<YouTubeItemsResponse>(`${BASE}/items`, { params: { category } }).then((r) => r.data),
  itemDetail: (itemId: string, category: string) =>
    axios
      .get<YouTubeItemDetail>(`${BASE}/items/${encodeURIComponent(itemId)}`, { params: { category } })
      .then((r) => r.data),
};
