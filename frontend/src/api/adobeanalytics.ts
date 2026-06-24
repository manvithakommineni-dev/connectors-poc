import axios from "axios";

const BASE = "http://localhost:8000/api/v1/adobeanalytics";

export interface AdobeAnalyticsConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  categories_count?: number;
  total_fields?: number;
  api_version?: string;
  auth_method?: string;
  report_suite_id?: string;
  report_suite_name?: string;
  company_id?: string;
  dimensions_sample?: number | string;
  metrics_sample?: number | string;
  api_host?: string;
}

export interface AdobeAnalyticsCategory {
  id: string;
  label: string;
  description: string;
  items_count: number | string;
}

export interface AdobeAnalyticsItem {
  name: string;
  label: string;
  description?: string;
  data_type?: string;
  category?: string;
  type?: string;
  raw?: Record<string, unknown>;
  fields?: Record<string, unknown>;
}

export interface AdobeAnalyticsItemsResponse {
  category: string;
  total: number;
  items: AdobeAnalyticsItem[];
  mode: "demo" | "live";
  message?: string;
}

export interface AdobeAnalyticsItemDetail extends AdobeAnalyticsItem {
  category: string;
  mode: "demo" | "live";
}

export const adobeAnalyticsApi = {
  connect: () =>
    axios.get<AdobeAnalyticsConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () =>
    axios.get<AdobeAnalyticsCategory[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios
      .get<AdobeAnalyticsItemsResponse>(`${BASE}/items`, { params: { category } })
      .then((r) => r.data),
  itemDetail: (itemId: string, category: string) =>
    axios
      .get<AdobeAnalyticsItemDetail>(`${BASE}/items/${encodeURIComponent(itemId)}`, {
        params: { category },
      })
      .then((r) => r.data),
};
