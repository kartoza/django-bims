/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for managing downloads - request, track status, and list downloads.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  downloadsApi,
  DownloadRequest,
  DownloadRequestPurpose,
  DownloadTaskStatus,
} from '../api/client';

export interface UseDownloadsResult {
  downloads: DownloadRequest[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useDownloads(): UseDownloadsResult {
  const [downloads, setDownloads] = useState<DownloadRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDownloads = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await downloadsApi.list();
      setDownloads(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch downloads');
      console.error('Failed to fetch downloads:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDownloads();
  }, [fetchDownloads]);

  return {
    downloads,
    isLoading,
    error,
    refetch: fetchDownloads,
  };
}

export interface UseDownloadPurposesResult {
  purposes: DownloadRequestPurpose[];
  isLoading: boolean;
  error: string | null;
}

export function useDownloadPurposes(): UseDownloadPurposesResult {
  const [purposes, setPurposes] = useState<DownloadRequestPurpose[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPurposes = async () => {
      try {
        const data = await downloadsApi.purposes();
        setPurposes(data);
      } catch (err) {
        // Purpose endpoint may not exist, use fallback
        setPurposes([
          { id: 1, name: 'Research', description: 'Academic or scientific research' },
          { id: 2, name: 'Conservation', description: 'Conservation planning' },
          { id: 3, name: 'Education', description: 'Educational purposes' },
          { id: 4, name: 'Government', description: 'Government reporting' },
          { id: 5, name: 'Other', description: 'Other purposes' },
        ]);
        console.log('Using fallback download purposes');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPurposes();
  }, []);

  return { purposes, isLoading, error };
}

export interface UseDownloadTaskResult {
  status: DownloadTaskStatus | null;
  isPolling: boolean;
  error: string | null;
  startPolling: (taskId: string) => void;
  stopPolling: () => void;
}

export function useDownloadTask(): UseDownloadTaskResult {
  const [status, setStatus] = useState<DownloadTaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const checkStatus = useCallback(async (taskId: string) => {
    try {
      const data = await downloadsApi.status(taskId);
      setStatus(data);

      // Stop polling if task is complete
      if (data.ready || data.status === 'SUCCESS' || data.status === 'FAILURE' || data.status === 'REVOKED') {
        stopPolling();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check download status');
      stopPolling();
    }
  }, [stopPolling]);

  const startPolling = useCallback((taskId: string) => {
    setIsPolling(true);
    setError(null);
    setStatus(null);

    // Check immediately
    checkStatus(taskId);

    // Then poll every 3 seconds
    intervalRef.current = setInterval(() => {
      checkStatus(taskId);
    }, 3000);
  }, [checkStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    status,
    isPolling,
    error,
    startPolling,
    stopPolling,
  };
}

export interface RequestDownloadOptions {
  type: 'csv' | 'checklist';
  filters?: Record<string, unknown>;
  taxonGroupId?: number;
  boundaryId?: number;
}

export interface UseDownloadRequestResult {
  requestDownload: (options: RequestDownloadOptions) => Promise<string | null>;
  isRequesting: boolean;
  error: string | null;
  taskId: string | null;
  taskStatus: DownloadTaskStatus | null;
  isPolling: boolean;
}

export function useDownloadRequest(): UseDownloadRequestResult {
  const [isRequesting, setIsRequesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const { status: taskStatus, isPolling, startPolling } = useDownloadTask();

  const requestDownload = useCallback(async (options: RequestDownloadOptions): Promise<string | null> => {
    setIsRequesting(true);
    setError(null);
    setTaskId(null);

    try {
      let response;

      if (options.type === 'csv') {
        response = await downloadsApi.csv(options.filters);
      } else if (options.type === 'checklist') {
        if (!options.taxonGroupId) {
          throw new Error('Taxon group ID is required for checklist download');
        }
        response = await downloadsApi.checklist(options.taxonGroupId, options.boundaryId);
      } else {
        throw new Error('Invalid download type');
      }

      const newTaskId = response?.task_id;
      if (newTaskId) {
        setTaskId(newTaskId);
        startPolling(newTaskId);
      }

      return newTaskId || null;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Download request failed';
      setError(errorMessage);
      return null;
    } finally {
      setIsRequesting(false);
    }
  }, [startPolling]);

  return {
    requestDownload,
    isRequesting,
    error,
    taskId,
    taskStatus,
    isPolling,
  };
}

export default useDownloads;
