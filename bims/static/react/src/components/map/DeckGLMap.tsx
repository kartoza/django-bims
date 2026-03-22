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
import { useVisualizationLayersStore } from '../../stores/visualizationLayersStore';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { ScatterplotLayer, ColumnLayer } from '@deck.gl/layers';
import { HeatmapLayer, HexagonLayer, GridLayer } from '@deck.gl/aggregation-layers';
import 'maplibre-gl/dist/maplibre-gl.css';

import { bimsMapStyle, switchBasemap } from '../../styles/mapStyle';
import { useMapStore } from '../../stores/mapStore';

// Site point data format: [id, longitude, latitude, record_count]
type SitePoint = [number, number, number, number];

export interface DeckGLMapProps {
  initialCenter?: [number, number];
  initialZoom?: number;
  is3D?: boolean;
  showScaleBar?: boolean;
  showMiniMap?: boolean;
  enableClustering?: boolean;
  onSiteSelect?: (siteId: number | null) => void;
  onSiteHover?: (siteId: number | null) => void;
  onBoundsChange?: (bounds: [number, number, number, number], zoom: number) => void;
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
      showScaleBar = true,
      showMiniMap = false,
      enableClustering = true,
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

    // Track layer visibility changes to trigger re-renders
    // We use visibleLayerIds as a dependency trigger, and read fresh state inside callback
    const visibleLayerIds = useMapStore((state) => state.visibleLayerIds);

    // Also track visualization layers store for persisted layer visibility
    const visualizationLayers = useVisualizationLayersStore((state) => state.layers);

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
      if (!deckOverlayRef.current || !mapRef.current) return;

      // Ensure the map is fully loaded and has a valid viewport
      // This prevents "viewport is null" errors in deck.gl
      if (!mapRef.current.loaded()) return;

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

      const layerArray: unknown[] = [];
      const dynamicMinRadius = getZoomBasedRadius();

      // Get fresh layer visibility from visualization layers store (persisted)
      const vizLayers = useVisualizationLayersStore.getState().layers;

      // Helper to check if a visualization layer is visible by ID
      const isLayerVisible = (layerId: string) => {
        const layer = vizLayers.find((l) => l.id === layerId);
        return layer ? layer.enabled && layer.visible : false;
      };

      // Check layer visibility from visualization store by layer ID
      const showSites = isLayerVisible('sites');
      const showClusters = isLayerVisible('clusters');
      const showHeatmap = isLayerVisible('heatmap');

      // Heatmap Layer (render first, behind other layers)
      // In 3D mode, use extruded grid for terrain-like 3D heatmap effect
      // In 2D mode, use standard heatmap layer
      if (showHeatmap && points.length > 0) {
        if (is3D) {
          // 3D Heatmap using GridLayer for continuous terrain-like appearance
          // Smaller cells create smoother terrain effect
          const getHeatmapCellSize = () => {
            const baseCellSize = 8000; // 8km at zoom 5
            const zoomFactor = Math.pow(2, zoomLevel - 5);
            return Math.max(200, baseCellSize / zoomFactor); // Min 200m
          };

          layerArray.push(
            new GridLayer<SitePoint>({
              id: 'heatmap-3d-layer',
              data: points,
              pickable: true,
              extruded: true,
              cellSize: getHeatmapCellSize(),
              elevationScale: 300, // Height multiplier for terrain effect
              elevationAggregation: 'SUM',
              getPosition: (d: SitePoint) => [d[1], d[2]],
              getElevationWeight: (d: SitePoint) => d[3] || 1,
              getColorWeight: (d: SitePoint) => d[3] || 1,
              colorAggregation: 'SUM',
              coverage: 1.0, // Full coverage for continuous terrain look
              material: {
                ambient: 0.6,
                diffuse: 0.8,
                shininess: 16,
                specularColor: [40, 44, 50],
              },
              colorRange: [
                [65, 105, 125, 255],   // Deep blue-grey (low/cool)
                [65, 182, 196, 255],   // Cyan
                [127, 205, 187, 255],  // Cyan-green
                [199, 233, 180, 255],  // Light green
                [237, 248, 177, 255],  // Light yellow
                [254, 217, 118, 255],  // Yellow
                [254, 178, 76, 255],   // Orange
                [253, 141, 60, 255],   // Dark orange
                [240, 59, 32, 255],    // Red
                [189, 0, 38, 255],     // Deep red (hot/high)
              ],
              onHover: (info: { object?: { position: number[]; count: number; elevationValue: number } }) => {
                if (mapRef.current) {
                  mapRef.current.getCanvas().style.cursor = info.object ? 'pointer' : '';
                }
              },
              updateTriggers: {
                cellSize: [zoomLevel],
              },
            })
          );
        } else {
          // 2D Heatmap using standard HeatmapLayer
          layerArray.push(
            new HeatmapLayer<SitePoint>({
              id: 'heatmap-layer',
              data: points,
              pickable: false,
              getPosition: (d: SitePoint) => [d[1], d[2]],
              getWeight: (d: SitePoint) => d[3] || 1,
              radiusPixels: 60,
              intensity: 1,
              threshold: 0.05,
              colorRange: [
                [65, 182, 196, 255],   // Light cyan
                [127, 205, 187, 255],  // Cyan-green
                [199, 233, 180, 255],  // Light green
                [237, 248, 177, 255],  // Light yellow
                [255, 237, 160, 255],  // Yellow
                [254, 217, 118, 255],  // Orange-yellow
                [254, 178, 76, 255],   // Orange
                [253, 141, 60, 255],   // Dark orange
                [252, 78, 42, 255],    // Red-orange
                [227, 26, 28, 255],    // Red
              ],
            })
          );
        }
      }

