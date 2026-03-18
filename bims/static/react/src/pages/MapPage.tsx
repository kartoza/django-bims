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
import { SiteDetailPanel } from '../components/panels/SiteDetailPanel';
import { TaxonDetailPanel } from '../components/panels/TaxonDetailPanel';
import { apiClient } from '../api/client';
import type { BiologicalRecord } from '../types';
import { Map as MapLibreMap } from 'maplibre-gl';

// Site point format from API: [uuid, longitude, latitude, record_count]
type SitePoint = [string, number, number, number];

const MapPage: React.FC = () => {
  const mapRef = useRef<DeckGLMapRef>(null);
  const { siteId, taxonId } = useParams<{ siteId?: string; taxonId?: string }>();
  const [searchParams] = useSearchParams();
  const toast = useToast();
  const { activePanel, setActivePanel, is3DMap } = useUIStore();
  const filters = useSearchStore((state) => state.filters);

  // Local state
  const [isLoading, setIsLoading] = useState(false);
  const [isMapReady, setIsMapReady] = useState(false);
  const [selectedSiteUuid, setSelectedSiteUuid] = useState<string | null>(null);
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null);
  const [selectedTaxonId, setSelectedTaxonId] = useState<number | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [currentBounds, setCurrentBounds] = useState<
    [number, number, number, number] | null
  >(null);

  // Get taxon group from search store filters
  const taxonGroupFilter = filters.taxonGroups?.[0] || searchParams.get('taxon_group');

  // Handle map ready
  const handleMapReady = useCallback((map: MapLibreMap) => {
    setIsMapReady(true);
  }, []);

  // Handle site selection from map (receives UUID)
  const handleSiteSelect = useCallback(async (uuid: string | null) => {
    setSelectedSiteUuid(uuid);
    setSelectedTaxonId(null); // Clear taxon when site is selected

    if (uuid) {
      setIsSearchOpen(false); // Close search when viewing site detail
      // Look up the site ID from UUID
      try {
        const response = await apiClient.get<{
          data: { id: number };
        }>(`sites/`, {
          params: { uuid: uuid, page_size: 1 },
        });
        const sites = response.data?.data;
        if (Array.isArray(sites) && sites.length > 0) {
          setSelectedSiteId(sites[0].id);
        }
      } catch (error) {
        console.error('Failed to look up site:', error);
      }
    } else {
      setSelectedSiteId(null);
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
  useEffect(() => {
    if (!isMapReady || !mapRef.current) return;

    const loadSitePoints = async () => {
      setIsLoading(true);
      try {
        const params: Record<string, string> = {};
        if (taxonGroupFilter) {
          params.taxon_group = String(taxonGroupFilter);
        }

        const response = await apiClient.get<{
          data: SitePoint[];
          meta: { count: number };
        }>('sites/map-points/', { params });

        const points = response.data?.data || [];
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
  }, [isMapReady, taxonGroupFilter, toast]);

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
    setSelectedSiteUuid(null);
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
          onFlyTo={(coords, zoom) => mapRef.current?.flyTo(coords, zoom)}
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
