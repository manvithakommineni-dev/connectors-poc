import axios from "axios";

const BASE = "http://localhost:8000/api/v1/servicenow";

export interface SNConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  categories_count?: number;
  total_tables?: number;
  total_fields?: number;
  instance_url?: string;
}

export interface SNCategory {
  id: string;
  label: string;
  description: string;
  tables_count: number;
}

export interface SNCategoriesResponse {
  total: number;
  categories: SNCategory[];
}

export interface SNTableSummary {
  name: string;
  label: string;
  category: string;
  description: string;
  is_extendable: boolean;
  fields_count: number | null;
}

export interface SNTablesResponse {
  total: number;
  tables: SNTableSummary[];
  mode: "demo" | "live";
}

export interface SNField {
  name: string;
  label: string;
  type: string;
  mandatory: boolean;
  is_key: boolean;
  max_length: number | null;
  reference: string | null;
  description: string;
}

export interface SNTableFields {
  table_name: string;
  table_label: string;
  description: string;
  is_extendable: boolean;
  fields_count: number;
  fields: SNField[];
  mode: "demo" | "live";
}

export const servicenowApi = {
  connect: () =>
    axios.get<SNConnectResult>(`${BASE}/connect`).then((r) => r.data),

  listCategories: () =>
    axios.get<SNCategoriesResponse>(`${BASE}/categories`).then((r) => r.data),

  listTables: (category?: string, search?: string, limit = 100) => {
    const params: Record<string, string | number> = { limit };
    if (category) params.category = category;
    if (search) params.search = search;
    return axios.get<SNTablesResponse>(`${BASE}/tables`, { params }).then((r) => r.data);
  },

  getTableFields: (tableName: string) =>
    axios.get<SNTableFields>(`${BASE}/tables/${tableName}/fields`).then((r) => r.data),
};
