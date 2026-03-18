/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Main map page component.
 * Uses MapContainer directly without external stores.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Box, Spinner, Center, useToast, IconButton } from '@chakra-ui/react';
import { useParams } from 'react-router-dom';
import { SearchIcon } from '@chakra-ui/icons';
import MapContainer, { MapContainerRef } from '../components/map/MapContainer';
import MapControls from '../components/map/MapControls';
import MapLegend from '../components/map/MapLegend';
import { SearchPanel } from '../components/search';
import { useUIStore } from '../stores/uiStore';
import { SiteDetailPanel } from '../components/panels/SiteDetailPanel';
import { TaxonDetailPanel } from '../components/panels/TaxonDetailPanel';
import { apiClient } from '../api/client';
import type { BiologicalRecord } from '../types';
import { Map as MapLibreMap } from 'maplibre-gl';

interface SiteFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number];
  };
  properties: {
    id: number;
    name: string;
    site_code?: string;
    ecosystem_type?: string;
    record_count?: number;
  };
}

const MapPage: React.FC = () => {
  const mapRef = useRef<MapContainerRef>(null);
  const { siteId, taxonId } = useParams<{ siteId?: string; taxonId?: string }>();
  const toast = useToast();
  const { activePanel, setActivePanel } = useUIStore();

  // Local state
  const [isLoading, setIsLoading] = useState(false);
  const [isMapReady, setIsMapReady] = useState(false);
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null);
  const [selectedTaxonId, setSelectedTaxonId] = useState<number | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [currentBounds, setCurrentBounds] = useState<
    [number, number, number, number] | null
  >(null);

  // Handle map ready
  const handleMapReady = useCallback((map: MapLibreMap) => {
    setIsMapReady(true);
  }, []);

  // Handle site selection from map
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

      // If record has a site, select it
      // Note: We'd need to get the site ID from the record
      // For now, just close the search panel
      setIsSearchOpen(false);
    },
    []
  );

  // Load sites data when map is ready
  useEffect(() => {
    if (!isMapReady || !mapRef.current) return;

    const loadSites = async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.get<{
          data: Array<{
            id: number;
            name: string;
            site_code: string;
            ecosystem_type?: string;
            geometry?: string;
          }>;
        }>('sites/', {
          params: { page_size: 1000 },
        });

        const sites = response.data?.data || [];

        // Convert to GeoJSON
        const features: SiteFeature[] = sites
          .filter((site) => site.geometry)
          .map((site) => {
            // Parse geometry from WKT or GeoJSON
            let coordinates: [number, number] = [0, 0];
            if (site.geometry) {
              try {
                // Assume geometry is GeoJSON or extract from WKT
                if (site.geometry.startsWith('{')) {
                  const geom = JSON.parse(site.geometry);
                  coordinates = geom.coordinates;
                } else if (site.geometry.includes('POINT')) {
                  // Parse WKT POINT(lon lat)
                  const match = site.geometry.match(
                    /POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)/
                  );
                  if (match) {
                    coordinates = [parseFloat(match[1]), parseFloat(match[2])];
                  }
                }
              } catch (e) {
                console.error('Failed to parse geometry:', e);
              }
            }

            return {
              type: 'Feature' as const,
              geometry: {
                type: 'Point' as const,
                coordinates,
              },
              properties: {
                id: site.id,
                name: site.name,
                site_code: site.site_code,
                ecosystem_type: site.ecosystem_type,
              },
            };
          })
          .filter((f) => f.geometry.coordinates[0] !== 0);

        mapRef.current?.setData({
          type: 'FeatureCollection',
          features,
        });
      } catch (error) {
        console.error('Failed to load sites:', error);
        toast({
          title: 'Error loading sites',
          description: 'Failed to load location sites from the server.',
          status: 'error',
          duration: 5000,
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadSites();
  }, [isMapReady, toast]);

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

  return (
    <Box position="absolute" top={0} left={0} right={0} bottom={0}>
      {/* Map container */}
      <MapContainer
        ref={mapRef}
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
