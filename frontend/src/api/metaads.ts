import axios from "axios";

const BASE = "http://localhost:8000/api/v1/metaads";

export interface MetaConnectResult {
  connected: boolean;
  mode: "live";
  ad_account_id: string;
  ad_account_name: string;
  account_status: number;
  currency: string;
  timezone: string;
  amount_spent: string;
  business_name: string;
  campaigns_sample: number | string;
  platforms: string;
  auth_method: string;
  api_version: string;
}

export interface MetaCategory {
  id: string;
  label: string;
  description: string;
  items_count: number | string;
}

export interface MetaItem {
  name: string;
  label: string;
  description: string;
  data_type?: string;
  type?: string;
  raw?: Record<string, unknown>;
  fields?: Record<string, unknown>;
}

export interface MetaItemsResponse {
  category: string;
  total: number;
  items: MetaItem[];
  mode: "live";
}

export interface MetaItemDetail extends MetaItem {
  category: string;
  mode: "live";
}

export const metaAdsApi = {
  connect: () => axios.get<MetaConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () => axios.get<MetaCategory[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios.get<MetaItemsResponse>(`${BASE}/items`, { params: { category } }).then((r) => r.data),
  itemDetail: (itemId: string, category: string) =>
    axios
      .get<MetaItemDetail>(`${BASE}/items/${encodeURIComponent(itemId)}`, { params: { category } })
      .then((r) => r.data),
};
