import axios from "axios";

const BASE = "http://localhost:8080/api/v1/hubspot";

export interface HSObjectType {
  name: string;
  label: string;
  object_type_id: string;
  type: "standard" | "custom";
}

export interface HSProperty {
  name: string;
  label: string;
  type: string;
  field_type: string;
  description: string;
  group_name: string;
  options: string[];
  created_at: string | null;
  updated_at: string | null;
  calculated: boolean;
  hidden: boolean;
  hubspot_defined: boolean;
  form_field: boolean;
}

export interface HSPropertiesResponse {
  object_type: string;
  properties_count: number;
  properties: HSProperty[];
}

export interface HSSchema extends HSPropertiesResponse {
  name: string;
  type: "standard" | "custom";
  labels?: { singular?: string; plural?: string };
  primary_display_property?: string;
  associations?: unknown[];
}

export interface HSConnectionInfo {
  connected: boolean;
  portal_id: number;
  account_type: string;
  time_zone: string;
  company_currency: string;
  ui_domain: string;
  data_hosting_location: string;
  auth_method: string;
}

export const hubspotApi = {
  connect: () => axios.get<HSConnectionInfo>(`${BASE}/connect`),

  listObjects: () =>
    axios.get<{ objects: HSObjectType[]; total: number }>(`${BASE}/objects`),

  getProperties: (objectType: string) =>
    axios.get<HSPropertiesResponse>(`${BASE}/objects/${objectType}/properties`),

  getSchema: (objectType: string) =>
    axios.get<HSSchema>(`${BASE}/objects/${objectType}/schema`),

  getSampleData: (objectType: string, limit = 5) =>
    axios.get(`${BASE}/objects/${objectType}/sample`, { params: { limit } }),
};