      // Cluster Layer using HexagonLayer for proper spatial aggregation
      if (showClusters && points.length > 0) {
        // Calculate hexagon radius based on zoom level
        // At zoom 5: ~20km hexagons, at zoom 10: ~2km, at zoom 15: ~200m
        const getClusterRadius = () => {
          const baseRadius = 20000; // 20km at zoom 5 (smaller for better detail)
          const zoomFactor = Math.pow(2, zoomLevel - 5);
          return Math.max(200, baseRadius / zoomFactor); // Min 200m
        };

        layerArray.push(
          new HexagonLayer<SitePoint>({
            id: 'clusters-layer',
            data: points,
            pickable: true,
            extruded: false,
            radius: getClusterRadius(),
            elevationScale: 0,
            getPosition: (d: SitePoint) => [d[1], d[2]],
            getElevationWeight: (d: SitePoint) => d[3] || 1,
            getColorWeight: (d: SitePoint) => d[3] || 1,
            colorAggregation: 'SUM',
            coverage: 1.0,  // No gaps between hexagons (no border effect)
            colorRange: [
              [65, 182, 196, 200],   // Light cyan (few points)
              [127, 205, 187, 200],  // Cyan-green
              [199, 233, 180, 200],  // Light green
              [254, 217, 118, 200],  // Yellow
              [254, 178, 76, 200],   // Orange
              [227, 26, 28, 200],    // Red (many points)
            ],
            onHover: (info: { object?: { position: number[]; count: number } }) => {
              if (mapRef.current) {
                mapRef.current.getCanvas().style.cursor = info.object ? 'pointer' : '';
              }
            },
            updateTriggers: {
              radius: [zoomLevel],
            },
          })
        );
      }

      // Sites Layer (individual points)
      if (showSites && points.length > 0) {
        if (is3D) {
          // 3D Column Layer - extrude based on record count
          layerArray.push(
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
            })
          );
        } else {
          // 2D Scatter Plot Layer
          layerArray.push(
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
            })
          );
        }
      }

      // Use requestAnimationFrame to ensure viewport is synced
      requestAnimationFrame(() => {
        if (deckOverlayRef.current) {
          try {
            deckOverlayRef.current.setProps({ layers: layerArray });
          } catch (error) {
            // Viewport may not be ready yet, will retry on next update
            console.warn('DeckGL layer update deferred:', error);
          }
        }
      });
    }, [points, selectedId, hoveredId, is3D, maxRecordCount, onSiteSelect, onSiteHover, getZoomBasedRadius, zoomLevel, visibleLayerIds, visualizationLayers]);

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

      // Add scale control (conditional)
      if (showScaleBar) {
        map.addControl(new ScaleControl({ maxWidth: 200 }), 'bottom-left');
      }

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

        // Delay setting isLoaded to ensure deck.gl viewport is synced
        // This prevents "viewport is null" errors during initial render
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            setIsLoaded(true);

            if (onMapReady) {
              onMapReady(map);
            }
          });
        });
      });

      // Track map movement
      map.on('moveend', () => {
        if (onBoundsChange) {
          const bounds = map.getBounds();
          const zoom = map.getZoom();
          onBoundsChange([
            bounds.getWest(),
            bounds.getSouth(),
            bounds.getEast(),
            bounds.getNorth(),
          ], zoom);
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
