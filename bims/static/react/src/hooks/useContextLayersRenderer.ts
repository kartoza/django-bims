/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for rendering context layers from the store onto the map.
 * Adds/removes WMS, XYZ, and GeoJSON layers based on visibility.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useEffect, useRef, useCallback } from 'react';
import type { Map as MapLibreMap } from 'maplibre-gl';
import { useContextLayersStore, ContextLayer } from '../stores/contextLayersStore';

interface UseContextLayersRendererOptions {
  map: MapLibreMap | null;
  enabled?: boolean;
}

export function useContextLayersRenderer({ map, enabled = true }: UseContextLayersRendererOptions) {
  const { layers } = useContextLayersStore();
  const addedLayersRef = useRef<Set<string>>(new Set());

  // Add a WMS layer to the map
  const addWMSLayer = useCallback((map: MapLibreMap, layer: ContextLayer) => {
    const sourceId = `context-source-${layer.id}`;
    const layerId = `context-layer-${layer.id}`;

    if (map.getSource(sourceId)) return; // Already added

    // Build WMS tile URL
    const wmsParams = new URLSearchParams({
      SERVICE: 'WMS',
      VERSION: '1.1.1',
      REQUEST: 'GetMap',
      LAYERS: layer.layerName || '',
      STYLES: '',
      FORMAT: 'image/png',
      TRANSPARENT: 'true',
      SRS: 'EPSG:3857',
      WIDTH: '256',
      HEIGHT: '256',
    });

    const tileUrl = `${layer.url}?${wmsParams.toString()}&BBOX={bbox-epsg-3857}`;

    map.addSource(sourceId, {
      type: 'raster',
      tiles: [tileUrl],
      tileSize: 256,
    });

    // Find first symbol layer to insert before
    const mapLayers = map.getStyle()?.layers || [];
    let firstSymbolId: string | undefined;
    for (const l of mapLayers) {
      if (l.type === 'symbol') {
        firstSymbolId = l.id;
        break;
      }
    }

    map.addLayer(
      {
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: {
          'raster-opacity': layer.opacity,
        },
      },
      firstSymbolId
    );

    addedLayersRef.current.add(layer.id);
  }, []);

  // Add an XYZ tile layer to the map
  const addXYZLayer = useCallback((map: MapLibreMap, layer: ContextLayer) => {
    const sourceId = `context-source-${layer.id}`;
    const layerId = `context-layer-${layer.id}`;

    if (map.getSource(sourceId)) return; // Already added

    // Convert {s} subdomain placeholder to MapLibre format
    const tileUrl = layer.url
      .replace('{s}', '{a|b|c}')
      .replace('{z}', '{z}')
      .replace('{x}', '{x}')
      .replace('{y}', '{y}');

    map.addSource(sourceId, {
      type: 'raster',
      tiles: [layer.url.replace('{s}', 'a')], // Use 'a' subdomain
      tileSize: 256,
      attribution: layer.attribution,
    });

    // Find first symbol layer to insert before
    const mapLayers = map.getStyle()?.layers || [];
    let firstSymbolId: string | undefined;
    for (const l of mapLayers) {
      if (l.type === 'symbol') {
        firstSymbolId = l.id;
        break;
      }
    }

    map.addLayer(
      {
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: {
          'raster-opacity': layer.opacity,
        },
      },
      firstSymbolId
    );

    addedLayersRef.current.add(layer.id);
  }, []);

  // Add a GeoJSON layer to the map
  const addGeoJSONLayer = useCallback(async (map: MapLibreMap, layer: ContextLayer) => {
    const sourceId = `context-source-${layer.id}`;
    const layerId = `context-layer-${layer.id}`;

    if (map.getSource(sourceId)) return; // Already added

    try {
      // Fetch GeoJSON data
      const response = await fetch(layer.url);
      if (!response.ok) {
        console.warn(`Failed to fetch GeoJSON for layer ${layer.name}`);
        return;
      }
      const geojson = await response.json();

      map.addSource(sourceId, {
        type: 'geojson',
        data: geojson,
      });

      // Determine geometry type and add appropriate layer
      const geometryType = geojson.features?.[0]?.geometry?.type || 'Polygon';

      if (geometryType.includes('Point')) {
        map.addLayer({
          id: layerId,
          type: 'circle',
          source: sourceId,
          paint: {
            'circle-radius': 6,
            'circle-color': '#007cbf',
            'circle-opacity': layer.opacity,
          },
        });
      } else if (geometryType.includes('Line')) {
        map.addLayer({
          id: layerId,
          type: 'line',
          source: sourceId,
          paint: {
            'line-color': '#007cbf',
            'line-width': 2,
            'line-opacity': layer.opacity,
          },
        });
      } else {
        // Polygon
        map.addLayer({
          id: layerId,
          type: 'fill',
          source: sourceId,
          paint: {
            'fill-color': '#007cbf',
            'fill-opacity': layer.opacity * 0.3,
          },
        });
        map.addLayer({
          id: `${layerId}-outline`,
          type: 'line',
          source: sourceId,
          paint: {
            'line-color': '#007cbf',
            'line-width': 1,
            'line-opacity': layer.opacity,
          },
        });
      }

      addedLayersRef.current.add(layer.id);
    } catch (error) {
      console.warn(`Error loading GeoJSON layer ${layer.name}:`, error);
    }
  }, []);

  // Update layer visibility
  const updateLayerVisibility = useCallback((map: MapLibreMap, layer: ContextLayer) => {
    const layerId = `context-layer-${layer.id}`;
    const outlineLayerId = `${layerId}-outline`;

    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, 'visibility', layer.visible ? 'visible' : 'none');
    }
    if (map.getLayer(outlineLayerId)) {
      map.setLayoutProperty(outlineLayerId, 'visibility', layer.visible ? 'visible' : 'none');
    }
  }, []);

  // Update layer opacity
  const updateLayerOpacity = useCallback((map: MapLibreMap, layer: ContextLayer) => {
    const layerId = `context-layer-${layer.id}`;

    if (!map.getLayer(layerId)) return;

    const layerType = map.getLayer(layerId)?.type;

    if (layerType === 'raster') {
      map.setPaintProperty(layerId, 'raster-opacity', layer.opacity);
    } else if (layerType === 'fill') {
      map.setPaintProperty(layerId, 'fill-opacity', layer.opacity * 0.3);
      const outlineLayerId = `${layerId}-outline`;
      if (map.getLayer(outlineLayerId)) {
        map.setPaintProperty(outlineLayerId, 'line-opacity', layer.opacity);
      }
    } else if (layerType === 'line') {
      map.setPaintProperty(layerId, 'line-opacity', layer.opacity);
    } else if (layerType === 'circle') {
      map.setPaintProperty(layerId, 'circle-opacity', layer.opacity);
    }
  }, []);

  // Main effect to sync layers with map
  useEffect(() => {
    if (!map || !enabled || !map.loaded()) return;

    const syncLayers = () => {
      layers.forEach((layer) => {
        // Skip basemap layers (handled separately)
        if (layer.category === 'Base Maps') return;

        // Skip disabled layers
        if (!layer.enabled) return;

        const isAdded = addedLayersRef.current.has(layer.id);

        // Add all enabled layers to the map (regardless of visibility)
        if (!isAdded) {
          switch (layer.type) {
            case 'wms':
            case 'wmts':
              addWMSLayer(map, layer);
              break;
            case 'xyz':
              addXYZLayer(map, layer);
              break;
            case 'geojson':
              addGeoJSONLayer(map, layer);
              break;
          }
        }

        // Update visibility after a short delay to ensure layer is added
        setTimeout(() => {
          updateLayerVisibility(map, layer);
          updateLayerOpacity(map, layer);
        }, 100);
      });
    };

    // Sync immediately if map is loaded
    if (map.loaded()) {
      syncLayers();
    }

    // Also sync when map loads
    const handleLoad = () => syncLayers();
    map.on('load', handleLoad);

    return () => {
      map.off('load', handleLoad);
    };
  }, [map, enabled, layers, addWMSLayer, addXYZLayer, addGeoJSONLayer, updateLayerVisibility, updateLayerOpacity]);

  // Re-sync when layers change
  useEffect(() => {
    if (!map || !enabled) return;

    const syncLayers = () => {
      if (!map.loaded()) return;

      layers.forEach((layer) => {
        if (layer.category === 'Base Maps') return;
        if (!layer.enabled) return;

        const isAdded = addedLayersRef.current.has(layer.id);

        // Add layer if not already on map
        if (!isAdded) {
          switch (layer.type) {
            case 'wms':
            case 'wmts':
              addWMSLayer(map, layer);
              break;
            case 'xyz':
              addXYZLayer(map, layer);
              break;
            case 'geojson':
              addGeoJSONLayer(map, layer);
              break;
          }
        }

        // Update visibility after a short delay to ensure layer is added
        setTimeout(() => {
          updateLayerVisibility(map, layer);
          updateLayerOpacity(map, layer);
        }, 100);
      });
    };

    syncLayers();
  }, [layers, map, enabled, addWMSLayer, addXYZLayer, addGeoJSONLayer, updateLayerVisibility, updateLayerOpacity]);

  return { layers };
}

export default useContextLayersRenderer;
