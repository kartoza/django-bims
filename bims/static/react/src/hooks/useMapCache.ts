/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for managing map points cache.
 * Provides methods to clear cache, get stats, and invalidate entries.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useState, useCallback } from 'react';
import { useToast } from '@chakra-ui/react';
import { apiClient } from '../api/client';
import {
  clearCache,
  getCacheStats,
  deleteCacheEntry,
} from '../utils/mapPointsCache';

interface CacheStats {
  entryCount: number;
  totalPoints: number;
  oldestEntry: number | null;
  serverVersion: number | null;
}

export function useMapCache() {
  const toast = useToast();
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Refresh cache statistics
   */
  const refreshStats = useCallback(async () => {
    setIsLoading(true);
    try {
      const localStats = await getCacheStats();

      // Get server version
      let serverVersion: number | null = null;
      try {
        const response = await apiClient.get<{
          data: { version: number };
        }>('sites/map-cache-version/');
        serverVersion = response.data?.data?.version || null;
      } catch {
        // Ignore version fetch errors
      }

      setStats({
        ...localStats,
        serverVersion,
      });
    } catch (error) {
      console.error('Failed to get cache stats:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Clear all cached map points (client-side only)
   */
  const clearLocalCache = useCallback(async () => {
    setIsLoading(true);
    try {
      await clearCache();
      await refreshStats();
      toast({
        title: 'Cache cleared',
        description: 'Local map points cache has been cleared.',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      console.error('Failed to clear cache:', error);
      toast({
        title: 'Error',
        description: 'Failed to clear local cache.',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsLoading(false);
    }
  }, [refreshStats, toast]);

  /**
   * Invalidate server cache (requires staff permissions)
   * This increments the server cache version, causing all clients to refetch
   */
  const invalidateServerCache = useCallback(async () => {
    setIsLoading(true);
    try {
      await apiClient.post('sites/clear-map-cache/');

      // Also clear local cache since server version changed
      await clearCache();
      await refreshStats();

      toast({
        title: 'Server cache invalidated',
        description: 'All clients will refetch map points on next load.',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      console.error('Failed to invalidate server cache:', error);
      toast({
        title: 'Error',
        description: 'Failed to invalidate server cache. Staff permissions required.',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsLoading(false);
    }
  }, [refreshStats, toast]);

  /**
   * Delete a specific cache entry by key
   */
  const deleteCacheKey = useCallback(
    async (cacheKey: string) => {
      try {
        await deleteCacheEntry(cacheKey);
        await refreshStats();
        toast({
          title: 'Cache entry deleted',
          status: 'success',
          duration: 2000,
        });
      } catch (error) {
        console.error('Failed to delete cache entry:', error);
      }
    },
    [refreshStats, toast]
  );

  return {
    stats,
    isLoading,
    refreshStats,
    clearLocalCache,
    invalidateServerCache,
    deleteCacheKey,
  };
}

export default useMapCache;
