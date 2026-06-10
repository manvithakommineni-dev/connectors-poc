import axios from "axios";

const BASE = "http://localhost:8000/api/v1/oracle";

export interface OracleConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  modules_count?: number;
  total_resources?: number;
  oracle_api_path?: string;
  base_url?: string;
}

export interface OracleModule {
  id: string;
  label: string;
  description: string;
  resources_count: number;
}

export interface OracleModulesResponse {
  total: number;
  modules: OracleModule[];
}

export interface OracleResourceSummary {
  name: string;
  title: string;
  module: string;
  description: string;
  attributes_count: number;
  children_count: number;
}

export interface OracleModuleResourcesResponse {
  module_id: string;
  module_label: string;
  total: number;
  resources: OracleResourceSummary[];
  mode: "demo" | "live";
}

export interface OracleAttribute {
  name: string;
  title: string;
  type: string;
  required: boolean;
  queryable: boolean;
  updatable: boolean;
  is_key: boolean;
  max_length: number | null;
}

export interface OracleChildResource {
  name: string;
  title: string;
  description: string;
}

export interface OracleResourceDescribe {
  name: string;
  title: string;
  module: string;
  description: string;
  attributes: OracleAttribute[];
  children: OracleChildResource[];
  attributes_count: number;
  children_count: number;
  mode: "demo" | "live";
}

export interface OracleAllResourcesResponse {
  total: number;
  resources: OracleResourceSummary[];
  mode: "demo" | "live";
}

export const oracleApi = {
  connect: () =>
    axios.get<OracleConnectResult>(`${BASE}/connect`).then((r) => r.data),

  listModules: () =>
    axios.get<OracleModulesResponse>(`${BASE}/modules`).then((r) => r.data),

  getModuleResources: (moduleId: string) =>
    axios
      .get<OracleModuleResourcesResponse>(`${BASE}/modules/${moduleId}/resources`)
      .then((r) => r.data),

  getAllResources: () =>
    axios
      .get<OracleAllResourcesResponse>(`${BASE}/resources`)
      .then((r) => r.data),

  describeResource: (resourceName: string) =>
    axios
      .get<OracleResourceDescribe>(`${BASE}/resources/${resourceName}/describe`)
      .then((r) => r.data),
};
