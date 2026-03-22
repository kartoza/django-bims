/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Main map page component.
 * Uses deck.gl for efficient rendering of site points with minimal data exposure.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { Box, Spinner, Center, useToast, IconButton } from '@chakra-ui/react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { SearchIcon } from '@chakra-ui/icons';
import DeckGLMap, { DeckGLMapRef } from '../components/map/DeckGLMap';
import MapControls from '../components/map/MapControls';
import MapLegend from '../components/map/MapLegend';
import { SearchPanel } from '../components/search';
import { useUIStore } from '../stores/uiStore';
import { useSearchStore } from '../stores/searchStore';
import { useMapStore } from '../stores/mapStore';
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
import { useContextLayers } from '../hooks/useContextLayers';
import { useContextLayersRenderer } from '../hooks/useContextLayersRenderer';
import { useDashboardSettingsStore } from '../stores/dashboardSettingsStore';

// Site point format from API: [id, longitude, latitude, record_count]
type SitePoint = [number, number, number, number];

// Minimum zoom level to start loading viewport-specific data
const VIEWPORT_LOAD_ZOOM = 8;
// Debounce delay for viewport changes (ms)
const VIEWPORT_DEBOUNCE_MS = 500;

// Debounce delay for URL updates (ms)
const URL_UPDATE_DEBOUNCE_MS = 300;

