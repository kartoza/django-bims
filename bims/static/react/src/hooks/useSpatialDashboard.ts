/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for fetching spatial dashboard data - handles async polling for long-running queries.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  spatialDashboardApi,
  SpatialDashboardResponse,
  SpatialSummaryData,
  ConservationStatusData,
  RLIData,
} from '../api/client';

type DashboardDataType = 'summary' | 'conservationStatus' | 'rli' | 'map';

interface UseSpatialDashboardOptions {
  type: DashboardDataType;
  filters?: Record<string, unknown>;
  enabled?: boolean;
  pollInterval?: number;
}

interface UseSpatialDashboardResult<T> {
  data: T | null;
  isLoading: boolean;
  isPolling: boolean;
  error: string | null;
  refetch: () => void;
}

// Helper to poll for task completion
const pollForResult = async (
  taskId: string,
  maxAttempts = 60,
  interval = 2000
): Promise<any> => {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const result = await spatialDashboardApi.checkTaskStatus(taskId);

    if (result.status === 'SUCCESS') {
      return result.result;
    } else if (result.status === 'FAILURE' || result.status === 'REVOKED') {
      throw new Error(result.result?.error || 'Task failed');
    }

    // Wait before next poll
    await new Promise((resolve) => setTimeout(resolve, interval));
    attempts++;
  }

  throw new Error('Polling timeout');
};

export function useSpatialDashboard<T = any>(
  options: UseSpatialDashboardOptions
): UseSpatialDashboardResult<T> {
  const { type, filters, enabled = true, pollInterval = 2000 } = options;

  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    if (!enabled) return;

    // Cancel any in-flight request
    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    setIsLoading(true);
    setError(null);

    try {
      let response: SpatialDashboardResponse;

      switch (type) {
        case 'summary':
          response = await spatialDashboardApi.summary(filters);
          break;
        case 'conservationStatus':
          response = await spatialDashboardApi.conservationStatus(filters);
          break;
        case 'rli':
          response = await spatialDashboardApi.rli(filters);
          break;
        case 'map':
          response = await spatialDashboardApi.map(filters);
          break;
        default:
          throw new Error(`Unknown dashboard type: ${type}`);
      }

      // Check if response is still processing
      if (response.status === 'processing' && response.task_id) {
        setIsPolling(true);
        try {
          const result = await pollForResult(response.task_id, 60, pollInterval);
          if (isMountedRef.current) {
            setData(result as T);
          }
        } catch (pollError) {
          if (isMountedRef.current) {
            setError(
              pollError instanceof Error ? pollError.message : 'Polling failed'
            );
          }
        } finally {
          if (isMountedRef.current) {
            setIsPolling(false);
          }
        }
      } else if (response.data) {
        // Direct result
        setData(response.data as T);
      } else {
        // Response itself is the data (for map endpoint)
        setData(response as unknown as T);
      }
    } catch (err) {
      if (isMountedRef.current && (err as Error).name !== 'AbortError') {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        console.error(`Spatial dashboard ${type} error:`, err);
      }
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [type, filters, enabled, pollInterval]);

  useEffect(() => {
    isMountedRef.current = true;
    fetchData();

    return () => {
      isMountedRef.current = false;
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [fetchData]);

  return {
    data,
    isLoading,
    isPolling,
    error,
    refetch: fetchData,
  };
}

// Convenience hooks for specific dashboard data types
export function useSpatialSummary(
  filters?: Record<string, unknown>,
  enabled = true
): UseSpatialDashboardResult<SpatialSummaryData> {
  return useSpatialDashboard<SpatialSummaryData>({
    type: 'summary',
    filters,
    enabled,
  });
}

export function useConservationStatus(
  filters?: Record<string, unknown>,
  enabled = true
): UseSpatialDashboardResult<ConservationStatusData> {
  return useSpatialDashboard<ConservationStatusData>({
    type: 'conservationStatus',
    filters,
    enabled,
  });
}

export function useRLI(
  filters?: Record<string, unknown>,
  enabled = true
): UseSpatialDashboardResult<RLIData> {
  return useSpatialDashboard<RLIData>({
    type: 'rli',
    filters,
    enabled,
  });
}

export interface SpatialMapData {
  extent?: [number, number, number, number];
  sites_raw_query?: string;
}

export function useSpatialMap(
  filters?: Record<string, unknown>,
  enabled = true
): UseSpatialDashboardResult<SpatialMapData> {
  return useSpatialDashboard<SpatialMapData>({
    type: 'map',
    filters,
    enabled,
  });
}

export default useSpatialDashboard;
