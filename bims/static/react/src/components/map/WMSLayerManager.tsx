/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * WMS Layer Manager - Handles WMS layers from GeoServer
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useCallback, useState } from 'react';
import type { Map as MapLibreMap } from 'maplibre-gl';
import { useMapStore } from '../../stores/mapStore';

export interface WMSLayerConfig {
  id: string;
  name: string;
  url: string;
  layers: string;
  format?: string;
  transparent?: boolean;
  version?: string;
  crs?: string;
  styles?: string;
  opacity?: number;
  visible?: boolean;
  minZoom?: number;
  maxZoom?: number;
  attribution?: string;
  legendUrl?: string;
}

interface WMSLayerManagerProps {
  map: MapLibreMap | null;
  layers?: WMSLayerConfig[];
  geoserverUrl?: string;
}

// Default BIMS GeoServer layers
const defaultWMSLayers: WMSLayerConfig[] = [
  {
    id: 'boundaries-wms',
    name: 'Administrative Boundaries',
    url: '/geoserver/wms',
    layers: 'bims:boundaries',
    transparent: true,
    opacity: 0.5,
    visible: false,
    legendUrl: '/geoserver/wms?service=WMS&request=GetLegendGraphic&layer=bims:boundaries&format=image/png',
  },
  {
    id: 'rivers-wms',
    name: 'Rivers',
    url: '/geoserver/wms',
    layers: 'bims:rivers',
    transparent: true,
    opacity: 0.7,
    visible: false,
    legendUrl: '/geoserver/wms?service=WMS&request=GetLegendGraphic&layer=bims:rivers&format=image/png',
  },
  {
    id: 'catchments-wms',
    name: 'Catchments',
    url: '/geoserver/wms',
    layers: 'bims:catchments',
    transparent: true,
    opacity: 0.4,
    visible: false,
    legendUrl: '/geoserver/wms?service=WMS&request=GetLegendGraphic&layer=bims:catchments&format=image/png',
  },
  {
    id: 'protected-areas-wms',
    name: 'Protected Areas',
    url: '/geoserver/wms',
    layers: 'bims:protected_areas',
    transparent: true,
    opacity: 0.5,
    visible: false,
    styles: 'protected_areas',
    legendUrl: '/geoserver/wms?service=WMS&request=GetLegendGraphic&layer=bims:protected_areas&format=image/png',
  },
  {
    id: 'ecoregions-wms',
    name: 'Ecoregions',
    url: '/geoserver/wms',
    layers: 'bims:ecoregions',
    transparent: true,
    opacity: 0.3,
    visible: false,
    legendUrl: '/geoserver/wms?service=WMS&request=GetLegendGraphic&layer=bims:ecoregions&format=image/png',
  },
];

/**
 * Build WMS tile URL for MapLibre GL
 */
const buildWMSTileUrl = (config: WMSLayerConfig): string => {
  const baseUrl = config.url;
  const params = new URLSearchParams({
    service: 'WMS',
    version: config.version || '1.1.1',
    request: 'GetMap',
    layers: config.layers,
    format: config.format || 'image/png',
    transparent: String(config.transparent ?? true),
    srs: config.crs || 'EPSG:3857',
    styles: config.styles || '',
    width: '256',
    height: '256',
    bbox: '{bbox-epsg-3857}',
  });

  return `${baseUrl}?${params.toString()}`;
};

