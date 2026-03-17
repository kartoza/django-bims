/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Map context provider for MapLibre GL integration.
 */
import React, { createContext, useContext, useRef, useCallback, useState } from 'react';
import type { Map as MapLibreMap, LngLatBoundsLike, MapOptions } from 'maplibre-gl';

interface MapContextValue {
  map: MapLibreMap | null;
  setMap: (map: MapLibreMap | null) => void;
  isMapReady: boolean;

  // Map operations
  flyTo: (center: [number, number], zoom?: number) => void;
  fitBounds: (bounds: LngLatBoundsLike, padding?: number) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  resetView: () => void;

  // Layer operations
  addGeoJSONLayer: (id: string, data: GeoJSON.GeoJSON, options?: Record<string, unknown>) => void;
  removeLayer: (id: string) => void;
  setLayerVisibility: (id: string, visible: boolean) => void;

  // Feature operations
  highlightFeature: (layerId: string, featureId: string | number | null) => void;
}

const MapContext = createContext<MapContextValue | null>(null);

// Default map center and zoom (South Africa)
const DEFAULT_CENTER: [number, number] = [24.5, -29.0];
const DEFAULT_ZOOM = 5;

interface MapProviderProps {
  children: React.ReactNode;
}

export const MapProvider: React.FC<MapProviderProps> = ({ children }) => {
  const [map, setMapState] = useState<MapLibreMap | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);

  const setMap = useCallback((newMap: MapLibreMap | null) => {
    setMapState(newMap);
    setIsMapReady(!!newMap);
  }, []);

  const flyTo = useCallback((center: [number, number], zoom?: number) => {
    if (!map) return;
    map.flyTo({
      center,
      zoom: zoom ?? map.getZoom(),
      duration: 1500,
    });
  }, [map]);

  const fitBounds = useCallback((bounds: LngLatBoundsLike, padding = 50) => {
    if (!map) return;
    map.fitBounds(bounds, {
      padding,
      duration: 1000,
    });
  }, [map]);

  const zoomIn = useCallback(() => {
    if (!map) return;
    map.zoomIn({ duration: 300 });
  }, [map]);

  const zoomOut = useCallback(() => {
    if (!map) return;
    map.zoomOut({ duration: 300 });
  }, [map]);

  const resetView = useCallback(() => {
    if (!map) return;
    map.flyTo({
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      duration: 1500,
    });
  }, [map]);

  const addGeoJSONLayer = useCallback((
    id: string,
    data: GeoJSON.GeoJSON,
    options: Record<string, unknown> = {}
  ) => {
    if (!map) return;

    // Remove existing layer and source if they exist
    if (map.getLayer(id)) {
      map.removeLayer(id);
    }
    if (map.getSource(id)) {
      map.removeSource(id);
    }

    // Add source
    map.addSource(id, {
      type: 'geojson',
      data,
    });

    // Determine layer type based on geometry
    const geometryType = (data as GeoJSON.FeatureCollection).features?.[0]?.geometry?.type;
    let layerType: 'circle' | 'line' | 'fill' = 'circle';

    if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
      layerType = 'line';
    } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
      layerType = 'fill';
    }

    // Add layer with default styling
    const layerConfig: any = {
      id,
      source: id,
      type: layerType,
      ...options,
    };

    // Default paint properties
    if (layerType === 'circle' && !options.paint) {
      layerConfig.paint = {
        'circle-radius': 6,
        'circle-color': '#0073e6',
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
      };
    } else if (layerType === 'line' && !options.paint) {
      layerConfig.paint = {
        'line-color': '#0073e6',
        'line-width': 2,
      };
    } else if (layerType === 'fill' && !options.paint) {
      layerConfig.paint = {
        'fill-color': '#0073e6',
        'fill-opacity': 0.3,
        'fill-outline-color': '#0073e6',
      };
    }

    map.addLayer(layerConfig);
  }, [map]);

  const removeLayer = useCallback((id: string) => {
    if (!map) return;

    if (map.getLayer(id)) {
      map.removeLayer(id);
    }
    if (map.getSource(id)) {
      map.removeSource(id);
    }
  }, [map]);

  const setLayerVisibility = useCallback((id: string, visible: boolean) => {
    if (!map) return;

    if (map.getLayer(id)) {
      map.setLayoutProperty(id, 'visibility', visible ? 'visible' : 'none');
    }
  }, [map]);

  const highlightFeature = useCallback((
    layerId: string,
    featureId: string | number | null
  ) => {
    if (!map) return;

    // Remove previous highlight
    if (map.getLayer(`${layerId}-highlight`)) {
      map.removeLayer(`${layerId}-highlight`);
    }

    if (featureId === null) return;

    // Add highlight layer
    const layer = map.getLayer(layerId);
    if (!layer) return;

    const layerType = layer.type;

    if (layerType === 'circle') {
      map.addLayer({
        id: `${layerId}-highlight`,
        source: layerId as string,
        type: 'circle',
        filter: ['==', ['get', 'id'], featureId],
        paint: {
          'circle-radius': 10,
          'circle-color': '#ff9900',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff',
        },
      });
    }
  }, [map]);

  const value: MapContextValue = {
    map,
    setMap,
    isMapReady,
    flyTo,
    fitBounds,
    zoomIn,
    zoomOut,
    resetView,
    addGeoJSONLayer,
    removeLayer,
    setLayerVisibility,
    highlightFeature,
  };

  return (
    <MapContext.Provider value={value}>
      {children}
    </MapContext.Provider>
  );
};

export const useMap = (): MapContextValue => {
  const context = useContext(MapContext);
  if (!context) {
    throw new Error('useMap must be used within a MapProvider');
  }
  return context;
};

export default MapProvider;
