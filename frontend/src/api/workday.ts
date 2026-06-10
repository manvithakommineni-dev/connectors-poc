import axios from "axios";

const BASE = "http://localhost:8000/api/v1/workday";

export interface WorkdayConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  modules_count?: number;
  total_objects?: number;
  total_fields?: number;
  workday_api_path?: string;
  tenant?: string;
}

export interface WorkdayModule {
  id: string;
  label: string;
  description: string;
  objects_count: number;
}

export interface WorkdayModulesResponse {
  total: number;
  modules: WorkdayModule[];
}

export interface WorkdayObjectSummary {
  name: string;
  title: string;
  module: string;
  rest_path: string;
  description: string;
  fields_count: number;
  related_count: number;
}

export interface WorkdayModuleObjectsResponse {
  module_id: string;
  module_label: string;
  total: number;
  objects: WorkdayObjectSummary[];
  mode: "demo" | "live";
}

export interface WorkdayField {
  name: string;
  title: string;
  type: string;
  required: boolean;
  filterable: boolean;
  is_key: boolean;
  description: string;
}

export interface WorkdayRelated {
  name: string;
  title: string;
  description: string;
}

export interface WorkdayObjectDescribe {
  name: string;
  title: string;
  module: string;
  rest_path: string;
  description: string;
  fields: WorkdayField[];
  related: WorkdayRelated[];
  fields_count: number;
  related_count: number;
  mode: "demo" | "live";
}

export interface WorkdayAllObjectsResponse {
  total: number;
  objects: WorkdayObjectSummary[];
  mode: "demo" | "live";
}

export const workdayApi = {
  connect: () =>
    axios.get<WorkdayConnectResult>(`${BASE}/connect`).then((r) => r.data),

  listModules: () =>
    axios.get<WorkdayModulesResponse>(`${BASE}/modules`).then((r) => r.data),

  getModuleObjects: (moduleId: string) =>
    axios
      .get<WorkdayModuleObjectsResponse>(`${BASE}/modules/${moduleId}/objects`)
      .then((r) => r.data),

  getAllObjects: () =>
    axios.get<WorkdayAllObjectsResponse>(`${BASE}/objects`).then((r) => r.data),

  describeObject: (objectName: string) =>
    axios
      .get<WorkdayObjectDescribe>(`${BASE}/objects/${objectName}/describe`)
      .then((r) => r.data),
};
