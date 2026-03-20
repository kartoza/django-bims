/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for fetching filter options (boundaries, endemism, collectors, etc.).
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useState, useEffect } from 'react';
import { filterOptionsApi } from '../api/client';

export interface FilterOption {
  id: number | string;
  name: string;
  description?: string;
  [key: string]: unknown;
}

export interface FilterOptions {
  boundaries: FilterOption[];
  collectors: FilterOption[];
  endemism: FilterOption[];
  referenceCategories: FilterOption[];
  dataSources: FilterOption[];
}

export interface UseFilterOptionsResult {
  options: FilterOptions;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

// Cache for filter options to avoid repeated fetches
let cachedOptions: FilterOptions | null = null;
let cachePromise: Promise<FilterOptions> | null = null;

export function useFilterOptions(): UseFilterOptionsResult {
  const [options, setOptions] = useState<FilterOptions>({
    boundaries: [],
    collectors: [],
    endemism: [],
    referenceCategories: [],
    dataSources: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOptions = async (force = false) => {
    // Return cached data if available
    if (cachedOptions && !force) {
      setOptions(cachedOptions);
      setIsLoading(false);
      return;
    }

    // Wait for existing fetch if in progress
    if (cachePromise && !force) {
      try {
        const result = await cachePromise;
        setOptions(result);
        setIsLoading(false);
        return;
      } catch {
        // If cached promise failed, continue to refetch
      }
    }

    setIsLoading(true);
    setError(null);

    // Create fetch promise
    cachePromise = (async () => {
      const [
        boundariesData,
        collectorsData,
        endemismData,
        refCategoriesData,
        dataSourcesData,
      ] = await Promise.all([
        filterOptionsApi.boundaries().catch(() => []),
        filterOptionsApi.collectors().catch(() => []),
        filterOptionsApi.endemism().catch(() => []),
        filterOptionsApi.referenceCategories().catch(() => []),
        filterOptionsApi.dataSources().catch(() => ({})),
      ]);

      // Transform data to consistent format
      const boundaries = (boundariesData || []).map((b: any) => ({
        id: b.id,
        name: b.name || b.code,
        type: b.type,
      }));

      const collectors = (collectorsData || []).map((c: any, idx: number) => ({
        id: idx + 1,
        name: typeof c === 'string' ? c : c.name || c.collector,
      }));

      const endemism = (endemismData || []).map((e: any) => ({
        id: e.id || e.name,
        name: e.name || e.display_name,
      }));

      const referenceCategories = (refCategoriesData || []).map(
        (r: any, idx: number) => ({
          id: idx + 1,
          name: r.category || r.name,
        })
      );

      const dataSources = Object.entries(dataSourcesData || {}).map(
        ([name, description]) => ({
          id: name,
          name: name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' '),
          description: description as string,
        })
      );

      return {
        boundaries,
        collectors,
        endemism,
        referenceCategories,
        dataSources,
      };
    })();

    try {
      const result = await cachePromise;
      cachedOptions = result;
      setOptions(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch filter options';
      setError(errorMessage);
      console.error('Filter options fetch error:', err);
    } finally {
      setIsLoading(false);
      cachePromise = null;
    }
  };

  useEffect(() => {
    fetchOptions();
  }, []);

  return {
    options,
    isLoading,
    error,
    refetch: () => fetchOptions(true),
  };
}

// Individual hooks for specific filter types
export function useBoundaryOptions() {
  const { options, isLoading, error } = useFilterOptions();
  return { boundaries: options.boundaries, isLoading, error };
}

export function useEndemismOptions() {
  const { options, isLoading, error } = useFilterOptions();
  return { endemism: options.endemism, isLoading, error };
}

export function useCollectorOptions() {
  const { options, isLoading, error } = useFilterOptions();
  return { collectors: options.collectors, isLoading, error };
}

export default useFilterOptions;
