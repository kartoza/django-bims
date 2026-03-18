/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Beautiful vector tile map style following OpenMapTiles schema.
 * Uses free vector tile sources compatible with OpenMapTiles specification.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import type { StyleSpecification } from 'maplibre-gl';

// Color palette - inspired by natural environments
const colors = {
  // Land colors
  land: '#f8f4f0',
  landUse: {
    park: '#d8e8c8',
    forest: '#c8d8b8',
    grass: '#e6efc8',
    residential: '#ebe8e4',
    industrial: '#ddd',
    commercial: '#ece8e4',
    farmland: '#eef0d5',
    cemetery: '#c6d8c5',
    hospital: '#f0e0e0',
    school: '#f0e4d8',
    water: '#a0d0ff',
  },
  // Water colors
  water: '#7eb8dc',
  waterway: '#7eb8dc',
  // Road colors
  road: {
    motorway: '#f99a52',
    trunk: '#ffc73d',
    primary: '#fee89c',
    secondary: '#fff',
    tertiary: '#fff',
    residential: '#fff',
    path: '#ddd',
  },
  // Building colors
  building: '#ddd',
  buildingOutline: '#ccc',
  // Boundary colors
  boundary: {
    country: '#8e6c8a',
    state: '#b8a2b6',
    admin: '#c8b8c6',
  },
  // Label colors
  text: {
    primary: '#333',
    secondary: '#666',
    water: '#1e6da0',
    park: '#2a603b',
    halo: '#fff',
  },
};

/**
 * Beautiful map style using free vector tiles.
 *
 * This style uses OpenFreeMap tiles which are free, open, and follow
 * the OpenMapTiles schema specification.
 */
