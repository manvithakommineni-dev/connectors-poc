import axios from "axios";

const BASE = "http://localhost:8000/api/v1/instagram";

export interface InstagramConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  categories_count?: number;
  total_fields?: number;
  scopes_needed?: string;
  account_id?: string;
  username?: string;
  name?: string;
  followers_count?: number;
  follows_count?: number;
  media_count?: number;
  profile_url?: string;
  media_sample?: number | string;
  auth_method?: string;
  api_version?: string;
  content_type?: string;
}

export interface InstagramCategory {
  id: string;
  label: string;
  description: string;
  items_count: number | string;
}

export interface InstagramItem {
  name: string;
  label: string;
  description: string;
  data_type?: string;
  type?: string;
  raw?: Record<string, unknown>;
  fields?: Record<string, unknown>;
}

export interface InstagramItemsResponse {
  category: string;
  total: number;
  items: InstagramItem[];
  mode: "demo" | "live";
  message?: string;
}

export interface InstagramItemDetail extends InstagramItem {
  category: string;
  mode: "demo" | "live";
}

export const instagramApi = {
  connect: () => axios.get<InstagramConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () => axios.get<InstagramCategory[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios.get<InstagramItemsResponse>(`${BASE}/items`, { params: { category } }).then((r) => r.data),
  itemDetail: (itemId: string, category: string) =>
    axios
      .get<InstagramItemDetail>(`${BASE}/items/${encodeURIComponent(itemId)}`, { params: { category } })
      .then((r) => r.data),
};
