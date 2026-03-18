/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Map style configuration for MapLibre GL.
 * Uses multiple tile sources for reliability.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import type { StyleSpecification } from 'maplibre-gl';

/**
 * BIMS Map Style using CartoDB Positron tiles.
 * CartoDB tiles have good CORS support and are visually clean.
 */
export const bimsMapStyle: StyleSpecification = {
  version: 8,
  name: 'BIMS Natural',
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
    // Alternative: OSM tiles (as fallback)
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
    // Satellite imagery from ESRI
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
  },
  layers: [
    // Default basemap - CartoDB Positron (clean, light, works well with data overlays)
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
 * Alternative dark style for contrast
 */
export const bimsDarkMapStyle: StyleSpecification = {
  version: 8,
  name: 'BIMS Dark',
  glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
  sources: {
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
  },
  layers: [
    {
      id: 'basemap',
      type: 'raster',
      source: 'carto-dark',
    },
  ],
};

export default bimsMapStyle;
