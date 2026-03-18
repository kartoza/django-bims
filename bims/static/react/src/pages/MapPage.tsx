/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Main map page component.
 * Uses deck.gl for efficient rendering of site points with minimal data exposure.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Box, Spinner, Center, useToast, IconButton } from '@chakra-ui/react';
import { useParams, useSearchParams } from 'react-router-dom';
import { SearchIcon } from '@chakra-ui/icons';
import DeckGLMap, { DeckGLMapRef } from '../components/map/DeckGLMap';
import MapControls from '../components/map/MapControls';
import MapLegend from '../components/map/MapLegend';
import { SearchPanel } from '../components/search';
import { useUIStore } from '../stores/uiStore';
import { useSearchStore } from '../stores/searchStore';
import { useMap } from '../providers/MapProvider';
import { SiteDetailPanel } from '../components/panels/SiteDetailPanel';
import { TaxonDetailPanel } from '../components/panels/TaxonDetailPanel';
import { apiClient } from '../api/client';
import type { BiologicalRecord } from '../types';
import { Map as MapLibreMap } from 'maplibre-gl';
import {
  generateCacheKey,
  getCachedPoints,
  setCachedPoints,
} from '../utils/mapPointsCache';

// Site point format from API: [id, longitude, latitude, record_count]
type SitePoint = [number, number, number, number];

