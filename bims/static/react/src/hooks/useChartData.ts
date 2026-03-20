/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for fetching chart data for dashboards and detail panels.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useState, useEffect, useCallback } from 'react';
import { chartsApi, ChartData } from '../api/client';

export interface ChartDataSet {
  endemism: ChartData | null;
  conservation: ChartData | null;
  taxa: ChartData | null;
  occurrences: ChartData | null;
  totalOccurrences: ChartData | null;
}

export interface UseChartDataOptions {
  siteId?: number;
  filters?: Record<string, unknown>;
  enabled?: boolean;
}

export interface UseChartDataResult {
  data: ChartDataSet;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useChartData({
  siteId,
  filters = {},
  enabled = true,
}: UseChartDataOptions): UseChartDataResult {
  const [data, setData] = useState<ChartDataSet>({
    endemism: null,
    conservation: null,
    taxa: null,
    occurrences: null,
    totalOccurrences: null,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!enabled) return;

    setIsLoading(true);
    setError(null);

    // Build filter params
    const params: Record<string, unknown> = { ...filters };
    if (siteId) {
      params.siteId = String(siteId);
    }

    try {
      // Fetch all chart data in parallel
      const [endemism, conservation, taxa, occurrences, totalOccurrences] =
        await Promise.all([
          chartsApi.endemism(params).catch(() => null),
          chartsApi.conservation(params).catch(() => null),
          chartsApi.taxa(params).catch(() => null),
          chartsApi.occurrences(params).catch(() => null),
          chartsApi.totalOccurrences(params).catch(() => null),
        ]);

      setData({
        endemism,
        conservation,
        taxa,
        occurrences,
        totalOccurrences,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch chart data';
      setError(errorMessage);
      console.error('Chart data fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [siteId, filters, enabled]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
  };
}

// Hook for a single chart type
export function useSingleChartData(
  chartType: keyof typeof chartsApi,
  filters?: Record<string, unknown>,
  enabled: boolean = true
) {
  const [data, setData] = useState<ChartData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const chartFn = chartsApi[chartType];
        if (typeof chartFn === 'function') {
          const result = await chartFn(filters);
          setData(result);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to fetch chart data';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [chartType, filters, enabled]);

  return { data, isLoading, error };
}

export default useChartData;
