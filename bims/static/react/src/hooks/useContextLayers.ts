/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for managing WMS context layers on the map.
 * Fetches layer configuration and adds/removes layers based on visibility.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import type { Map as MapLibreMap, FillPaint, LinePaint, CirclePaint } from 'maplibre-gl';
import { useMapStore, MapLayer } from '../stores/mapStore';

interface WMSLayerConfig {
  id: number;
  name: string;
  wms_url: string;
  wms_layer_name: string;
  wms_format: string;
  default_visibility: boolean;
  order: number;
  native_layer_url?: string;
  native_layer_style?: Record<string, unknown>;
  pmtiles?: string;
  type: 'Layer' | 'LayerGroup';
  layers?: WMSLayerConfig[];
}

interface UseContextLayersOptions {
  map: MapLibreMap | null;
  enabled?: boolean;
}

export function useContextLayers({ map, enabled = true }: UseContextLayersOptions) {
  const [layerConfigs, setLayerConfigs] = useState<WMSLayerConfig[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const addedLayersRef = useRef<Set<string>>(new Set());

  const { layers: layerVisibility, addLayer } = useMapStore();

  // Fetch layer configurations
  useEffect(() => {
    if (!enabled) return;

    const fetchLayers = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('/api/list-non-biodiversity/');
        if (response.ok) {
          const data = await response.json();
          setLayerConfigs(data);

          // Register layers in the mapStore
          const flattenLayers = (items: WMSLayerConfig[]): WMSLayerConfig[] => {
            const result: WMSLayerConfig[] = [];
            items.forEach(item => {
              if (item.type === 'LayerGroup' && item.layers) {
                result.push(...flattenLayers(item.layers));
              } else {
                result.push(item);
              }
            });
            return result;
          };

          const allLayers = flattenLayers(data);
          allLayers.forEach(layer => {
            const mapLayer: MapLayer = {
              id: layer.wms_layer_name || layer.name,
              name: layer.name,
              visible: layer.default_visibility,
              opacity: 1,
              type: 'overlay',
            };
            addLayer(mapLayer);
          });
        } else {
          console.log('Context layers endpoint not available');
        }
      } catch (err) {
        console.log('Failed to fetch context layers');
        setError('Failed to load context layers');
      } finally {
        setIsLoading(false);
      }
    };

    fetchLayers();
  }, [enabled, addLayer]);

  // Add/remove WMS layers based on visibility
  const updateMapLayers = useCallback(() => {
    if (!map || !map.loaded() || layerConfigs.length === 0) return;

    const flattenLayers = (items: WMSLayerConfig[]): WMSLayerConfig[] => {
      const result: WMSLayerConfig[] = [];
      items.forEach(item => {
        if (item.type === 'LayerGroup' && item.layers) {
          result.push(...flattenLayers(item.layers));
        } else {
          result.push(item);
        }
      });
      return result;
    };

    const allLayers = flattenLayers(layerConfigs);

    allLayers.forEach(layerConfig => {
      const layerId = layerConfig.wms_layer_name || layerConfig.name;
      const sourceId = `context-source-${layerId}`;
      const isVisible = layerVisibility[layerId] === true;

      // Determine if this is a vector tile layer or WMS layer
      const isVectorTile = !!layerConfig.native_layer_url || !!layerConfig.pmtiles;

      // Always add layers to the map (they can be hidden via visibility)
      // This ensures layers are ready when user toggles them on
      if (!addedLayersRef.current.has(layerId)) {
        // Find the first symbol layer to insert before (for proper layer ordering)
        const layers = map.getStyle().layers;
        let firstSymbolId: string | undefined;
        for (const layer of layers || []) {
          if (layer.type === 'symbol') {
            firstSymbolId = layer.id;
            break;
          }
        }

        if (isVectorTile) {
          // Compute tile URL
          const tileUrl = layerConfig.native_layer_url?.startsWith('/')
            ? `${window.location.origin}${layerConfig.native_layer_url}`
            : layerConfig.native_layer_url;

          // Add vector tile source
          if (!map.getSource(sourceId) && tileUrl) {
            map.addSource(sourceId, {
              type: 'vector',
              tiles: [tileUrl],
              minzoom: 0,
              maxzoom: 14,
            });
          }

          // Add vector layer with styling from Maputnik or defaults
          const vectorLayerId = `vector-layer-${layerId}`;
          if (map.getSource(sourceId) && !map.getLayer(`${vectorLayerId}-fill`)) {
            // Parse Maputnik style if available
            const maputnikStyle = layerConfig.native_layer_style as {
              layers?: Array<{
                id: string;
                type: string;
                paint?: Record<string, unknown>;
                layout?: Record<string, unknown>;
              }>;
            } | null;

            // Extract paint properties from Maputnik style layers
            let fillPaint: Record<string, unknown> = {
              'fill-color': '#3388ff',
              'fill-opacity': 0.4,
            };
            let linePaint: Record<string, unknown> = {
              'line-color': '#3388ff',
              'line-width': 2,
            };
            let circlePaint: Record<string, unknown> = {
              'circle-color': '#3388ff',
              'circle-radius': 6,
              'circle-stroke-color': '#fff',
              'circle-stroke-width': 2,
            };

            if (maputnikStyle?.layers) {
              for (const styleLayer of maputnikStyle.layers) {
                if (styleLayer.type === 'fill' && styleLayer.paint) {
                  fillPaint = { ...fillPaint, ...styleLayer.paint };
                } else if (styleLayer.type === 'line' && styleLayer.paint) {
                  linePaint = { ...linePaint, ...styleLayer.paint };
                } else if (styleLayer.type === 'circle' && styleLayer.paint) {
                  circlePaint = { ...circlePaint, ...styleLayer.paint };
                }
              }
            }

            // Add fill layer for polygons
            map.addLayer(
              {
                id: `${vectorLayerId}-fill`,
                type: 'fill',
                source: sourceId,
                'source-layer': 'default',
                paint: fillPaint as FillPaint,
                filter: ['==', '$type', 'Polygon'],
              },
              firstSymbolId
            );

            // Add line layer for lines and polygon outlines
            map.addLayer(
              {
                id: `${vectorLayerId}-line`,
                type: 'line',
                source: sourceId,
                'source-layer': 'default',
                paint: linePaint as LinePaint,
                filter: ['any', ['==', '$type', 'LineString'], ['==', '$type', 'Polygon']],
              },
              firstSymbolId
            );

            // Add circle layer for points
            map.addLayer(
              {
                id: `${vectorLayerId}-point`,
                type: 'circle',
                source: sourceId,
                'source-layer': 'default',
                paint: circlePaint as CirclePaint,
                filter: ['==', '$type', 'Point'],
              },
              firstSymbolId
            );
          }

          addedLayersRef.current.add(layerId);
        } else if (layerConfig.wms_url) {
          // Add WMS raster source
          const rasterLayerId = `wms-layer-${layerId}`;

          if (!map.getSource(sourceId)) {
            const wmsUrl = layerConfig.wms_url.startsWith('http')
              ? `/bims_proxy/${layerConfig.wms_url}`
              : layerConfig.wms_url;

            const tileUrl = `${wmsUrl}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=${layerConfig.wms_layer_name}&STYLES=&FORMAT=${layerConfig.wms_format || 'image/png'}&TRANSPARENT=true&SRS=EPSG:3857&WIDTH=256&HEIGHT=256&BBOX={bbox-epsg-3857}`;

            map.addSource(sourceId, {
              type: 'raster',
              tiles: [tileUrl],
              tileSize: 256,
            });
          }

          if (!map.getLayer(rasterLayerId)) {
            map.addLayer(
              {
                id: rasterLayerId,
                type: 'raster',
                source: sourceId,
                paint: {
                  'raster-opacity': 0.7,
                },
              },
              firstSymbolId
            );
          }

          addedLayersRef.current.add(layerId);
        }
      }

      // Update visibility of existing layers
      const vectorLayerId = `vector-layer-${layerId}`;
      const rasterLayerId = `wms-layer-${layerId}`;

      // Toggle vector layers visibility
      [`${vectorLayerId}-fill`, `${vectorLayerId}-line`, `${vectorLayerId}-point`].forEach(id => {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, 'visibility', isVisible ? 'visible' : 'none');
        }
      });

      // Toggle raster layer visibility
      if (map.getLayer(rasterLayerId)) {
        map.setLayoutProperty(rasterLayerId, 'visibility', isVisible ? 'visible' : 'none');
      }
    });
  }, [map, layerConfigs, layerVisibility]);

  // Update layers when visibility changes
  useEffect(() => {
    updateMapLayers();
  }, [updateMapLayers]);

  // Also update when map loads
  useEffect(() => {
    if (!map) return;

    const handleLoad = () => {
      updateMapLayers();
    };

    if (map.loaded()) {
      updateMapLayers();
    } else {
      map.on('load', handleLoad);
    }

    return () => {
      map.off('load', handleLoad);
    };
  }, [map, updateMapLayers]);

  return {
    layerConfigs,
    isLoading,
    error,
  };
}

export default useContextLayers;
