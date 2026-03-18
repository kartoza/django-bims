/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Map style configuration for MapLibre GL.
 * Uses raster tiles for basemap and WMS for data layers.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import type { StyleSpecification } from 'maplibre-gl';

/**
 * GeoServer WMS configuration
 * Configure these based on your GeoServer setup
 */
export const GEOSERVER_CONFIG = {
  baseUrl: '/geoserver/wms',
  workspace: 'bims',
  layers: {
    sites: 'bims:location_site_view',
    rivers: 'bims:rivers',
    catchments: 'bims:catchments',
    provinces: 'bims:provinces',
    protectedAreas: 'bims:protected_areas',
  },
};

/**
 * Build a WMS tile URL for GeoServer
 */
export const buildWmsUrl = (
  layers: string,
  options: {
    transparent?: boolean;
    format?: string;
    styles?: string;
    cql_filter?: string;
  } = {}
): string => {
  const params = new URLSearchParams({
    SERVICE: 'WMS',
    VERSION: '1.1.1',
    REQUEST: 'GetMap',
    LAYERS: layers,
    FORMAT: options.format || 'image/png',
    TRANSPARENT: String(options.transparent ?? true),
    SRS: 'EPSG:3857',
    WIDTH: '256',
    HEIGHT: '256',
    BBOX: '{bbox-epsg-3857}',
  });

  if (options.styles) {
    params.set('STYLES', options.styles);
  }

  if (options.cql_filter) {
    params.set('CQL_FILTER', options.cql_filter);
  }

  return `${GEOSERVER_CONFIG.baseUrl}?${params.toString()}`;
};

/**
 * BIMS Map Style using CartoDB Positron tiles as basemap.
 * Data layers are added dynamically via WMS from GeoServer.
 */
export const bimsMapStyle: StyleSpecification = {
  version: 8,
  name: 'BIMS Map',
  glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
  sprite: 'https://demotiles.maplibre.org/styles/osm-bright-gl-style/sprite',
  sources: {
    // CartoDB Positron - clean, light basemap with good CORS
    'carto-positron': {
      type: 'raster',
      tiles: [
        'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
        'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
        'https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
      ],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxzoom: 20,
    },
    // CartoDB Dark Matter - dark basemap
    'carto-dark': {
      type: 'raster',
      tiles: [
        'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
        'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
        'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
      ],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxzoom: 20,
    },
    // CartoDB Voyager - colorful alternative
    'carto-voyager': {
      type: 'raster',
      tiles: [
        'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
        'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
        'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
      ],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxzoom: 20,
    },
    // OSM tiles (fallback)
    'osm-raster': {
      type: 'raster',
      tiles: [
        'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
      ],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxzoom: 19,
    },
    // ESRI Satellite imagery
    'esri-satellite': {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      attribution:
        'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
      maxzoom: 18,
    },
    // ESRI Topo
    'esri-topo': {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      attribution: 'Tiles &copy; Esri',
      maxzoom: 18,
    },
  },
  layers: [
    // Default basemap layer
    {
      id: 'basemap',
      type: 'raster',
      source: 'carto-positron',
      minzoom: 0,
      maxzoom: 22,
    },
  ],
};

/**
 * Available basemap options for the layer switcher
 */
export const BASEMAP_OPTIONS = [
  { id: 'carto-positron', name: 'Light (Positron)', source: 'carto-positron' },
  { id: 'carto-dark', name: 'Dark', source: 'carto-dark' },
  { id: 'carto-voyager', name: 'Voyager', source: 'carto-voyager' },
  { id: 'osm-raster', name: 'OpenStreetMap', source: 'osm-raster' },
  { id: 'esri-satellite', name: 'Satellite', source: 'esri-satellite' },
  { id: 'esri-topo', name: 'Topographic', source: 'esri-topo' },
];

/**
 * WMS overlay layers that can be toggled
 * These are rendered via GeoServer WMS for security (no data exfiltration)
 */
export const WMS_LAYERS = [
  {
    id: 'wms-sites',
    name: 'Location Sites',
    category: 'biodiversity',
    wmsLayer: GEOSERVER_CONFIG.layers.sites,
    visible: true,
    opacity: 1.0,
  },
  {
    id: 'wms-rivers',
    name: 'Rivers',
    category: 'hydrology',
    wmsLayer: GEOSERVER_CONFIG.layers.rivers,
    visible: false,
    opacity: 0.7,
  },
  {
    id: 'wms-catchments',
    name: 'Catchments',
    category: 'hydrology',
    wmsLayer: GEOSERVER_CONFIG.layers.catchments,
    visible: false,
    opacity: 0.5,
  },
  {
    id: 'wms-provinces',
    name: 'Provinces',
    category: 'boundaries',
    wmsLayer: GEOSERVER_CONFIG.layers.provinces,
    visible: false,
    opacity: 0.5,
  },
  {
    id: 'wms-protected-areas',
    name: 'Protected Areas',
    category: 'conservation',
    wmsLayer: GEOSERVER_CONFIG.layers.protectedAreas,
    visible: false,
    opacity: 0.6,
  },
];

/**
 * Add a WMS layer to the map
 */
export const addWmsLayer = (
  map: maplibregl.Map,
  layerId: string,
  wmsLayer: string,
  options: { opacity?: number; beforeId?: string } = {}
) => {
  const sourceId = `${layerId}-source`;

  // Add source if it doesn't exist
  if (!map.getSource(sourceId)) {
    map.addSource(sourceId, {
      type: 'raster',
      tiles: [buildWmsUrl(wmsLayer)],
      tileSize: 256,
    });
  }

  // Add layer if it doesn't exist
  if (!map.getLayer(layerId)) {
    map.addLayer(
      {
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: {
          'raster-opacity': options.opacity ?? 1.0,
        },
      },
      options.beforeId
    );
  }
};

/**
 * Remove a WMS layer from the map
 */
export const removeWmsLayer = (map: maplibregl.Map, layerId: string) => {
  const sourceId = `${layerId}-source`;

  if (map.getLayer(layerId)) {
    map.removeLayer(layerId);
  }

  if (map.getSource(sourceId)) {
    map.removeSource(sourceId);
  }
};

/**
 * Set WMS layer opacity
 */
export const setWmsLayerOpacity = (
  map: maplibregl.Map,
  layerId: string,
  opacity: number
) => {
  if (map.getLayer(layerId)) {
    map.setPaintProperty(layerId, 'raster-opacity', opacity);
  }
};

/**
 * Switch basemap
 */
export const switchBasemap = (map: maplibregl.Map, sourceId: string) => {
  const basemapLayer = map.getLayer('basemap');
  if (basemapLayer) {
    // Update the source for the basemap layer
    map.removeLayer('basemap');
    map.addLayer(
      {
        id: 'basemap',
        type: 'raster',
        source: sourceId,
        minzoom: 0,
        maxzoom: 22,
      },
      map.getStyle().layers[1]?.id // Add before first overlay layer
    );
  }
};

export default bimsMapStyle;
