import axios from "axios";

const BASE = "http://localhost:8000/api/v1/netsuite";

export interface NSConnectResult {
  connected: boolean;
  mode: "demo" | "live";
  message?: string;
  modules_count?: number;
  total_record_types?: number;
  total_fields?: number;
  account_id?: string;
}

export interface NSModule {
  id: string;
  label: string;
  description: string;
  records_count: number;
}

export interface NSModulesResponse {
  total: number;
  modules: NSModule[];
}

export interface NSRecordSummary {
  name: string;
  label: string;
  module: string;
  description: string;
  fields_count: number;
}

export interface NSModuleRecordsResponse {
  module_id: string;
  module_label: string;
  total: number;
  records: NSRecordSummary[];
  mode: "demo" | "live";
}

export interface NSField {
  name: string;
  label: string;
  type: string;
  nullable: boolean;
  readOnly: boolean;
  is_key: boolean;
  referenceType: string | null;
  description: string;
}

export interface NSRecordDescribe {
  name: string;
  label: string;
  module: string;
  description: string;
  fields: NSField[];
  fields_count: number;
  mode: "demo" | "live";
}

export interface NSAllRecordsResponse {
  total: number;
  records: NSRecordSummary[];
  mode: "demo" | "live";
}

export const netsuiteApi = {
  connect: () =>
    axios.get<NSConnectResult>(`${BASE}/connect`).then((r) => r.data),

  listModules: () =>
    axios.get<NSModulesResponse>(`${BASE}/modules`).then((r) => r.data),

  getModuleRecords: (moduleId: string) =>
    axios.get<NSModuleRecordsResponse>(`${BASE}/modules/${moduleId}/records`).then((r) => r.data),

  getAllRecords: () =>
    axios.get<NSAllRecordsResponse>(`${BASE}/records`).then((r) => r.data),

  getRecordFields: (recordType: string) =>
    axios.get<NSRecordDescribe>(`${BASE}/records/${recordType}/fields`).then((r) => r.data),
};
