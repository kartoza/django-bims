/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * MapLibre GL map container component.
 * Implements map functionality directly with React state.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, {
  useRef,
  useEffect,
  useCallback,
  useState,
  forwardRef,
  useImperativeHandle,
} from 'react';
import { Box } from '@chakra-ui/react';
import maplibregl, {
  Map as MapLibreMap,
  NavigationControl,
  ScaleControl,
  GeolocateControl,
  LngLatBoundsLike,
} from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// Default map style - using a free tile provider
const DEFAULT_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  name: 'BIMS Base Map',
  sources: {
    'osm-tiles': {
      type: 'raster',
      tiles: [
        'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
      ],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  layers: [
    {
      id: 'osm-tiles-layer',
      type: 'raster',
      source: 'osm-tiles',
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

// GeoJSON Feature type for sites
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

interface SiteFeatureCollection {
  type: 'FeatureCollection';
  features: SiteFeature[];
}

// Props for the MapContainer
export interface MapContainerProps {
  initialCenter?: [number, number];
  initialZoom?: number;
  onSiteSelect?: (siteId: number | null) => void;
  onSiteHover?: (siteId: number | null) => void;
  onBoundsChange?: (bounds: [number, number, number, number]) => void;
  onMapReady?: (map: MapLibreMap) => void;
}

// Ref methods exposed by MapContainer
export interface MapContainerRef {
  flyTo: (center: [number, number], zoom?: number) => void;
  fitBounds: (bounds: LngLatBoundsLike, padding?: number) => void;
  setData: (data: SiteFeatureCollection) => void;
  getMap: () => MapLibreMap | null;
  highlightSite: (siteId: number | null) => void;
  getBounds: () => [number, number, number, number] | null;
}

const MapContainer = forwardRef<MapContainerRef, MapContainerProps>(
  (
    {
      initialCenter = [24.5, -29.0], // Default: South Africa
      initialZoom = 5,
      onSiteSelect,
      onSiteHover,
      onBoundsChange,
      onMapReady,
    },
    ref
  ) => {
    const mapContainer = useRef<HTMLDivElement>(null);
    const mapRef = useRef<MapLibreMap | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null);

    // Expose methods via ref
    useImperativeHandle(ref, () => ({
      flyTo: (center: [number, number], zoom?: number) => {
        if (mapRef.current) {
          mapRef.current.flyTo({
            center,
            zoom: zoom ?? mapRef.current.getZoom(),
            duration: 1500,
          });
        }
      },

      fitBounds: (bounds: LngLatBoundsLike, padding = 50) => {
        if (mapRef.current) {
          mapRef.current.fitBounds(bounds, { padding });
        }
      },

      setData: (data: SiteFeatureCollection) => {
        if (mapRef.current && isLoaded) {
          const source = mapRef.current.getSource('sites');
          if (source && 'setData' in source) {
            (source as maplibregl.GeoJSONSource).setData(data);
          }
        }
      },

      getMap: () => mapRef.current,

      highlightSite: (siteId: number | null) => {
        if (mapRef.current && isLoaded) {
          setSelectedSiteId(siteId);
          mapRef.current.setFilter('highlighted-point', [
            '==',
            ['get', 'id'],
            siteId ?? '',
          ]);
        }
      },

      getBounds: () => {
        if (mapRef.current) {
          const bounds = mapRef.current.getBounds();
          return [
            bounds.getWest(),
            bounds.getSouth(),
            bounds.getEast(),
            bounds.getNorth(),
          ];
        }
        return null;
      },
    }));

    // Initialize map
    useEffect(() => {
      if (mapRef.current || !mapContainer.current) return;

      const map = new MapLibreMap({
        container: mapContainer.current,
        style: DEFAULT_STYLE,
        center: initialCenter,
        zoom: initialZoom,
        minZoom: 2,
        maxZoom: 18,
        attributionControl: true,
      });

      // Add navigation control
      map.addControl(
        new NavigationControl({
          visualizePitch: true,
        }),
        'top-right'
      );

      // Add scale control
      map.addControl(new ScaleControl({ maxWidth: 200 }), 'bottom-left');

      // Add geolocation control
      map.addControl(
        new GeolocateControl({
          positionOptions: {
            enableHighAccuracy: true,
          },
          trackUserLocation: true,
        }),
        'top-right'
      );

      // Map load event
      map.on('load', () => {
        mapRef.current = map;
        setIsLoaded(true);

        // Add placeholder source for sites
        map.addSource('sites', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [],
          },
          cluster: true,
          clusterMaxZoom: 14,
          clusterRadius: 50,
        });

        // Add clustered points layer
        map.addLayer({
          id: 'clusters',
          type: 'circle',
          source: 'sites',
          filter: ['has', 'point_count'],
          paint: {
            'circle-color': [
              'step',
              ['get', 'point_count'],
              '#51bbd6',
              10,
              '#f1f075',
              50,
              '#f28cb1',
            ],
            'circle-radius': [
              'step',
              ['get', 'point_count'],
              15,
              10,
              20,
              50,
              25,
            ],
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff',
          },
        });

        // Add cluster count labels
        map.addLayer({
          id: 'cluster-count',
          type: 'symbol',
          source: 'sites',
          filter: ['has', 'point_count'],
          layout: {
            'text-field': '{point_count_abbreviated}',
            'text-font': ['Open Sans Semibold'],
            'text-size': 12,
          },
          paint: {
            'text-color': '#333333',
          },
        });

        // Add unclustered point layer
        map.addLayer({
          id: 'unclustered-point',
          type: 'circle',
          source: 'sites',
          filter: ['!', ['has', 'point_count']],
          paint: {
            'circle-color': '#0073e6',
            'circle-radius': 8,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff',
          },
        });

        // Add highlighted point layer
        map.addLayer({
          id: 'highlighted-point',
          type: 'circle',
          source: 'sites',
          filter: ['==', ['get', 'id'], ''],
          paint: {
            'circle-color': '#ff9900',
            'circle-radius': 12,
            'circle-stroke-width': 3,
            'circle-stroke-color': '#ffffff',
          },
        });

        // Notify parent that map is ready
        if (onMapReady) {
          onMapReady(map);
        }
      });

      // Handle cluster click - zoom in
      map.on('click', 'clusters', (e) => {
        const features = map.queryRenderedFeatures(e.point, {
          layers: ['clusters'],
        });
        const clusterId = features[0]?.properties?.cluster_id;

        if (clusterId === undefined) return;

        const source = map.getSource('sites');
        if (source && 'getClusterExpansionZoom' in source) {
          (source as maplibregl.GeoJSONSource).getClusterExpansionZoom(
            clusterId,
            (err: Error | null, zoom: number | null | undefined) => {
              if (err || zoom === null || zoom === undefined) return;

              const coordinates = (features[0].geometry as GeoJSON.Point)
                .coordinates;
              map.easeTo({
                center: coordinates as [number, number],
                zoom: zoom,
              });
            }
          );
        }
      });

      // Handle point click - select site
      map.on('click', 'unclustered-point', (e) => {
        const features = e.features;
        if (!features || features.length === 0) return;

        const feature = features[0];
        const siteId = feature.properties?.id;

        if (siteId) {
          const parsedId = parseInt(siteId, 10);
          setSelectedSiteId(parsedId);

          // Update highlight filter
          map.setFilter('highlighted-point', ['==', ['get', 'id'], siteId]);

          // Notify parent
          if (onSiteSelect) {
            onSiteSelect(parsedId);
          }
        }
      });

      // Handle click on empty area - deselect
      map.on('click', (e) => {
        const features = map.queryRenderedFeatures(e.point, {
          layers: ['unclustered-point', 'clusters'],
        });
        if (features.length === 0) {
          setSelectedSiteId(null);
          map.setFilter('highlighted-point', ['==', ['get', 'id'], '']);
          if (onSiteSelect) {
            onSiteSelect(null);
          }
        }
      });

      // Handle hover effects
      map.on('mouseenter', 'unclustered-point', (e) => {
        map.getCanvas().style.cursor = 'pointer';
        const features = e.features;
        if (features && features.length > 0 && onSiteHover) {
          const siteId = features[0].properties?.id;
          if (siteId) {
            onSiteHover(parseInt(siteId, 10));
          }
        }
      });

      map.on('mouseleave', 'unclustered-point', () => {
        map.getCanvas().style.cursor = '';
        if (onSiteHover) {
          onSiteHover(null);
        }
      });

      map.on('mouseenter', 'clusters', () => {
        map.getCanvas().style.cursor = 'pointer';
      });

      map.on('mouseleave', 'clusters', () => {
        map.getCanvas().style.cursor = '';
      });

      // Track map movement
      map.on('moveend', () => {
        if (onBoundsChange) {
          const bounds = map.getBounds();
          onBoundsChange([
            bounds.getWest(),
            bounds.getSouth(),
            bounds.getEast(),
            bounds.getNorth(),
          ]);
        }
      });

      // Cleanup on unmount
      return () => {
        if (mapRef.current) {
          mapRef.current.remove();
          mapRef.current = null;
          setIsLoaded(false);
        }
      };
    }, []); // Only run once on mount

    return (
      <Box
        ref={mapContainer}
        position="absolute"
        top={0}
        left={0}
        right={0}
        bottom={0}
        bg="gray.100"
      />
    );
  }
);

MapContainer.displayName = 'MapContainer';

export default MapContainer;
