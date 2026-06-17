import axios from "axios";

const BASE = "http://localhost:8000/api/v1/workato";

export interface WorkatoConnectResult {
  connected: boolean;
  mode: "live";
  api_base: string;
  workspace_name: string | null;
  workspace_email: string | null;
  plan: string | null;
  connections_count: number;
  recipes_count: number;
  auth_method: string;
  note: string;
}

export interface WorkatoCategory {
  id: string;
  label: string;
  description: string;
  items_count: number | string;
}

export interface WorkatoItem {
  name: string;
  label: string;
  description: string;
  application?: string;
  authorization_status?: string;
  applications?: string[];
  running?: boolean;
  recipe_id?: number | string;
  job_id?: string;
  status?: string;
  raw?: Record<string, unknown>;
}

export interface WorkatoItemsResponse {
  category: string;
  total: number;
  items: WorkatoItem[];
  mode: "live";
}

export interface WorkatoJobLine {
  recipe_line_number: number;
  adapter_name: string;
  adapter_operation: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
}

export interface WorkatoItemDetail {
  category: string;
  mode: "live";
  name: string;
  label: string;
  description: string;
  fields?: Record<string, unknown>;
  lines?: WorkatoJobLine[];
  recent_jobs?: Record<string, unknown>[];
  raw?: Record<string, unknown>;
}

export interface WorkatoSetupStep {
  step: number;
  action: string;
  where: string;
  note: string;
}

export interface WorkatoSetupGuide {
  title: string;
  docs: string;
  trial_url: string;
  env_keys_needed: string[];
  steps: WorkatoSetupStep[];
}

export const workatoApi = {
  connect: () => axios.get<WorkatoConnectResult>(`${BASE}/connect`).then((r) => r.data),
  setupGuide: () => axios.get<WorkatoSetupGuide>(`${BASE}/setup-guide`).then((r) => r.data),
  categories: () => axios.get<WorkatoCategory[]>(`${BASE}/categories`).then((r) => r.data),
  items: (category: string) =>
    axios.get<WorkatoItemsResponse>(`${BASE}/items`, { params: { category } }).then((r) => r.data),
  itemDetail: (itemId: string, category: string) =>
    axios
      .get<WorkatoItemDetail>(`${BASE}/items/${encodeURIComponent(itemId)}`, { params: { category } })
      .then((r) => r.data),
  jobDetail: (recipeId: string, jobId: string) =>
    axios
      .get<Record<string, unknown>>(`${BASE}/recipes/${recipeId}/jobs/${encodeURIComponent(jobId)}`)
      .then((r) => r.data),
};
