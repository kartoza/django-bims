/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Client-side cache for map points using IndexedDB.
 * Stores points locally and only refetches when server cache is invalidated.
 *
 * Made with love by Kartoza | https://kartoza.com
 */

// Site point format: [id, longitude, latitude, record_count]
type SitePoint = [number, number, number, number];

interface CacheEntry {
  key: string;
  version: number;
  timestamp: number;
  points: SitePoint[];
  meta: {
    count: number;
    filtered: boolean;
  };
}

interface CacheMetadata {
  key: string;
  version: number;
  timestamp: number;
}

const DB_NAME = 'bims_map_cache';
const DB_VERSION = 1;
const STORE_NAME = 'map_points';
const META_STORE_NAME = 'cache_meta';
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes local TTL

let dbPromise: Promise<IDBDatabase> | null = null;

/**
 * Initialize IndexedDB database
 */
function initDB(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;

  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      console.error('Failed to open IndexedDB:', request.error);
      reject(request.error);
    };

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      // Create object store for cached points
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'key' });
      }

      // Create object store for cache metadata
      if (!db.objectStoreNames.contains(META_STORE_NAME)) {
        db.createObjectStore(META_STORE_NAME, { keyPath: 'key' });
      }
    };
  });

  return dbPromise;
}

/**
 * Generate a cache key from filter parameters
 */
export function generateCacheKey(params: Record<string, string>): string {
  const sortedParams = Object.keys(params)
    .sort()
    .filter(k => params[k]) // Only include non-empty params
    .map(k => `${k}=${params[k]}`)
    .join('&');

  return sortedParams || '__all__'; // Use __all__ for no filters
}

/**
 * Get cached points from IndexedDB
 */
export async function getCachedPoints(
  cacheKey: string
): Promise<CacheEntry | null> {
  try {
    const db = await initDB();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(cacheKey);

      request.onsuccess = () => {
        const entry = request.result as CacheEntry | undefined;

        if (!entry) {
          resolve(null);
          return;
        }

        // Check if local TTL has expired
        const age = Date.now() - entry.timestamp;
        if (age > CACHE_TTL) {
          // Don't use stale data, but don't delete it yet
          // (server might still have same version)
          resolve(null);
          return;
        }

        resolve(entry);
      };

      request.onerror = () => {
        console.error('Failed to get cached points:', request.error);
        reject(request.error);
      };
    });
  } catch (error) {
    console.error('IndexedDB error:', error);
    return null;
  }
}

/**
 * Store points in IndexedDB cache
 */
export async function setCachedPoints(
  cacheKey: string,
  version: number,
  points: SitePoint[],
  meta: { count: number; filtered: boolean }
): Promise<void> {
  try {
    const db = await initDB();

    const entry: CacheEntry = {
      key: cacheKey,
      version,
      timestamp: Date.now(),
      points,
      meta,
    };

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.put(entry);

      request.onsuccess = () => resolve();
      request.onerror = () => {
        console.error('Failed to cache points:', request.error);
        reject(request.error);
      };
    });
  } catch (error) {
    console.error('IndexedDB error:', error);
  }
}

/**
 * Get cached version for a cache key
 */
export async function getCachedVersion(cacheKey: string): Promise<number | null> {
  try {
    const db = await initDB();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(cacheKey);

      request.onsuccess = () => {
        const entry = request.result as CacheEntry | undefined;
        resolve(entry?.version ?? null);
      };

      request.onerror = () => {
        console.error('Failed to get cached version:', request.error);
        reject(request.error);
      };
    });
  } catch (error) {
    console.error('IndexedDB error:', error);
    return null;
  }
}

/**
 * Clear all cached points
 */
export async function clearCache(): Promise<void> {
  try {
    const db = await initDB();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onsuccess = () => {
        console.log('Map points cache cleared');
        resolve();
      };
      request.onerror = () => {
        console.error('Failed to clear cache:', request.error);
        reject(request.error);
      };
    });
  } catch (error) {
    console.error('IndexedDB error:', error);
  }
}

/**
 * Delete a specific cache entry
 */
export async function deleteCacheEntry(cacheKey: string): Promise<void> {
  try {
    const db = await initDB();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(cacheKey);

      request.onsuccess = () => resolve();
      request.onerror = () => {
        console.error('Failed to delete cache entry:', request.error);
        reject(request.error);
      };
    });
  } catch (error) {
    console.error('IndexedDB error:', error);
  }
}

/**
 * Get cache statistics
 */
export async function getCacheStats(): Promise<{
  entryCount: number;
  totalPoints: number;
  oldestEntry: number | null;
}> {
  try {
    const db = await initDB();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        const entries = request.result as CacheEntry[];
        const totalPoints = entries.reduce((sum, e) => sum + e.points.length, 0);
        const oldestTimestamp = entries.length > 0
          ? Math.min(...entries.map(e => e.timestamp))
          : null;

        resolve({
          entryCount: entries.length,
          totalPoints,
          oldestEntry: oldestTimestamp,
        });
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  } catch (error) {
    console.error('IndexedDB error:', error);
    return { entryCount: 0, totalPoints: 0, oldestEntry: null };
  }
}

export default {
  generateCacheKey,
  getCachedPoints,
  setCachedPoints,
  getCachedVersion,
  clearCache,
  deleteCacheEntry,
  getCacheStats,
};
