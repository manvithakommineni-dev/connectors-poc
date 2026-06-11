import axios from "axios";

const BASE = "http://localhost:8000/api/v1/googleads";

export interface GAdsConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  categories_count?: number;
  total_resources?: number;
  total_fields?: number;
  api_version?: string;
  customer_id?: string;
}

export interface GAdsCategory {
  id: string;
  label: string;
  description: string;
  resources_count: number;
}

export interface GAdsResourceSummary {
  name: string;
  label: string;
  category: string;
  description: string;
  fields_count: number;
  gaql_example: string;
}

export interface GAdsResourcesResponse {
  total: number;
  resources: GAdsResourceSummary[];
  mode: "demo" | "live";
}

export interface GAdsField {
  name: string;
  label: string;
  data_type: string;           // INT64, STRING, DOUBLE, BOOLEAN, ENUM, MESSAGE
  category: "ATTRIBUTE" | "METRIC" | "SEGMENT" | "RESOURCE";
  filterable: boolean;
  selectable: boolean;
  sortable: boolean;
  is_repeated: boolean;
  description: string;
}

export interface GAdsResourceDetail {
  name: string;
  label: string;
  category: string;
  description: string;
  fields: GAdsField[];
  fields_count: number;
  gaql_example: string;
  mode: "demo" | "live";
}

export const googleAdsApi = {
  connect: () => axios.get<GAdsConnectResult>(`${BASE}/connect`).then((r) => r.data),
  categories: () => axios.get<GAdsCategory[]>(`${BASE}/categories`).then((r) => r.data),
  resources: (category?: string) =>
    axios
      .get<GAdsResourcesResponse>(`${BASE}/resources`, { params: category ? { category } : {} })
      .then((r) => r.data),
  resourceFields: (resourceName: string) =>
    axios.get<GAdsResourceDetail>(`${BASE}/resources/${resourceName}/fields`).then((r) => r.data),
};
