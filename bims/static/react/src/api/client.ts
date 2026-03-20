/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * API client for BIMS v1 API.
 */
import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import type { ApiResponse, PaginatedResponse } from '../types';

// CSRF token handling for Django
function getCsrfToken(): string | null {
  const cookie = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : null;
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1/',
  timeout: 60000, // 60 second timeout for large queries
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor to add CSRF token
apiClient.interceptors.request.use(
  (config) => {
    const csrfToken = getCsrfToken();
    if (csrfToken && config.headers) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;

      if (status === 401) {
        // Unauthorized - redirect to login
        window.location.href = '/accounts/login/?next=' + window.location.pathname;
      } else if (status === 403) {
        // Forbidden - show error message
        console.error('Permission denied');
      } else if (status >= 500) {
        // Server error
        console.error('Server error occurred');
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('Network error - no response received');
    }

    return Promise.reject(error);
  }
);

// Generic API methods
export const api = {
  // GET request
  async get<T>(url: string, params?: Record<string, unknown>): Promise<ApiResponse<T>> {
    const response = await apiClient.get<ApiResponse<T>>(url, { params });
    return response.data;
  },

  // GET request with pagination
  async getList<T>(url: string, params?: Record<string, unknown>): Promise<PaginatedResponse<T>> {
    const response = await apiClient.get<PaginatedResponse<T>>(url, { params });
    return response.data;
  },

  // POST request
  async post<T>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await apiClient.post<ApiResponse<T>>(url, data);
    return response.data;
  },

  // PUT request
  async put<T>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await apiClient.put<ApiResponse<T>>(url, data);
    return response.data;
  },

  // PATCH request
  async patch<T>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await apiClient.patch<ApiResponse<T>>(url, data);
    return response.data;
  },

  // DELETE request
  async delete<T>(url: string): Promise<ApiResponse<T>> {
    const response = await apiClient.delete<ApiResponse<T>>(url);
    return response.data;
  },

  // File upload
  async upload<T>(url: string, formData: FormData): Promise<ApiResponse<T>> {
    const response = await apiClient.post<ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Resource-specific API methods
export const sitesApi = {
  list: (params?: Record<string, unknown>) => api.getList<any>('sites/', params),
  get: (id: number) => api.get<any>(`sites/${id}/`),
  create: (data: unknown) => api.post<any>('sites/', data),
  update: (id: number, data: unknown) => api.patch<any>(`sites/${id}/`, data),
  delete: (id: number) => api.delete<any>(`sites/${id}/`),
  summary: () => api.get<any>('sites/summary/'),
  nearby: (lat: number, lon: number, radius?: number) =>
    api.get<any>('sites/nearby/', { lat, lon, radius }),
  validate: (id: number) => api.post<any>(`sites/${id}/validate/`),
  reject: (id: number, reason?: string) => api.post<any>(`sites/${id}/reject/`, { reason }),
  surveys: (id: number) => api.get<any>(`sites/${id}/surveys/`),
  records: (id: number, params?: Record<string, unknown>) =>
    api.getList<any>(`sites/${id}/records/`, params),
};

export const recordsApi = {
  list: (params?: Record<string, unknown>) => api.getList<any>('records/', params),
  get: (id: number) => api.get<any>(`records/${id}/`),
  create: (data: unknown) => api.post<any>('records/', data),
  update: (id: number, data: unknown) => api.patch<any>(`records/${id}/`, data),
  delete: (id: number) => api.delete<any>(`records/${id}/`),
  summary: (params?: Record<string, unknown>) => api.get<any>('records/summary/', params),
  search: (params?: Record<string, unknown>) => api.getList<any>('records/search/', params),
  validate: (id: number) => api.post<any>(`records/${id}/validate/`),
  bySite: (siteId: number) => api.getList<any>('records/by_site/', { site_id: siteId }),
  byTaxon: (taxonomyId: number) => api.getList<any>('records/by_taxon/', { taxonomy_id: taxonomyId }),
};

export const taxaApi = {
  list: (params?: Record<string, unknown>) => api.getList<any>('taxa/', params),
  get: (id: number) => api.get<any>(`taxa/${id}/`),
  find: (query: string, rank?: string) => api.get<any>('taxa/find/', { q: query, rank }),
  tree: (id: number, direction?: string, depth?: number) =>
    api.get<any>(`taxa/${id}/tree/`, { direction, depth }),
  images: (id: number) => api.get<any>(`taxa/${id}/images/`),
  proposals: () => api.getList<any>('taxa/proposals/'),
  validate: (id: number) => api.post<any>(`taxa/${id}/validate/`),
  records: (id: number, params?: Record<string, unknown>) =>
    api.getList<any>(`taxa/${id}/records/`, params),
};

export const taxonGroupsApi = {
  list: () => api.getList<any>('taxon-groups/'),
  get: (id: number) => api.get<any>(`taxon-groups/${id}/`),
  taxa: (id: number, params?: Record<string, unknown>) =>
    api.getList<any>(`taxon-groups/${id}/taxa/`, params),
  summary: () => api.get<any>('taxon-groups/summary/'),
};

export const surveysApi = {
  list: (params?: Record<string, unknown>) => api.getList<any>('surveys/', params),
  get: (id: number) => api.get<any>(`surveys/${id}/`),
  create: (data: unknown) => api.post<any>('surveys/', data),
  update: (id: number, data: unknown) => api.patch<any>(`surveys/${id}/`, data),
  delete: (id: number) => api.delete<any>(`surveys/${id}/`),
  validate: (id: number) => api.post<any>(`surveys/${id}/validate/`),
  bulkValidate: (surveyIds: number[]) => api.post<any>('surveys/bulk_validate/', { survey_ids: surveyIds }),
  bulkReject: (surveyIds: number[], reason?: string) =>
    api.post<any>('surveys/bulk_reject/', { survey_ids: surveyIds, reason }),
  records: (id: number) => api.getList<any>(`surveys/${id}/records/`),
};

export const boundariesApi = {
  list: (type?: string) => api.getList<any>('boundaries/', { type }),
  get: (id: number) => api.get<any>(`boundaries/${id}/`),
  geojson: (id: number) => api.get<any>(`boundaries/${id}/geojson/`),
  types: () => api.get<any>('boundaries/types/'),
};

export const userBoundariesApi = {
  list: () => api.getList<any>('user-boundaries/'),
  get: (id: number) => api.get<any>(`user-boundaries/${id}/`),
  create: (data: unknown) => api.post<any>('user-boundaries/', data),
  update: (id: number, data: unknown) => api.patch<any>(`user-boundaries/${id}/`, data),
  delete: (id: number) => api.delete<any>(`user-boundaries/${id}/`),
};

export const downloadsApi = {
  csv: (filters?: Record<string, unknown>) => api.post<any>('downloads/csv/', { filters }),
  checklist: (taxonGroupId: number, boundaryId?: number) =>
    api.post<any>('downloads/checklist/', { taxon_group_id: taxonGroupId, boundary_id: boundaryId }),
  status: (taskId: string) => api.get<any>(`downloads/${taskId}/status/`),
};

export const tasksApi = {
  get: (taskId: string) => api.get<any>(`tasks/${taskId}/`),
  cancel: (taskId: string) => api.delete<any>(`tasks/${taskId}/`),
};

// Legacy API client for endpoints not yet migrated to v1
const legacyClient = axios.create({
  baseURL: '/api/',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Add CSRF token to legacy client
legacyClient.interceptors.request.use(
  (config) => {
    const csrfToken = getCsrfToken();
    if (csrfToken && config.headers) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Chart data API (legacy endpoints)
export interface ChartData {
  dataset_labels: string[];
  labels: string[];
  data: Record<string, number[]>;
  colours?: Record<string, string>;
}

export const chartsApi = {
  // Endemism chart data for filtered records
  endemism: async (filters?: Record<string, unknown>): Promise<ChartData> => {
    const response = await legacyClient.get<ChartData>('location-sites-endemism-chart-data/', { params: filters });
    return response.data;
  },

  // Conservation status (IUCN) chart data
  conservation: async (filters?: Record<string, unknown>): Promise<ChartData> => {
    const response = await legacyClient.get<ChartData>('location-sites-cons-chart-data/', { params: filters });
    return response.data;
  },

  // Taxa distribution chart data
  taxa: async (filters?: Record<string, unknown>): Promise<ChartData> => {
    const response = await legacyClient.get<ChartData>('location-sites-taxa-chart-data/', { params: filters });
    return response.data;
  },

  // Occurrences by origin chart data
  occurrences: async (filters?: Record<string, unknown>): Promise<ChartData> => {
    const response = await legacyClient.get<ChartData>('location-sites-occurrences-chart-data/', { params: filters });
    return response.data;
  },

  // Total occurrences chart data
  totalOccurrences: async (filters?: Record<string, unknown>): Promise<ChartData> => {
    const response = await legacyClient.get<ChartData>('location-sites-total-occurrences-chart-data/', { params: filters });
    return response.data;
  },
};

// Filter options API (legacy endpoints)
export const filterOptionsApi = {
  // Get list of boundaries for filtering
  boundaries: async (type?: string) => {
    const response = await legacyClient.get<any[]>('list-boundary/', { params: { type } });
    return response.data;
  },

  // Get list of collectors for autocomplete
  collectors: async () => {
    const response = await legacyClient.get<any[]>('list-collector/');
    return response.data;
  },

  // Get endemism options
  endemism: async () => {
    const response = await legacyClient.get<any[]>('endemism-list/');
    return response.data;
  },

  // Get reference categories
  referenceCategories: async () => {
    const response = await legacyClient.get<Array<{ category: string }>>('list-reference-category/');
    return response.data;
  },

  // Get data source descriptions
  dataSources: async () => {
    const response = await legacyClient.get<Record<string, string>>('data-source-descriptions/');
    return response.data;
  },

  // Get non-biodiversity layers (context layers)
  contextLayers: async () => {
    const response = await legacyClient.get<any[]>('list-non-biodiversity-layer/');
    return response.data;
  },
};

// Autocomplete API
export const autocompleteApi = {
  // Autocomplete for collectors
  collectors: async (query: string) => {
    const response = await apiClient.get<{ data: string[] }>('autocomplete/collectors/', { params: { q: query } });
    return response.data?.data || [];
  },

  // Autocomplete for taxa
  taxa: async (query: string, taxonGroup?: string) => {
    const response = await apiClient.get<{ data: any[] }>('autocomplete/taxa/', {
      params: { q: query, taxon_group: taxonGroup },
    });
    return response.data?.data || [];
  },

  // Autocomplete for sites
  sites: async (query: string) => {
    const response = await apiClient.get<{ data: any[] }>('autocomplete/sites/', { params: { q: query } });
    return response.data?.data || [];
  },
};

// Site detail API (combines multiple data sources)
export const siteDetailApi = {
  // Get full site details including charts
  getFullDetails: async (siteId: number) => {
    const [site, chartFilters] = await Promise.all([
      sitesApi.get(siteId),
      { siteId: String(siteId) },
    ]);
    return site;
  },

  // Get chart data for a specific site
  getCharts: async (siteId: number) => {
    const filters = { siteId: String(siteId) };
    const [endemism, conservation, taxa, occurrences] = await Promise.all([
      chartsApi.endemism(filters).catch(() => null),
      chartsApi.conservation(filters).catch(() => null),
      chartsApi.taxa(filters).catch(() => null),
      chartsApi.occurrences(filters).catch(() => null),
    ]);
    return { endemism, conservation, taxa, occurrences };
  },
};

// Taxon images API
export const taxonImagesApi = {
  // Get images for a taxon
  getImages: async (taxonId: number) => {
    const response = await legacyClient.get<any[]>(`taxon-images/${taxonId}/`);
    return response.data;
  },
};

// Module summary API (for landing page taxon groups)
export interface ModuleSummary {
  total: number;
  total_site: number;
  total_site_visit: number;
  total_validated: number;
  icon?: string;
  origin?: Record<string, number>;
  endemism?: Record<string, number>;
  'conservation-status'?: {
    chart_data: Record<string, number>;
    colors: string[];
  };
}

export interface GeneralSummary {
  total_occurrences: number;
  total_taxa: number;
  total_users: number;
  total_uploads: number;
  total_downloads: number;
}

export interface ModuleSummaryResponse {
  status?: string;
  message?: string;
  general_summary: GeneralSummary;
  [moduleName: string]: ModuleSummary | GeneralSummary | string | undefined;
}

export const moduleSummaryApi = {
  // Get module summary for landing page
  getSummary: async (): Promise<ModuleSummaryResponse> => {
    const response = await legacyClient.get<ModuleSummaryResponse>('module-summary/');
    return response.data;
  },
};

// Location site detail API
export const locationSiteApi = {
  // Get site detail
  getDetail: async (siteId: number) => {
    const response = await legacyClient.get<any>('location-site-detail/', {
      params: { siteId },
    });
    return response.data;
  },

  // Get site summary (public)
  getSummaryPublic: async (siteId: number) => {
    const response = await legacyClient.get<any>('location-site-summary-public/', {
      params: { siteId },
    });
    return response.data;
  },

  // Get location context report
  getContextReport: async (siteId: number) => {
    const response = await legacyClient.get<any>('location-context-report/', {
      params: { siteId },
    });
    return response.data;
  },
};

// Export legacy client for direct use if needed
export { legacyClient };

// Export apiClient as both named and default export
export { apiClient };
export default apiClient;