const MapPage: React.FC = () => {
  const mapRef = useRef<DeckGLMapRef>(null);
  const { siteId, taxonId } = useParams<{ siteId?: string; taxonId?: string }>();
  const [searchParams] = useSearchParams();
  const toast = useToast();
  const { activePanel, setActivePanel, is3DMap } = useUIStore();
  const filters = useSearchStore((state) => state.filters);
  const filterVersion = useSearchStore((state) => state.filterVersion);
  const { setMap } = useMap();

  // Local state
  const [isLoading, setIsLoading] = useState(false);
  const [isMapReady, setIsMapReady] = useState(false);
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null);
  const [selectedTaxonId, setSelectedTaxonId] = useState<number | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [currentBounds, setCurrentBounds] = useState<
    [number, number, number, number] | null
  >(null);

  // Handle map ready - register with MapProvider context
  const handleMapReady = useCallback((map: MapLibreMap) => {
    setIsMapReady(true);
    setMap(map); // Register with MapProvider for MapControls
  }, [setMap]);

  // Handle site selection from map (receives site ID directly)
  const handleSiteSelect = useCallback((siteId: number | null) => {
    setSelectedSiteId(siteId);
    setSelectedTaxonId(null); // Clear taxon when site is selected

    if (siteId) {
      setIsSearchOpen(false); // Close search when viewing site detail
    }
  }, []);

  // Handle bounds change
  const handleBoundsChange = useCallback(
    (bounds: [number, number, number, number]) => {
      setCurrentBounds(bounds);
    },
    []
  );

  // Handle record selection from search results
  const handleRecordSelect = useCallback(
    (record: BiologicalRecord) => {
      // Fly to record location
      if (record.latitude && record.longitude) {
        mapRef.current?.flyTo([record.longitude, record.latitude], 14);
      } else if (record.coordinates) {
        mapRef.current?.flyTo(
          [record.coordinates.longitude, record.coordinates.latitude],
          14
        );
      }
      setIsSearchOpen(false);
    },
    []
  );

  // Load minimal site points when map is ready or filters change
  // Uses client-side IndexedDB cache with server version validation
  useEffect(() => {
    if (!isMapReady || !mapRef.current) return;

    const loadSitePoints = async () => {
      setIsLoading(true);
      try {
        // Build params from all active filters
        const params: Record<string, string> = {};

        // Taxon group filter
        const taxonGroupFilter = filters.taxonGroups?.[0] || searchParams.get('taxon_group');
        if (taxonGroupFilter) {
          params.taxon_group = String(taxonGroupFilter);
        }

        // Date range filters
        if (filters.yearFrom) {
          params.year_from = String(filters.yearFrom);
        }
        if (filters.yearTo) {
          params.year_to = String(filters.yearTo);
        }

        // IUCN category filter
        if (filters.iucnCategories && filters.iucnCategories.length > 0) {
          params.iucn_category = filters.iucnCategories.join(',');
        }

        // Endemism filter
        if (filters.endemism && filters.endemism.length > 0) {
          params.endemism = filters.endemism.join(',');
        }

        // Collector filter
        if (filters.collectors && filters.collectors.length > 0) {
          params.collector = filters.collectors.join(',');
        }

        // Validation status filter
        if (filters.validated !== undefined) {
          params.validated = String(filters.validated);
        }

        // Search text filter
        if (filters.search) {
          params.search = filters.search;
        }

        // Boundary filter
        if (filters.boundaryId) {
          params.boundary = String(filters.boundaryId);
        }

        // Bounding box filter
        if (filters.bbox) {
          params.bbox = filters.bbox;
        }

        // Generate cache key from params
        const cacheKey = generateCacheKey(params);

        // Try to get cached data
        const cachedEntry = await getCachedPoints(cacheKey);

        if (cachedEntry) {
          // Check if server cache version matches
          try {
            const versionResponse = await apiClient.get<{
              data: { version: number };
            }>('sites/map-cache-version/');
            const serverVersion = versionResponse.data?.data?.version || 1;

            if (cachedEntry.version === serverVersion) {
              // Cache is valid, use cached data
              console.log(`Using cached points (${cachedEntry.points.length} points, version ${serverVersion})`);
              mapRef.current?.setPoints(cachedEntry.points);
              setIsLoading(false);
              return;
            } else {
              console.log(`Cache invalidated (local: ${cachedEntry.version}, server: ${serverVersion})`);
            }
          } catch (versionError) {
            // If version check fails, use cached data anyway
            console.warn('Failed to check cache version, using cached data');
            mapRef.current?.setPoints(cachedEntry.points);
            setIsLoading(false);
            return;
          }
        }

        // Fetch fresh data from server
        const response = await apiClient.get<{
          data: SitePoint[];
          meta: { count: number; filtered: boolean; cache_key?: string };
        }>('sites/map-points/', { params });

        const points = response.data?.data || [];
        const meta = response.data?.meta || { count: 0, filtered: false };

        // Get server cache version for storing
        let serverVersion = 1;
        try {
          const versionResponse = await apiClient.get<{
            data: { version: number };
          }>('sites/map-cache-version/');
          serverVersion = versionResponse.data?.data?.version || 1;
        } catch {
          // Use default version if check fails
        }

        // Cache the fresh data
        await setCachedPoints(cacheKey, serverVersion, points, {
          count: meta.count,
          filtered: meta.filtered,
        });

        console.log(`Cached ${points.length} points (version ${serverVersion})`);
        mapRef.current?.setPoints(points);
      } catch (error) {
        console.error('Failed to load site points:', error);
        toast({
          title: 'Error loading sites',
          description: 'Failed to load site points from the server.',
          status: 'error',
          duration: 5000,
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadSitePoints();
  }, [isMapReady, filters, filterVersion, searchParams, toast]);

  // Handle 3D toggle
  useEffect(() => {
    if (isMapReady && mapRef.current) {
      mapRef.current.setIs3D(is3DMap);
    }
  }, [is3DMap, isMapReady]);

  // Handle URL parameters for deep linking
  useEffect(() => {
    if (siteId) {
      const id = parseInt(siteId, 10);
      if (!isNaN(id)) {
        setSelectedSiteId(id);
        setIsSearchOpen(false);
      }
    } else if (taxonId) {
      const id = parseInt(taxonId, 10);
      if (!isNaN(id)) {
        setSelectedTaxonId(id);
        setIsSearchOpen(false);
      }
    }
  }, [siteId, taxonId]);

  // Close detail panel
  const handleCloseDetail = useCallback(() => {
    setSelectedSiteId(null);
    setSelectedTaxonId(null);
    mapRef.current?.highlightSite(null);
  }, []);

  // Handle taxon selection from taxon detail panel
  const handleTaxonSelect = useCallback((taxonId: number) => {
    setSelectedTaxonId(taxonId);
  }, []);

  // Toggle search panel
  const toggleSearch = useCallback(() => {
    setIsSearchOpen((prev) => !prev);
  }, []);

  // Handle fly to location (memoized to prevent re-renders)
  const handleFlyTo = useCallback((coords: [number, number], zoom?: number) => {
    mapRef.current?.flyTo(coords, zoom);
  }, []);

  return (
    <Box w="100%" h="100%" position="relative">
      {/* deck.gl Map */}
      <DeckGLMap
        ref={mapRef}
        is3D={is3DMap}
        onSiteSelect={handleSiteSelect}
        onBoundsChange={handleBoundsChange}
        onMapReady={handleMapReady}
      />

      {/* Map controls */}
      <MapControls />

      {/* Map Legend */}
      <MapLegend
        isOpen={activePanel === 'legend'}
        onClose={() => setActivePanel(null)}
      />

      {/* Search toggle button (when search is closed) */}
      {!isSearchOpen && !selectedSiteId && !selectedTaxonId && (
        <IconButton
          aria-label="Open search"
          icon={<SearchIcon />}
          position="absolute"
          left={4}
          top={4}
          zIndex={1000}
          colorScheme="blue"
          onClick={toggleSearch}
          boxShadow="lg"
        />
      )}

      {/* Search Panel */}
      <SearchPanel
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onRecordSelect={handleRecordSelect}
      />

      {/* Site Detail Panel */}
      {selectedSiteId && (
        <SiteDetailPanel
          siteId={selectedSiteId}
          onClose={handleCloseDetail}
          onFlyTo={handleFlyTo}
        />
      )}

      {/* Taxon Detail Panel */}
      {selectedTaxonId && (
        <TaxonDetailPanel
          taxonId={selectedTaxonId}
          onClose={handleCloseDetail}
          onTaxonSelect={handleTaxonSelect}
        />
      )}

      {/* Loading overlay */}
      {isLoading && (
        <Center
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="whiteAlpha.700"
          zIndex={15}
        >
          <Spinner size="xl" color="blue.500" thickness="4px" />
        </Center>
      )}
    </Box>
  );
};

export default MapPage;