const MapPage: React.FC = () => {
  console.log('[MapPage] Rendering, pathname:', window.location.pathname);
  const mapRef = useRef<DeckGLMapRef>(null);
  const { siteId, taxonId } = useParams<{ siteId?: string; taxonId?: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { activePanel, setActivePanel, is3DMap } = useUIStore();
  // Use getState() to avoid re-renders when filters object reference changes
  const filterVersion = useSearchStore((state) => state.filterVersion);
  const getFilters = useSearchStore((state) => state.getFilterParams);
  const { setMap } = useMap();

  // Get map store actions for initializing from URL
  const { setLayerVisibility, setBasemapStyle } = useMapStore();
  const { set3DMap } = useUIStore();

  // Get map settings from dashboard settings store
  const { mapSettings } = useDashboardSettingsStore();

  // Parse initial map state from URL (use dashboard settings as defaults)
  const initialPosition = useMemo(() => {
    const lat = parseFloat(searchParams.get('lat') || String(mapSettings.defaultLatitude));
    const lng = parseFloat(searchParams.get('lng') || String(mapSettings.defaultLongitude));
    const zoom = parseFloat(searchParams.get('z') || String(mapSettings.defaultZoom));
    return {
      center: [lng, lat] as [number, number],
      zoom: isNaN(zoom) ? mapSettings.defaultZoom : zoom,
    };
  }, [mapSettings.defaultLatitude, mapSettings.defaultLongitude, mapSettings.defaultZoom]); // Recompute when defaults change

  // Get search store actions for initializing from URL
  const setSearchQuery = useSearchStore((state) => state.setQuery);
  const setSearchFilters = useSearchStore((state) => state.setFilters);

  // Initialize settings from URL on mount
  useEffect(() => {
    // Parse layers from URL (comma-separated list of visible layers)
    const layersParam = searchParams.get('layers');
    if (layersParam) {
      // First, turn off all visualization layers
      const allVizLayers = ['sites', 'clusters', 'heatmap'];
      allVizLayers.forEach(layer => setLayerVisibility(layer, false));

      // Then enable only the ones in the URL
      const visibleLayers = layersParam.split(',').filter(Boolean);
      visibleLayers.forEach(layer => setLayerVisibility(layer, true));
    }

    // Parse basemap from URL
    const basemapParam = searchParams.get('basemap');
    if (basemapParam && ['streets', 'satellite', 'terrain', 'light', 'dark'].includes(basemapParam)) {
      setBasemapStyle(basemapParam as 'streets' | 'satellite' | 'terrain' | 'light' | 'dark');
    }

    // Parse 3D mode from URL
    const is3DParam = searchParams.get('3d');
    if (is3DParam === 'true' || is3DParam === '1') {
      set3DMap(true);
    } else if (is3DParam === 'false' || is3DParam === '0') {
      set3DMap(false);
    }

    // Parse search query from URL
    const queryParam = searchParams.get('q');
    if (queryParam) {
      setSearchQuery(queryParam);
    }

    // Parse filters from URL
    const urlFilters: Record<string, unknown> = {};

    const taxonGroupParam = searchParams.get('taxon_group');
    if (taxonGroupParam) {
      urlFilters.taxonGroups = taxonGroupParam.split(',').filter(Boolean);
    }

    const yearFromParam = searchParams.get('year_from');
    if (yearFromParam) {
      urlFilters.yearFrom = parseInt(yearFromParam, 10);
    }

    const yearToParam = searchParams.get('year_to');
    if (yearToParam) {
      urlFilters.yearTo = parseInt(yearToParam, 10);
    }

    const iucnParam = searchParams.get('iucn');
    if (iucnParam) {
      urlFilters.iucnCategories = iucnParam.split(',').filter(Boolean);
    }

    const endemismParam = searchParams.get('endemism');
    if (endemismParam) {
      urlFilters.endemism = endemismParam.split(',').filter(Boolean);
    }

    const refCatParam = searchParams.get('ref_cat');
    if (refCatParam) {
      urlFilters.referenceCategories = refCatParam.split(',').filter(Boolean);
    }

    const sourceParam = searchParams.get('source');
    if (sourceParam) {
      urlFilters.sourceCollections = sourceParam.split(',').filter(Boolean);
    }

    const boundaryParam = searchParams.get('boundary');
    if (boundaryParam) {
      urlFilters.boundaryId = parseInt(boundaryParam, 10);
    }

    if (Object.keys(urlFilters).length > 0) {
      setSearchFilters(urlFilters);
    }

    // Mark URL initialization as complete after a short delay
    // This prevents the filter-to-URL sync from running immediately
    setTimeout(() => {
      isInitializingFromUrl.current = false;
    }, 500);
  }, []); // Only run on mount

  // Local state
  const [isLoading, setIsLoading] = useState(false);
  const [isMapReady, setIsMapReady] = useState(false);
  const [mapInstance, setMapInstance] = useState<MapLibreMap | null>(null);
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(() => {
    // Initialize from URL if present
    const site = searchParams.get('site');
    return site ? parseInt(site, 10) : null;
  });
  const [selectedTaxonId, setSelectedTaxonId] = useState<number | null>(() => {
    // Initialize from URL if present
    const taxon = searchParams.get('taxon');
    return taxon ? parseInt(taxon, 10) : null;
  });
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [currentBounds, setCurrentBounds] = useState<
    [number, number, number, number] | null
  >(null);
  const [currentZoom, setCurrentZoom] = useState(initialPosition.zoom);
  const [currentCenter, setCurrentCenter] = useState<[number, number]>(initialPosition.center);
  const [globalPoints, setGlobalPoints] = useState<SitePoint[]>([]);
  const [viewportPoints, setViewportPoints] = useState<SitePoint[]>([]);
  const viewportLoadTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const loadedBoundsRef = useRef<string | null>(null);
  const urlUpdateTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isInitialMount = useRef(true);
  const isInitializingFromUrl = useRef(true);
  const isUnmounting = useRef(false);

  // Load and manage WMS context layers from API (NonBiodiversityLayer model)
  useContextLayers({ map: mapInstance, enabled: isMapReady });

  // Render context layers from the store (ContextLayersPage)
  useContextLayersRenderer({ map: mapInstance, enabled: isMapReady });

  // Update URL when map state changes (debounced)
  const updateUrl = useCallback((params: {
    lat?: number;
    lng?: number;
    z?: number;
    site?: number | null;
    taxon?: number | null;
    layers?: string[];
    basemap?: string;
    is3D?: boolean;
    query?: string | null;
    filters?: {
      taxonGroups?: string[];
      yearFrom?: number;
      yearTo?: number;
      iucnCategories?: string[];
      endemism?: string[];
      referenceCategories?: string[];
      sourceCollections?: string[];
      boundaryId?: number;
    };
  }) => {
    // Skip URL updates during initial mount
    if (isInitialMount.current) return;

    // Debounce URL updates
    if (urlUpdateTimeoutRef.current) {
      clearTimeout(urlUpdateTimeoutRef.current);
    }

    urlUpdateTimeoutRef.current = setTimeout(() => {
      // Skip if component is unmounting to prevent navigation interference
      if (isUnmounting.current) {
        console.log('[MapPage] Skipping URL update - component unmounting');
        return;
      }

      // Skip if we've navigated away from the map page
      if (!window.location.pathname.includes('/map')) {
        console.log('[MapPage] Skipping URL update - no longer on map page');
        return;
      }

      const newParams = new URLSearchParams(searchParams);

      // Update map position params
      if (params.lat !== undefined && params.lng !== undefined) {
        newParams.set('lat', params.lat.toFixed(4));
        newParams.set('lng', params.lng.toFixed(4));
      }
      if (params.z !== undefined) {
        newParams.set('z', params.z.toFixed(1));
      }

      // Update selection params
      if (params.site !== undefined) {
        if (params.site === null) {
          newParams.delete('site');
        } else {
          newParams.set('site', String(params.site));
        }
      }
      if (params.taxon !== undefined) {
        if (params.taxon === null) {
          newParams.delete('taxon');
        } else {
          newParams.set('taxon', String(params.taxon));
        }
      }

      // Update layer visibility (comma-separated list)
      if (params.layers !== undefined) {
        if (params.layers.length > 0) {
          newParams.set('layers', params.layers.join(','));
        } else {
          newParams.delete('layers');
        }
      }

      // Update basemap style
      if (params.basemap !== undefined) {
        if (params.basemap === 'streets') {
          // Default, remove from URL
          newParams.delete('basemap');
        } else {
          newParams.set('basemap', params.basemap);
        }
      }

      // Update 3D mode
      if (params.is3D !== undefined) {
        if (params.is3D) {
          newParams.set('3d', '1');
        } else {
          newParams.delete('3d');
        }
      }

      // Update search query
      if (params.query !== undefined) {
        if (params.query === null || params.query === '') {
          newParams.delete('q');
        } else {
          newParams.set('q', params.query);
        }
      }

      // Update search filters
      if (params.filters !== undefined) {
        // Serialize common filters to URL
        const filters = params.filters;

        // Taxon group
        if (filters.taxonGroups && filters.taxonGroups.length > 0) {
          newParams.set('taxon_group', filters.taxonGroups.join(','));
        } else {
          newParams.delete('taxon_group');
        }

        // Year range
        if (filters.yearFrom) {
          newParams.set('year_from', String(filters.yearFrom));
        } else {
          newParams.delete('year_from');
        }
        if (filters.yearTo) {
          newParams.set('year_to', String(filters.yearTo));
        } else {
          newParams.delete('year_to');
        }

        // IUCN categories
        if (filters.iucnCategories && filters.iucnCategories.length > 0) {
          newParams.set('iucn', filters.iucnCategories.join(','));
        } else {
          newParams.delete('iucn');
        }

        // Endemism
        if (filters.endemism && filters.endemism.length > 0) {
          newParams.set('endemism', filters.endemism.join(','));
        } else {
          newParams.delete('endemism');
        }

        // Reference categories
        if (filters.referenceCategories && filters.referenceCategories.length > 0) {
          newParams.set('ref_cat', filters.referenceCategories.join(','));
        } else {
          newParams.delete('ref_cat');
        }

        // Source collections
        if (filters.sourceCollections && filters.sourceCollections.length > 0) {
          newParams.set('source', filters.sourceCollections.join(','));
        } else {
          newParams.delete('source');
        }

        // Boundary ID
        if (filters.boundaryId) {
          newParams.set('boundary', String(filters.boundaryId));
        } else {
          newParams.delete('boundary');
        }
      }

      // Use replaceState to avoid creating history entries for every move
      setSearchParams(newParams, { replace: true });
    }, URL_UPDATE_DEBOUNCE_MS);
  }, [searchParams, setSearchParams]);

  // Cleanup URL update timeout on unmount and set unmounting flag
  useEffect(() => {
    return () => {
      console.log('[MapPage] Unmounting, canceling pending URL updates');
      isUnmounting.current = true;
      if (urlUpdateTimeoutRef.current) {
        clearTimeout(urlUpdateTimeoutRef.current);
        urlUpdateTimeoutRef.current = null;
      }
    };
  }, []);

  // Mark initial mount as complete after first render
  useEffect(() => {
    // Delay to allow initial map position to be set
    const timer = setTimeout(() => {
      isInitialMount.current = false;
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  // Sync layer visibility to URL
  const visibleLayerIds = useMapStore((state) => state.visibleLayerIds);
  useEffect(() => {
    if (isInitialMount.current) return;
    // Only include visualization layers in URL (not context layers which have dynamic IDs)
    const vizLayers = ['sites', 'clusters', 'heatmap'];
    const activeVizLayers = visibleLayerIds.filter(id => vizLayers.includes(id));
    updateUrl({ layers: activeVizLayers });
  }, [visibleLayerIds, updateUrl]);

  // Sync basemap to URL
  const basemapStyle = useMapStore((state) => state.basemapStyle);
  useEffect(() => {
    if (isInitialMount.current) return;
    updateUrl({ basemap: basemapStyle });
  }, [basemapStyle, updateUrl]);

  // Sync 3D mode to URL
  useEffect(() => {
    if (isInitialMount.current) return;
    updateUrl({ is3D: is3DMap });
  }, [is3DMap, updateUrl]);

  // Sync search query to URL
  const searchQuery = useSearchStore((state) => state.query);
  useEffect(() => {
    if (isInitialMount.current) return;
    updateUrl({ query: searchQuery || null });
  }, [searchQuery, updateUrl]);

  // Sync search filters to URL - use filterVersion to track actual changes
  // and avoid re-running when object reference changes
  const filterVersionForUrl = useSearchStore((state) => state.filterVersion);
  useEffect(() => {
    // Skip during initial mount and URL initialization
    if (isInitialMount.current || isInitializingFromUrl.current) return;
    // Get current filters from store
    const currentFilters = useSearchStore.getState().filters;
    updateUrl({
      filters: {
        taxonGroups: currentFilters.taxonGroups,
        yearFrom: currentFilters.yearFrom,
        yearTo: currentFilters.yearTo,
        iucnCategories: currentFilters.iucnCategories,
        endemism: currentFilters.endemism,
        referenceCategories: currentFilters.referenceCategories,
        sourceCollections: currentFilters.sourceCollections,
        boundaryId: currentFilters.boundaryId,
      },
    });
  }, [filterVersionForUrl, updateUrl]);

  // Handle map ready - register with MapProvider context
  const handleMapReady = useCallback((map: MapLibreMap) => {
    setIsMapReady(true);
    setMapInstance(map); // Store map instance for context layers
    setMap(map); // Register with MapProvider for MapControls
  }, [setMap]);

  // Handle site selection from map (receives site ID directly)
  const handleSiteSelect = useCallback((siteId: number | null) => {
    setSelectedSiteId(siteId);
    setSelectedTaxonId(null); // Clear taxon when site is selected

    if (siteId) {
      setIsSearchOpen(false); // Close search when viewing site detail
    }

    // Update URL with selected site
    updateUrl({ site: siteId });
  }, [updateUrl]);

  // Handle bounds change with zoom
  const handleBoundsChange = useCallback(
    (bounds: [number, number, number, number], zoom?: number) => {
      setCurrentBounds(bounds);

      // Calculate center from bounds [west, south, east, north]
      const centerLng = (bounds[0] + bounds[2]) / 2;
      const centerLat = (bounds[1] + bounds[3]) / 2;
      setCurrentCenter([centerLng, centerLat]);

      if (zoom !== undefined) {
        setCurrentZoom(zoom);
      }

      // Update URL with new position
      updateUrl({
        lat: centerLat,
        lng: centerLng,
        z: zoom,
      });
    },
    [updateUrl]
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
        // Get filter params from store (this doesn't cause re-renders)
        const filterParams = getFilters();

        // Build params for map points API
        const params: Record<string, string> = {};

        // Add URL search params
        const taxonGroupFromUrl = searchParams.get('taxon_group');
        if (taxonGroupFromUrl) {
          params.taxon_group = taxonGroupFromUrl;
        }

        // Copy relevant filter params (convert to strings for API)
        for (const [key, value] of Object.entries(filterParams)) {
          if (value !== undefined && value !== null && value !== '' && key !== 'page' && key !== 'page_size') {
            params[key] = String(value);
          }
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
              setGlobalPoints(cachedEntry.points);
              mapRef.current?.setPoints(cachedEntry.points);
              setIsLoading(false);
              return;
            } else {
              console.log(`Cache invalidated (local: ${cachedEntry.version}, server: ${serverVersion})`);
            }
          } catch (versionError) {
            // If version check fails, use cached data anyway
            console.warn('Failed to check cache version, using cached data');
            setGlobalPoints(cachedEntry.points);
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
        setGlobalPoints(points);
        mapRef.current?.setPoints(points);
      } catch (error) {
        console.error('Failed to load site points:', error);
        const errorMessage = error instanceof Error ? error.message : String(error);
        toast({
          title: 'Error loading sites',
          description: `Failed to load site points: ${errorMessage}`,
          status: 'error',
          duration: 8000,
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadSitePoints();
    // Note: filterVersion changes when filters change, so we don't need filters in deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMapReady, filterVersion, searchParams, toast, getFilters]);

  // Load viewport-specific points when zoomed in
  useEffect(() => {
    if (!isMapReady || !mapRef.current || !currentBounds) return;
    if (currentZoom < VIEWPORT_LOAD_ZOOM) {
      // Not zoomed in enough, just use global points
      if (viewportPoints.length > 0) {
        setViewportPoints([]);
        mapRef.current?.setPoints(globalPoints);
      }
      return;
    }

    // Debounce viewport loading
    if (viewportLoadTimeoutRef.current) {
      clearTimeout(viewportLoadTimeoutRef.current);
    }

    const boundsKey = currentBounds.map(b => b.toFixed(4)).join(',');

    // Skip if we already loaded this exact bounds
    if (loadedBoundsRef.current === boundsKey) {
      return;
    }

    viewportLoadTimeoutRef.current = setTimeout(async () => {
      try {
        const filterParams = getFilters();
        const params: Record<string, string> = {
          bbox: currentBounds.join(','),
          limit: '0', // No limit when using bbox
        };

        // Add filters
        const taxonGroupFromUrl = searchParams.get('taxon_group');
        if (taxonGroupFromUrl) {
          params.taxon_group = taxonGroupFromUrl;
        }
        for (const [key, value] of Object.entries(filterParams)) {
          if (value !== undefined && value !== null && value !== '' && key !== 'page' && key !== 'page_size') {
            params[key] = String(value);
          }
        }

        console.log(`Loading viewport points at zoom ${currentZoom.toFixed(1)}...`);
        const response = await apiClient.get<{
          data: SitePoint[];
          meta: { count: number };
        }>('sites/map-points/', { params });

        const points = response.data?.data || [];
        console.log(`Loaded ${points.length} viewport points`);

        loadedBoundsRef.current = boundsKey;
        setViewportPoints(points);

        // Merge with global points (viewport points take precedence)
        const viewportIds = new Set(points.map(p => p[0]));
        const mergedPoints = [
          ...points,
          ...globalPoints.filter(p => !viewportIds.has(p[0])),
        ];
        mapRef.current?.setPoints(mergedPoints);
      } catch (error) {
        console.error('Failed to load viewport points:', error);
      }
    }, VIEWPORT_DEBOUNCE_MS);

    return () => {
      if (viewportLoadTimeoutRef.current) {
        clearTimeout(viewportLoadTimeoutRef.current);
      }
    };
  }, [isMapReady, currentBounds, currentZoom, globalPoints, getFilters, searchParams, viewportPoints.length]);

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
    // Clear URL params
    updateUrl({ site: null, taxon: null });
  }, [updateUrl]);

  // Handle taxon selection from taxon detail panel
  const handleTaxonSelect = useCallback((taxonId: number) => {
    setSelectedTaxonId(taxonId);
    // Update URL with selected taxon
    updateUrl({ taxon: taxonId });
  }, [updateUrl]);

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
        initialCenter={initialPosition.center}
        initialZoom={initialPosition.zoom}
        is3D={is3DMap}
        showScaleBar={mapSettings.showScaleBar}
        showMiniMap={mapSettings.showMiniMap}
        enableClustering={mapSettings.enableClustering}
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
