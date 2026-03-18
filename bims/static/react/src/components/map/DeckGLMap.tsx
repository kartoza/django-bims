/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * deck.gl map component for rendering site points.
 * Uses minimal data (UUID + coordinates only) to prevent data exfiltration.
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
import { ScatterplotLayer } from '@deck.gl/layers';
import 'maplibre-gl/dist/maplibre-gl.css';

import { bimsMapStyle, switchBasemap } from '../../styles/mapStyle';

// Site point data format: [uuid, longitude, latitude]
type SitePoint = [string, number, number];

export interface DeckGLMapProps {
  initialCenter?: [number, number];
  initialZoom?: number;
  onSiteSelect?: (uuid: string | null) => void;
  onSiteHover?: (uuid: string | null) => void;
  onBoundsChange?: (bounds: [number, number, number, number]) => void;
  onMapReady?: (map: MapLibreMap) => void;
}

export interface DeckGLMapRef {
  flyTo: (center: [number, number], zoom?: number) => void;
  setPoints: (points: SitePoint[]) => void;
  getMap: () => MapLibreMap | null;
  highlightSite: (uuid: string | null) => void;
  getBounds: () => [number, number, number, number] | null;
  switchBasemap: (sourceId: string) => void;
}

const DeckGLMap = forwardRef<DeckGLMapRef, DeckGLMapProps>(
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
    const deckOverlayRef = useRef<MapboxOverlay | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const [points, setPoints] = useState<SitePoint[]>([]);
    const [selectedUuid, setSelectedUuid] = useState<string | null>(null);
    const [hoveredUuid, setHoveredUuid] = useState<string | null>(null);

    // Update deck.gl layers when points or selection changes
    const updateLayers = useCallback(() => {
      if (!deckOverlayRef.current) return;

      const layers = [
        new ScatterplotLayer<SitePoint>({
          id: 'sites-layer',
          data: points,
          pickable: true,
          opacity: 0.8,
          stroked: true,
          filled: true,
          radiusScale: 1,
          radiusMinPixels: 5,
          radiusMaxPixels: 20,
          lineWidthMinPixels: 1,
          getPosition: (d: SitePoint) => [d[1], d[2]],
          getRadius: (d: SitePoint) => {
            if (d[0] === selectedUuid) return 12;
            if (d[0] === hoveredUuid) return 10;
            return 6;
          },
          getFillColor: (d: SitePoint) => {
            if (d[0] === selectedUuid) return [255, 153, 0, 255]; // Orange for selected
            if (d[0] === hoveredUuid) return [0, 150, 255, 255]; // Light blue for hovered
            return [0, 115, 230, 200]; // Blue for normal
          },
          getLineColor: [255, 255, 255, 255],
          getLineWidth: 2,
          onClick: (info) => {
            if (info.object) {
              const uuid = info.object[0];
              setSelectedUuid(uuid);
              if (onSiteSelect) {
                onSiteSelect(uuid);
              }
            } else {
              setSelectedUuid(null);
              if (onSiteSelect) {
                onSiteSelect(null);
              }
            }
          },
          onHover: (info) => {
            const uuid = info.object ? info.object[0] : null;
            setHoveredUuid(uuid);
            if (onSiteHover) {
              onSiteHover(uuid);
            }
            // Update cursor
            if (mapRef.current) {
              mapRef.current.getCanvas().style.cursor = info.object ? 'pointer' : '';
            }
          },
          updateTriggers: {
            getRadius: [selectedUuid, hoveredUuid],
            getFillColor: [selectedUuid, hoveredUuid],
          },
        }),
      ];

      deckOverlayRef.current.setProps({ layers });
    }, [points, selectedUuid, hoveredUuid, onSiteSelect, onSiteHover]);

    // Update layers when dependencies change
    useEffect(() => {
      updateLayers();
    }, [updateLayers]);

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

      highlightSite: (uuid: string | null) => {
        setSelectedUuid(uuid);
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
    }));

    // Initialize map
    useEffect(() => {
      if (mapRef.current || !mapContainer.current) return;

      const container = mapContainer.current;
      const rect = container.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) {
        // Container not ready, will retry
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

        // Notify parent
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

      // Handle click on empty area
      map.on('click', (e) => {
        // This is handled by deck.gl layer onClick
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
    }, [initialCenter, initialZoom, onBoundsChange, onMapReady]);

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
