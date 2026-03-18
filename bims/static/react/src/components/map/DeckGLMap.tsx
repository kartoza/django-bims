/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * deck.gl map component for rendering site points.
 * Supports 2D scatter plot and 3D column extrusion based on record count.
 * Uses minimal data (UUID + coordinates + count) to prevent data exfiltration.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, {
  useRef,
  useEffect,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from 'react';
import { Box } from '@chakra-ui/react';
import maplibregl, { Map as MapLibreMap, NavigationControl, ScaleControl } from 'maplibre-gl';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { ScatterplotLayer, ColumnLayer } from '@deck.gl/layers';
import 'maplibre-gl/dist/maplibre-gl.css';

import { bimsMapStyle, switchBasemap } from '../../styles/mapStyle';

// Site point data format: [id, longitude, latitude, record_count]
type SitePoint = [number, number, number, number];

export interface DeckGLMapProps {
  initialCenter?: [number, number];
  initialZoom?: number;
  is3D?: boolean;
  onSiteSelect?: (siteId: number | null) => void;
  onSiteHover?: (siteId: number | null) => void;
  onBoundsChange?: (bounds: [number, number, number, number]) => void;
  onMapReady?: (map: MapLibreMap) => void;
}

export interface DeckGLMapRef {
  flyTo: (center: [number, number], zoom?: number) => void;
  setPoints: (points: SitePoint[]) => void;
  getMap: () => MapLibreMap | null;
  highlightSite: (siteId: number | null) => void;
  getBounds: () => [number, number, number, number] | null;
  switchBasemap: (sourceId: string) => void;
  setIs3D: (is3D: boolean) => void;
}

const DeckGLMap = forwardRef<DeckGLMapRef, DeckGLMapProps>(
  (
    {
      initialCenter = [24.5, -29.0], // Default: South Africa
      initialZoom = 5,
      is3D: initialIs3D = false,
      onSiteSelect,
      onSiteHover,
      onBoundsChange,
      onMapReady,
    },
    ref
  ) => {
    const mapContainer = useRef<HTMLDivElement>(null);
    const mapRef = useRef<MapLibreMap | null>(null);
    const deckOverlayRef = useRef<MapboxOverlay | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const [points, setPoints] = useState<SitePoint[]>([]);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [hoveredId, setHoveredId] = useState<number | null>(null);
    const [is3D, setIs3D] = useState(initialIs3D);
    const [zoomLevel, setZoomLevel] = useState(initialZoom);

    // Calculate max record count for scaling extrusion
    const maxRecordCount = points.reduce((max, p) => Math.max(max, p[3] || 1), 1);

    // Calculate dynamic radius based on zoom level
    // At zoom 5 (country level): small dots, at zoom 15 (street level): larger dots
    const getZoomBasedRadius = useCallback(() => {
      const minRadius = 4;
      const maxRadius = 20;
      // Scale from minRadius at zoom 2 to maxRadius at zoom 18
      const scale = Math.min(1, Math.max(0, (zoomLevel - 2) / 16));
      return minRadius + (maxRadius - minRadius) * scale;
    }, [zoomLevel]);

    // Update deck.gl layers when points or selection changes
    const updateLayers = useCallback(() => {
      if (!deckOverlayRef.current) return;

      const commonProps = {
        data: points,
        pickable: true,
        onClick: (info: { object?: SitePoint }) => {
          if (info.object) {
            const siteId = info.object[0];
            setSelectedId(siteId);
            if (onSiteSelect) {
              onSiteSelect(siteId);
            }
          } else {
            setSelectedId(null);
            if (onSiteSelect) {
              onSiteSelect(null);
            }
          }
        },
        onHover: (info: { object?: SitePoint }) => {
          const siteId = info.object ? info.object[0] : null;
          setHoveredId(siteId);
          if (onSiteHover) {
            onSiteHover(siteId);
          }
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = info.object ? 'pointer' : '';
          }
        },
        updateTriggers: {
          getElevation: [selectedId, hoveredId],
          getFillColor: [selectedId, hoveredId],
          getRadius: [selectedId, hoveredId, zoomLevel],
        },
        // Larger picking radius for easier clicking on small dots
        pickingRadius: 10,
      };

      let layers;

      if (is3D) {
        // 3D Column Layer - extrude based on record count
        layers = [
          new ColumnLayer<SitePoint>({
            id: 'sites-3d-layer',
            ...commonProps,
            diskResolution: 12,
            radius: 3000, // meters - thick columns for visibility
            extruded: true,
            elevationScale: 100,
            getPosition: (d: SitePoint) => [d[1], d[2]],
            getElevation: (d: SitePoint) => {
              const count = d[3] || 1;
              // Scale elevation logarithmically for better visualization
              return Math.log10(count + 1) * 1000;
            },
            getFillColor: (d: SitePoint) => {
              if (d[0] === selectedId) return [255, 153, 0, 255]; // Orange
              if (d[0] === hoveredId) return [0, 150, 255, 255]; // Light blue
              // Color based on record count (blue to red gradient)
              const ratio = Math.min((d[3] || 1) / maxRecordCount, 1);
              return [
                Math.floor(50 + ratio * 200), // R: 50 -> 250
                Math.floor(150 - ratio * 100), // G: 150 -> 50
                Math.floor(230 - ratio * 180), // B: 230 -> 50
                220,
              ];
            },
            material: {
              ambient: 0.4,
              diffuse: 0.6,
              shininess: 32,
              specularColor: [60, 64, 70],
            },
          }),
        ];
      } else {
        // 2D Scatter Plot Layer
        const dynamicMinRadius = getZoomBasedRadius();
        layers = [
          new ScatterplotLayer<SitePoint>({
            id: 'sites-layer',
            ...commonProps,
            opacity: 0.8,
            stroked: true,
            filled: true,
            radiusScale: 1,
            radiusMinPixels: dynamicMinRadius,
            radiusMaxPixels: 50,
            lineWidthMinPixels: 1,
            getPosition: (d: SitePoint) => [d[1], d[2]],
            getRadius: (d: SitePoint) => {
              // Base radius scales with record count
              const baseRadius = Math.sqrt(d[3] || 1) * 3 + dynamicMinRadius;
              if (d[0] === selectedId) return baseRadius + 8;
              if (d[0] === hoveredId) return baseRadius + 5;
              return baseRadius;
            },
            getFillColor: (d: SitePoint) => {
              if (d[0] === selectedId) return [255, 153, 0, 255]; // Orange
              if (d[0] === hoveredId) return [0, 150, 255, 255]; // Light blue
              // Color based on record count
              const ratio = Math.min((d[3] || 1) / maxRecordCount, 1);
              return [
                Math.floor(50 + ratio * 200),
                Math.floor(150 - ratio * 100),
                Math.floor(230 - ratio * 180),
                200,
              ];
            },
            getLineColor: [255, 255, 255, 255],
            getLineWidth: 2,
          }),
        ];
      }

      deckOverlayRef.current.setProps({ layers });
    }, [points, selectedId, hoveredId, is3D, maxRecordCount, onSiteSelect, onSiteHover, getZoomBasedRadius, zoomLevel]);

    // Update layers when dependencies change
    // Include isLoaded to ensure layers update when deck overlay becomes ready
    useEffect(() => {
      if (isLoaded) {
        updateLayers();
      }
    }, [updateLayers, isLoaded]);

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

      setPoints: (newPoints: SitePoint[]) => {
        setPoints(newPoints);
      },

      getMap: () => mapRef.current,

      highlightSite: (siteId: number | null) => {
        setSelectedId(siteId);
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

      switchBasemap: (sourceId: string) => {
        if (mapRef.current && isLoaded) {
          switchBasemap(mapRef.current, sourceId);
        }
      },

      setIs3D: (newIs3D: boolean) => {
        setIs3D(newIs3D);
        // Enable/disable map pitch for 3D view
        if (mapRef.current) {
          if (newIs3D) {
            mapRef.current.easeTo({ pitch: 60, bearing: -20, duration: 1000 });
          } else {
            mapRef.current.easeTo({ pitch: 0, bearing: 0, duration: 1000 });
          }
        }
      },
    }));

    // Initialize map
    useEffect(() => {
      if (mapRef.current || !mapContainer.current) return;

      const container = mapContainer.current;
      const rect = container.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) {
        return;
      }

      // Check WebGL support
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) {
        console.error('DeckGLMap: WebGL is not supported');
        return;
      }

      const map = new MapLibreMap({
        container,
        style: bimsMapStyle,
        center: initialCenter,
        zoom: initialZoom,
        minZoom: 2,
        maxZoom: 18,
        pitch: is3D ? 60 : 0,
        bearing: is3D ? -20 : 0,
        attributionControl: true,
      });

      // Add navigation control
      map.addControl(
        new NavigationControl({ visualizePitch: true }),
        'top-right'
      );

      // Add scale control
      map.addControl(new ScaleControl({ maxWidth: 200 }), 'bottom-left');

      // Create deck.gl overlay
      const deckOverlay = new MapboxOverlay({
        layers: [],
        interleaved: true,
      });

      map.on('load', () => {
        mapRef.current = map;
        deckOverlayRef.current = deckOverlay;

        // Add deck.gl overlay to map
        map.addControl(deckOverlay as unknown as maplibregl.IControl);

        setIsLoaded(true);

        if (onMapReady) {
          onMapReady(map);
        }
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

      // Track zoom changes for dynamic radius scaling
      map.on('zoom', () => {
        setZoomLevel(map.getZoom());
      });

      map.on('error', (e) => {
        console.error('Map error:', e);
      });

      // Cleanup
      return () => {
        if (deckOverlayRef.current) {
          deckOverlayRef.current.finalize();
          deckOverlayRef.current = null;
        }
        if (mapRef.current) {
          mapRef.current.remove();
          mapRef.current = null;
          setIsLoaded(false);
        }
      };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Only initialize once on mount

    return (
      <Box
        ref={mapContainer}
        position="absolute"
        top={0}
        left={0}
        right={0}
        bottom={0}
        bg="gray.200"
        sx={{
          '.maplibregl-map': {
            width: '100%',
            height: '100%',
          },
          '.maplibregl-canvas': {
            outline: 'none',
          },
        }}
      />
    );
  }
);

DeckGLMap.displayName = 'DeckGLMap';

export default DeckGLMap;