export const bimsMapStyle: StyleSpecification = {
  version: 8,
  name: 'BIMS Natural',
  glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
  sprite: 'https://tiles.openfreemap.org/sprites/liberty',
  sources: {
    'openmaptiles': {
      type: 'vector',
      url: 'https://tiles.openfreemap.org/planet',
      attribution: '© <a href="https://openfreemap.org">OpenFreeMap</a> © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    },
  },
  layers: [
    // Background
    {
      id: 'background',
      type: 'background',
      paint: {
        'background-color': colors.land,
      },
    },

    // Landuse - parks, forests, etc
    {
      id: 'landuse-park',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'landuse',
      filter: ['in', 'class', 'park', 'recreation_ground'],
      paint: {
        'fill-color': colors.landUse.park,
      },
    },
    {
      id: 'landuse-forest',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'landuse',
      filter: ['==', 'class', 'wood'],
      paint: {
        'fill-color': colors.landUse.forest,
      },
    },
    {
      id: 'landuse-grass',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'landuse',
      filter: ['in', 'class', 'grass', 'meadow', 'village_green'],
      paint: {
        'fill-color': colors.landUse.grass,
      },
    },
    {
      id: 'landuse-residential',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'landuse',
      filter: ['==', 'class', 'residential'],
      paint: {
        'fill-color': colors.landUse.residential,
      },
    },
    {
      id: 'landuse-farmland',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'landuse',
      filter: ['in', 'class', 'farmland', 'farm'],
      paint: {
        'fill-color': colors.landUse.farmland,
      },
    },
    {
      id: 'landuse-cemetery',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'landuse',
      filter: ['==', 'class', 'cemetery'],
      paint: {
        'fill-color': colors.landUse.cemetery,
      },
    },

    // Landcover
    {
      id: 'landcover-grass',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'landcover',
      filter: ['==', 'class', 'grass'],
      paint: {
        'fill-color': colors.landUse.grass,
        'fill-opacity': 0.7,
      },
    },
    {
      id: 'landcover-wood',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'landcover',
      filter: ['==', 'class', 'wood'],
      paint: {
        'fill-color': colors.landUse.forest,
        'fill-opacity': 0.8,
      },
    },

    // Water
    {
      id: 'water',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'water',
      paint: {
        'fill-color': colors.water,
      },
    },
    {
      id: 'waterway',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'waterway',
      paint: {
        'line-color': colors.waterway,
        'line-width': [
          'interpolate', ['linear'], ['zoom'],
          8, 0.5,
          14, 3,
          20, 8,
        ],
      },
    },

    // Buildings
    {
      id: 'building',
      type: 'fill',
      source: 'openmaptiles',
      'source-layer': 'building',
      minzoom: 13,
      paint: {
        'fill-color': colors.building,
        'fill-opacity': [
          'interpolate', ['linear'], ['zoom'],
          13, 0,
          14, 0.8,
        ],
      },
    },
    {
      id: 'building-outline',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'building',
      minzoom: 14,
      paint: {
        'line-color': colors.buildingOutline,
        'line-width': 0.5,
      },
    },

    // Roads - casing (outline)
    {
      id: 'road-motorway-casing',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'motorway'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#c75d3a',
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          5, 1.5,
          10, 3,
          14, 8,
          18, 24,
        ],
      },
    },
    {
      id: 'road-trunk-casing',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'trunk'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#d4a82c',
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          7, 1,
          10, 2.5,
          14, 6,
          18, 20,
        ],
      },
    },
    {
      id: 'road-primary-casing',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'primary'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#c8a870',
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          8, 0.5,
          10, 2,
          14, 5,
          18, 16,
        ],
      },
    },
    {
      id: 'road-secondary-casing',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'secondary'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#ccc',
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          10, 1,
          14, 4,
          18, 14,
        ],
      },
    },

    // Roads - fill
    {
      id: 'road-motorway',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'motorway'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': colors.road.motorway,
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          5, 0.5,
          10, 2,
          14, 6,
          18, 20,
        ],
      },
    },
    {
      id: 'road-trunk',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'trunk'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': colors.road.trunk,
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          7, 0.5,
          10, 1.5,
          14, 4,
          18, 16,
        ],
      },
    },
    {
      id: 'road-primary',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'primary'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': colors.road.primary,
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          8, 0.3,
          10, 1.5,
          14, 3.5,
          18, 12,
        ],
      },
    },
    {
      id: 'road-secondary',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'secondary'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': colors.road.secondary,
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          10, 0.5,
          14, 2.5,
          18, 10,
        ],
      },
    },
    {
      id: 'road-tertiary',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['==', 'class', 'tertiary'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': colors.road.tertiary,
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          11, 0.5,
          14, 2,
          18, 8,
        ],
      },
    },
    {
      id: 'road-minor',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['in', 'class', 'minor', 'service'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': colors.road.residential,
        'line-width': [
          'interpolate', ['exponential', 1.5], ['zoom'],
          13, 0.5,
          14, 1.5,
          18, 6,
        ],
      },
    },
    {
      id: 'road-path',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['all', ['in', 'class', 'path', 'track'], ['!has', 'brunnel']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': colors.road.path,
        'line-width': [
          'interpolate', ['linear'], ['zoom'],
          14, 0.5,
          18, 2,
        ],
        'line-dasharray': [2, 1],
      },
    },

    // Railways
    {
      id: 'railway',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['==', 'class', 'rail'],
      paint: {
        'line-color': '#bbb',
        'line-width': [
          'interpolate', ['linear'], ['zoom'],
          8, 0.5,
          14, 2,
        ],
      },
    },
    {
      id: 'railway-hatching',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'transportation',
      filter: ['==', 'class', 'rail'],
      paint: {
        'line-color': '#bbb',
        'line-dasharray': [0.5, 5],
        'line-width': [
          'interpolate', ['linear'], ['zoom'],
          8, 2,
          14, 6,
        ],
      },
    },

    // Admin boundaries
    {
      id: 'admin-country',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'boundary',
      filter: ['all', ['==', 'admin_level', 2], ['!has', 'claimed_by']],
      paint: {
        'line-color': colors.boundary.country,
        'line-width': [
          'interpolate', ['linear'], ['zoom'],
          3, 0.5,
          10, 2,
        ],
        'line-dasharray': [3, 1, 1, 1],
      },
    },
    {
      id: 'admin-state',
      type: 'line',
      source: 'openmaptiles',
      'source-layer': 'boundary',
      filter: ['all', ['==', 'admin_level', 4], ['!has', 'claimed_by']],
      minzoom: 4,
      paint: {
        'line-color': colors.boundary.state,
        'line-width': [
          'interpolate', ['linear'], ['zoom'],
          4, 0.3,
          10, 1,
        ],
        'line-dasharray': [2, 2],
      },
    },

    // Place labels - countries
    {
      id: 'place-country',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'place',
      filter: ['==', 'class', 'country'],
      maxzoom: 6,
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Bold'],
        'text-size': [
          'interpolate', ['linear'], ['zoom'],
          2, 10,
          5, 16,
        ],
        'text-transform': 'uppercase',
        'text-letter-spacing': 0.15,
      },
      paint: {
        'text-color': colors.text.primary,
        'text-halo-color': colors.text.halo,
        'text-halo-width': 1.5,
      },
    },

    // Place labels - states/provinces
    {
      id: 'place-state',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'place',
      filter: ['==', 'class', 'state'],
      minzoom: 4,
      maxzoom: 8,
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Regular'],
        'text-size': [
          'interpolate', ['linear'], ['zoom'],
          4, 9,
          7, 14,
        ],
        'text-transform': 'uppercase',
        'text-letter-spacing': 0.1,
      },
      paint: {
        'text-color': colors.text.secondary,
        'text-halo-color': colors.text.halo,
        'text-halo-width': 1.5,
      },
    },

    // Place labels - cities
    {
      id: 'place-city',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'place',
      filter: ['==', 'class', 'city'],
      minzoom: 5,
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Bold'],
        'text-size': [
          'interpolate', ['linear'], ['zoom'],
          5, 10,
          10, 18,
        ],
      },
      paint: {
        'text-color': colors.text.primary,
        'text-halo-color': colors.text.halo,
        'text-halo-width': 1.5,
      },
    },

    // Place labels - towns
    {
      id: 'place-town',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'place',
      filter: ['==', 'class', 'town'],
      minzoom: 7,
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Regular'],
        'text-size': [
          'interpolate', ['linear'], ['zoom'],
          7, 10,
          14, 16,
        ],
      },
      paint: {
        'text-color': colors.text.primary,
        'text-halo-color': colors.text.halo,
        'text-halo-width': 1.2,
      },
    },

    // Place labels - villages
    {
      id: 'place-village',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'place',
      filter: ['==', 'class', 'village'],
      minzoom: 10,
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Regular'],
        'text-size': [
          'interpolate', ['linear'], ['zoom'],
          10, 9,
          14, 13,
        ],
      },
      paint: {
        'text-color': colors.text.secondary,
        'text-halo-color': colors.text.halo,
        'text-halo-width': 1,
      },
    },

    // Water labels
    {
      id: 'water-name-ocean',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'water_name',
      filter: ['==', 'class', 'ocean'],
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Italic'],
        'text-size': 14,
        'text-letter-spacing': 0.2,
      },
      paint: {
        'text-color': colors.text.water,
        'text-halo-color': 'rgba(255,255,255,0.5)',
        'text-halo-width': 1,
      },
    },
    {
      id: 'water-name-lake',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'water_name',
      filter: ['==', 'class', 'lake'],
      minzoom: 8,
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Italic'],
        'text-size': [
          'interpolate', ['linear'], ['zoom'],
          8, 10,
          14, 14,
        ],
      },
      paint: {
        'text-color': colors.text.water,
        'text-halo-color': 'rgba(255,255,255,0.5)',
        'text-halo-width': 1,
      },
    },

    // Road labels
    {
      id: 'road-label',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'transportation_name',
      minzoom: 13,
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Regular'],
        'text-size': [
          'interpolate', ['linear'], ['zoom'],
          13, 9,
          18, 14,
        ],
        'symbol-placement': 'line',
        'text-rotation-alignment': 'map',
        'text-max-angle': 30,
      },
      paint: {
        'text-color': colors.text.secondary,
        'text-halo-color': colors.text.halo,
        'text-halo-width': 1,
      },
    },

    // Park labels
    {
      id: 'park-label',
      type: 'symbol',
      source: 'openmaptiles',
      'source-layer': 'park',
      minzoom: 10,
      layout: {
        'text-field': '{name:latin}',
        'text-font': ['Noto Sans Italic'],
        'text-size': 11,
      },
      paint: {
        'text-color': colors.text.park,
        'text-halo-color': colors.text.halo,
        'text-halo-width': 1,
      },
    },
  ],
};

export default bimsMapStyle;
