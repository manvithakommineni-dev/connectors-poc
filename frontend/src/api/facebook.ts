import axios from "axios";

const BASE = "http://localhost:8000/api/v1/facebook";

export interface FacebookConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  categories_count?: number;
  total_fields?: number;
  scopes_needed?: string;
  page_id?: string;
  page_name?: string;
  category?: string;
  fan_count?: number;
  followers_count?: number;
  link?: string;
  posts_sample?: number | string;
  auth_method?: string;
  api_version?: string;
  content_type?: string;
}

export interface FacebookCategory {
  id: string;
  label: string;
  description: string;
  items_count: number | string;
}

export interface FacebookItem {
  name: string;
  label: string;
  description: string;
  data_type?: string;
  type?: string;
  raw?: Record<string, unknown>;
  fields?: Record<string, unknown>;
}

export interface FacebookItemsResponse {
  category: string;
  total: number;
  items: FacebookItem[];
  mode: "demo" | "live";
  message?: string;
}

export interface FacebookItemDetail extends FacebookItem {
  category: string;
  mode: "demo" | "live";
}

export const facebookApi = {
  connect: () => axios.get<FacebookConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () => axios.get<FacebookCategory[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios.get<FacebookItemsResponse>(`${BASE}/items`, { params: { category } }).then((r) => r.data),
  itemDetail: (itemId: string, category: string) =>
    axios
      .get<FacebookItemDetail>(`${BASE}/items/${encodeURIComponent(itemId)}`, { params: { category } })
      .then((r) => r.data),
};
