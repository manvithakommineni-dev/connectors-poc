import axios from "axios";

const BASE = "http://localhost:8000/api/v1/salesforce";

export interface SFObject {
  name: string;
  label: string;
  label_plural: string;
  queryable: boolean;
  createable: boolean;
  updateable: boolean;
  deletable: boolean;
  custom: boolean;
  key_prefix: string | null;
}

export interface SFField {
  name: string;
  label: string;
  type: string;
  length: number | null;
  nillable: boolean;
  unique: boolean;
  custom: boolean;
  picklist_values: string[];
  reference_to: string[];
  relationship_name: string | null;
  createable: boolean;
  updateable: boolean;
  filterable: boolean;
  sortable: boolean;
}

export interface SFObjectMetadata {
  name: string;
  label: string;
  label_plural: string;
  custom: boolean;
  fields: SFField[];
  fields_count: number;
  child_relationships: Array<{
    child_sobject: string;
    field: string;
    relationship_name: string | null;
    cascade_delete: boolean;
  }>;
  record_types: Array<{ id: string; name: string; developer_name: string }>;
}

export interface ConnectionInfo {
  connected: boolean;
  instance_url: string;
  api_version: string;
  org_objects_count: number;
  username: string;
}

export const salesforceApi = {
  ping: () => axios.get(`${BASE}/ping`),

  connect: () => axios.get<ConnectionInfo>(`${BASE}/connect`),

  listObjects: (queryableOnly = true, customOnly = false) =>
    axios.get<{ total: number; objects: SFObject[] }>(`${BASE}/objects`, {
      params: { queryable_only: queryableOnly, custom_only: customOnly },
    }),

  getMetadata: (objectName: string) =>
    axios.get<SFObjectMetadata>(`${BASE}/objects/${objectName}/metadata`),

  getSampleData: (objectName: string, limit = 5) =>
    axios.get(`${BASE}/objects/${objectName}/sample`, { params: { limit } }),
};
