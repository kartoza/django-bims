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
  timeout: 30000,
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

export default apiClient;
