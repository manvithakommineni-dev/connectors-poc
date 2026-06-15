import axios from "axios";

const BASE = "http://localhost:8000/api/v1/adjust";

export interface AdjustConnectResult {
  connected: boolean;
  mode: "live";
  apps_count: number;
  events_count: number;
  sample_app: string | null;
  auth_method: string;
  api_base: string;
  plan_note: string;
}

export interface AdjustCategory {
  id: string;
  label: string;
  description: string;
  items_count: number | string;
}

export interface AdjustItem {
  name: string;
  label: string;
  description: string;
  raw?: Record<string, unknown>;
  fields?: Record<string, unknown>;
}

export interface AdjustItemsResponse {
  category: string;
  total: number;
  items: AdjustItem[];
  mode: "live";
}

export interface AdjustItemDetail extends AdjustItem {
  category: string;
  mode: "live";
}

export const adjustApi = {
  connect: () => axios.get<AdjustConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () => axios.get<AdjustCategory[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios.get<AdjustItemsResponse>(`${BASE}/items`, { params: { category } }).then((r) => r.data),
  itemDetail: (itemId: string, category: string) =>
    axios
      .get<AdjustItemDetail>(`${BASE}/items/${encodeURIComponent(itemId)}`, { params: { category } })
      .then((r) => r.data),
};
