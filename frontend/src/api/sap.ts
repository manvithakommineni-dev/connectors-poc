import axios from "axios";

const BASE = "http://localhost:8000/api/v1/sap";

export interface SAPService {
  name: string;
  label: string;
  description: string;
}

export interface SAPEntitySummary {
  name: string;
  entity_set_name: string;
  fields_count: number;
  key_fields: string[];
  nav_properties_count: number;
}

export interface SAPField {
  name: string;
  type: string;
  simple_type: string;
  nullable: boolean;
  max_length: string | null;
  precision: string | null;
  scale: string | null;
  is_key: boolean;
  label: string;
  creatable: string;
  updatable: string;
  filterable: string;
  sortable: string;
}

export interface SAPNavProperty {
  name: string;
  relationship: string;
  from_role: string;
  to_role: string;
}

export interface SAPEntityFields {
  service_name: string;
  entity_type: string;
  entity_set: string;
  key_fields: string[];
  fields_count: number;
  fields: SAPField[];
  navigation_properties: SAPNavProperty[];
}

export interface SAPEntitiesResponse {
  service_name: string;
  namespace: string;
  total: number;
  entities: SAPEntitySummary[];
}

export interface SAPConnectionInfo {
  connected: boolean;
  base_url: string;
  auth_type: string;
  test_service: string;
  entity_types_found: number;
  entity_sets_found: number;
  namespace: string;
}

export const sapApi = {
  connect: () => axios.get<SAPConnectionInfo>(`${BASE}/connect`),

  listServices: () =>
    axios.get<{ total: number; services: SAPService[] }>(`${BASE}/services`),

  getEntities: (serviceName: string) =>
    axios.get<SAPEntitiesResponse>(`${BASE}/services/${serviceName}/entities`),

  getEntityFields: (serviceName: string, entityName: string) =>
    axios.get<SAPEntityFields>(
      `${BASE}/services/${serviceName}/entities/${entityName}/fields`
    ),

  getServiceMetadata: (serviceName: string) =>
    axios.get(`${BASE}/services/${serviceName}/metadata`),
};
