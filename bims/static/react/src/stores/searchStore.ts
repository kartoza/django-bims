/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Zustand store for search state management.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  SearchFilters,
  BiologicalCollectionRecord,
  BiologicalRecord,
  LocationSite,
  Taxonomy,
} from '../types';
import { apiClient } from '../api/client';

interface SearchResults {
  records: BiologicalCollectionRecord[];
  sites: LocationSite[];
  taxa: Taxonomy[];
  totalRecords: number;
  totalSites: number;
  totalTaxa: number;
}

interface SearchState {
  // Query
  query: string;

  // Filters
  filters: SearchFilters;
  activeFilters: string[];

  // Results (flat list for SearchPanel)
  results: BiologicalRecord[];
  totalCount: number | null;

  // Full results
  fullResults: SearchResults;
  isLoading: boolean;
  error: string | null;

  // Pagination
  page: number;
  pageSize: number;
  totalPages: number;

  // UI State
  isSearchPanelOpen: boolean;
  activeTab: 'records' | 'sites' | 'taxa';
  sortBy: string;
  sortOrder: 'asc' | 'desc';

  // Computed
  activeFilterCount: number;

  // Actions
  setQuery: (query: string) => void;
  setFilter: (key: string, value: unknown) => void;
  setFilters: (filters: Partial<SearchFilters>) => void;
  clearFilter: (key: string) => void;
  clearFilters: () => void;
  clearAllFilters: () => void;

  search: () => Promise<void>;
  setResults: (results: Partial<SearchResults>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setTotalPages: (totalPages: number) => void;

  toggleSearchPanel: () => void;
  setActiveTab: (tab: 'records' | 'sites' | 'taxa') => void;
  setSortBy: (field: string) => void;
  setSortOrder: (order: 'asc' | 'desc') => void;

  reset: () => void;
}

const initialFilters: SearchFilters = {};

const initialFullResults: SearchResults = {
  records: [],
  sites: [],
  taxa: [],
  totalRecords: 0,
  totalSites: 0,
  totalTaxa: 0,
};

const initialState = {
  query: '',
  filters: initialFilters,
  activeFilters: [] as string[],
  results: [] as BiologicalRecord[],
  totalCount: null as number | null,
  fullResults: initialFullResults,
  isLoading: false,
  error: null as string | null,
  page: 1,
  pageSize: 20,
  totalPages: 0,
  isSearchPanelOpen: true,
  activeTab: 'records' as const,
  sortBy: 'collection_date',
  sortOrder: 'desc' as const,
  activeFilterCount: 0,
};

// Helper to count active filters
const countActiveFilters = (filters: SearchFilters): number => {
  let count = 0;
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === '') continue;
    if (Array.isArray(value) && value.length === 0) continue;
    count++;
  }
  return count;
};

// Helper to build API params from filters
const buildApiParams = (
  query: string,
  filters: SearchFilters,
  page: number,
  pageSize: number
): Record<string, unknown> => {
  const params: Record<string, unknown> = {
    page,
    page_size: pageSize,
  };

  if (query) {
    params.search = query;
  }

  if (filters.taxonGroups && filters.taxonGroups.length > 0) {
    params.taxon_group = filters.taxonGroups.join(',');
  }

  if (filters.yearFrom) {
    params.year_from = filters.yearFrom;
  }

  if (filters.yearTo) {
    params.year_to = filters.yearTo;
  }

  if (filters.iucnCategories && filters.iucnCategories.length > 0) {
    params.iucn_category = filters.iucnCategories.join(',');
  }

  if (filters.endemism && filters.endemism.length > 0) {
    params.endemism = filters.endemism.join(',');
  }

  if (filters.collectors && filters.collectors.length > 0) {
    params.collector = filters.collectors.join(',');
  }

  if (filters.bbox) {
    params.bbox = filters.bbox;
  }

  if (filters.boundaryId) {
    params.boundary = filters.boundaryId;
  }

  if (filters.validated !== undefined) {
    params.validated = filters.validated;
  }

  return params;
};

export const useSearchStore = create<SearchState>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setQuery: (query) => set({ query }),

      setFilter: (key, value) => {
        const filters = { ...get().filters };
        if (value === undefined || value === '' || value === null) {
          delete filters[key];
        } else if (Array.isArray(value) && value.length === 0) {
          delete filters[key];
        } else {
          filters[key] = value as SearchFilters[keyof SearchFilters];
        }

        const activeFilters = Object.keys(filters).filter((k) => {
          const v = filters[k];
          if (v === undefined || v === null || v === '') return false;
          if (Array.isArray(v) && v.length === 0) return false;
          return true;
        });

        set({
          filters,
          activeFilters,
          activeFilterCount: countActiveFilters(filters),
          page: 1,
        });
      },

      setFilters: (newFilters) => {
        const filters = { ...get().filters, ...newFilters };
        const activeFilters = Object.keys(filters).filter((k) => {
          const v = filters[k];
          if (v === undefined || v === null || v === '') return false;
          if (Array.isArray(v) && v.length === 0) return false;
          return true;
        });
        set({
          filters,
          activeFilters,
          activeFilterCount: countActiveFilters(filters),
          page: 1,
        });
      },

      clearFilter: (key) => {
        const filters = { ...get().filters };
        delete filters[key];
        const activeFilters = Object.keys(filters).filter((k) => {
          const v = filters[k];
          if (v === undefined || v === null || v === '') return false;
          if (Array.isArray(v) && v.length === 0) return false;
          return true;
        });
        set({
          filters,
          activeFilters,
          activeFilterCount: countActiveFilters(filters),
          page: 1,
        });
      },

      clearFilters: () =>
        set({
          query: '',
          filters: initialFilters,
          activeFilters: [],
          activeFilterCount: 0,
          page: 1,
        }),

      clearAllFilters: () =>
        set({
          query: '',
          filters: initialFilters,
          activeFilters: [],
          activeFilterCount: 0,
          page: 1,
        }),

      search: async () => {
        const { query, filters, page, pageSize } = get();
        set({ isLoading: true, error: null });

        try {
          const params = buildApiParams(query, filters, page, pageSize);
          const response = await apiClient.get<{
            data: BiologicalRecord[];
            meta: { count: number; total_pages: number };
          }>('records/', { params });

          const data = response.data?.data || [];
          const meta = response.data?.meta || { count: 0, total_pages: 0 };

          set({
            results: data,
            totalCount: meta.count,
            totalPages: meta.total_pages,
            isLoading: false,
          });
        } catch (error) {
          console.error('Search failed:', error);
          set({
            error: error instanceof Error ? error.message : 'Search failed',
            isLoading: false,
          });
        }
      },

      setResults: (results) =>
        set({ fullResults: { ...get().fullResults, ...results } }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      setPage: (page) => set({ page }),

      setPageSize: (pageSize) => set({ pageSize, page: 1 }),

      setTotalPages: (totalPages) => set({ totalPages }),

      toggleSearchPanel: () =>
        set({ isSearchPanelOpen: !get().isSearchPanelOpen }),

      setActiveTab: (tab) => set({ activeTab: tab }),

      setSortBy: (field) => set({ sortBy: field }),

      setSortOrder: (order) => set({ sortOrder: order }),

      reset: () => set(initialState),
    }),
    { name: 'SearchStore' }
  )
);

export default useSearchStore;
