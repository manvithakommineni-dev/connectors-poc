import axios from "axios";

const BASE = "http://localhost:8000/api/v1/ga4";

export interface GA4ConnectResult {
  connected: boolean;
  mode: "live";
  property_id: string;
  property_name: string;
  time_zone: string;
  currency_code: string;
  industry_category: string;
  service_level: string;
  dimensions_count: number;
  metrics_count: number;
  auth_method: string;
}

export interface GA4Category {
  id: string;
  label: string;
  description: string;
  items_count: number;
}

export interface GA4Item {
  name: string;
  label: string;
  description: string;
  category?: string;
  type?: string;
  scope?: string;
  custom_definition?: boolean;
  deprecated?: boolean;
  expression?: string;
  measurement_unit?: string;
  measurement_id?: string;
  default_uri?: string;
  stream_id?: string;
  stream_type?: string;
  resource_name?: string;
}

export interface GA4ItemsResponse {
  category: string;
  total: number;
  items: GA4Item[];
  mode: "live";
}

export interface GA4ItemDetail extends GA4Item {
  category: string;
  mode: "live";
}

export const ga4Api = {
  connect: () => axios.get<GA4ConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () => axios.get<GA4Category[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios.get<GA4ItemsResponse>(`${BASE}/items`, { params: { category } }).then((r) => r.data),
  itemDetail: (itemName: string, category: string) =>
    axios
      .get<GA4ItemDetail>(`${BASE}/items/${encodeURIComponent(itemName)}`, {
        params: { category },
      })
      .then((r) => r.data),
};