export const WMSLayerManager: React.FC<WMSLayerManagerProps> = ({
  map,
  layers = defaultWMSLayers,
  geoserverUrl,
}) => {
  const [addedLayers, setAddedLayers] = useState<Set<string>>(new Set());
  const { layers: visibleLayers, layerOpacities, setLayerVisibility } = useMapStore();

  // Add WMS layers to the map
  const addWMSLayer = useCallback(
    (config: WMSLayerConfig) => {
      if (!map || addedLayers.has(config.id)) return;

      const tileUrl = buildWMSTileUrl({
        ...config,
        url: geoserverUrl || config.url,
      });

      try {
        // Add source
        if (!map.getSource(config.id)) {
          map.addSource(config.id, {
            type: 'raster',
            tiles: [tileUrl],
            tileSize: 256,
            attribution: config.attribution || '',
          });
        }

        // Add layer
        if (!map.getLayer(config.id)) {
          // Insert WMS layers below deck.gl layers but above basemap
          // Find the first symbol layer to insert before
          const mapLayers = map.getStyle()?.layers || [];
          let insertBefore: string | undefined;
          for (const layer of mapLayers) {
            if (layer.type === 'symbol') {
              insertBefore = layer.id;
              break;
            }
          }

          map.addLayer(
            {
              id: config.id,
              type: 'raster',
              source: config.id,
              minzoom: config.minZoom || 0,
              maxzoom: config.maxZoom || 22,
              paint: {
                'raster-opacity': config.opacity ?? 1,
              },
              layout: {
                visibility: config.visible ? 'visible' : 'none',
              },
            },
            insertBefore
          );
        }

        setAddedLayers((prev) => new Set(prev).add(config.id));
      } catch (error) {
        console.error(`Failed to add WMS layer ${config.id}:`, error);
      }
    },
    [map, addedLayers, geoserverUrl]
  );

  // Update layer visibility
  const updateLayerVisibility = useCallback(
    (layerId: string, visible: boolean) => {
      if (!map || !map.getLayer(layerId)) return;

      map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
    },
    [map]
  );

  // Update layer opacity
  const updateLayerOpacity = useCallback(
    (layerId: string, opacity: number) => {
      if (!map || !map.getLayer(layerId)) return;

      map.setPaintProperty(layerId, 'raster-opacity', opacity);
    },
    [map]
  );

  // Remove WMS layer
  const removeWMSLayer = useCallback(
    (layerId: string) => {
      if (!map) return;

      try {
        if (map.getLayer(layerId)) {
          map.removeLayer(layerId);
        }
        if (map.getSource(layerId)) {
          map.removeSource(layerId);
        }
        setAddedLayers((prev) => {
          const next = new Set(prev);
          next.delete(layerId);
          return next;
        });
      } catch (error) {
        console.error(`Failed to remove WMS layer ${layerId}:`, error);
      }
    },
    [map]
  );

  // Initialize layers when map is ready
  useEffect(() => {
    if (!map) return;

    const handleMapLoad = () => {
      layers.forEach((config) => {
        addWMSLayer(config);
      });
    };

    if (map.isStyleLoaded()) {
      handleMapLoad();
    } else {
      map.on('style.load', handleMapLoad);
    }

    return () => {
      map.off('style.load', handleMapLoad);
    };
  }, [map, layers, addWMSLayer]);

  // Sync visibility with store
  useEffect(() => {
    if (!map) return;

    layers.forEach((config) => {
      // Map layer IDs from store to WMS layer IDs
      const storeKey = config.id.replace('-wms', '');
      const isVisible = visibleLayers[storeKey] ?? config.visible ?? false;
      updateLayerVisibility(config.id, isVisible);
    });
  }, [map, layers, visibleLayers, updateLayerVisibility]);

  // Sync opacity with store
  useEffect(() => {
    if (!map) return;

    layers.forEach((config) => {
      const opacity = layerOpacities[config.id] ?? config.opacity ?? 1;
      updateLayerOpacity(config.id, opacity);
    });
  }, [map, layers, layerOpacities, updateLayerOpacity]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      addedLayers.forEach((layerId) => {
        removeWMSLayer(layerId);
      });
    };
    // Only run on unmount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // This component doesn't render anything visible
  return null;
};

/**
 * Hook to get WMS capabilities from GeoServer
 */
export const useWMSCapabilities = (geoserverUrl: string) => {
  const [layers, setLayers] = useState<WMSLayerConfig[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCapabilities = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${geoserverUrl}?service=WMS&request=GetCapabilities&version=1.3.0`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch WMS capabilities');
        }

        const text = await response.text();
        const parser = new DOMParser();
        const xml = parser.parseFromString(text, 'text/xml');

        // Parse layers from capabilities
        const layerElements = xml.querySelectorAll('Layer > Layer');
        const parsedLayers: WMSLayerConfig[] = [];

        layerElements.forEach((layer) => {
          const name = layer.querySelector('Name')?.textContent;
          const title = layer.querySelector('Title')?.textContent;

          if (name) {
            parsedLayers.push({
              id: `wms-${name.replace(/[^a-zA-Z0-9]/g, '-')}`,
              name: title || name,
              url: geoserverUrl,
              layers: name,
              transparent: true,
              visible: false,
              opacity: 0.7,
            });
          }
        });

        setLayers(parsedLayers);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    if (geoserverUrl) {
      fetchCapabilities();
    }
  }, [geoserverUrl]);

  return { layers, isLoading, error };
};

export default WMSLayerManager;
