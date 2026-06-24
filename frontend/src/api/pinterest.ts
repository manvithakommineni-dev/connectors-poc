import axios from "axios";

const BASE = "http://localhost:8000/api/v1/pinterest";

export interface PinterestConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  categories_count?: number;
  total_fields?: number;
  api_version?: string;
  scopes_needed?: string;
  ad_account_id?: string;
  ad_account_name?: string;
  account_status?: string;
  currency?: string;
  country?: string;
  campaigns_sample?: number;
  platforms?: string;
  auth_method?: string;
}

export interface PinterestCategory {
  id: string;
  label: string;
  description: string;
  items_count: number | string;
}

export interface PinterestItem {
  name: string;
  label: string;
  description: string;
  data_type?: string;
  type?: string;
  raw?: Record<string, unknown>;
  fields?: Record<string, unknown>;
}

export interface PinterestItemsResponse {
  category: string;
  total: number;
  items: PinterestItem[];
  mode: "demo" | "live";
  message?: string;
}

export interface PinterestItemDetail extends PinterestItem {
  category: string;
  mode: "demo" | "live";
}

export const pinterestApi = {
  connect: () => axios.get<PinterestConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () => axios.get<PinterestCategory[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios.get<PinterestItemsResponse>(`${BASE}/items`, { params: { category } }).then((r) => r.data),
  itemDetail: (itemId: string, category: string) =>
    axios
      .get<PinterestItemDetail>(`${BASE}/items/${encodeURIComponent(itemId)}`, { params: { category } })
      .then((r) => r.data),
};
