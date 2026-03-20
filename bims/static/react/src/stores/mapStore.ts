/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Zustand store for map state management.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface MapLayer {
  id: string;
  name: string;
  visible: boolean;
  opacity: number;
  type: 'base' | 'overlay' | 'data';
}

export type DrawMode = 'none' | 'point' | 'polygon' | 'line' | 'circle' | 'bbox' | 'rectangle' | 'freehand';

export type BasemapStyle = 'streets' | 'satellite' | 'terrain' | 'light' | 'dark';

export interface LayerVisibility {
  sites: boolean;
  clusters: boolean;
  heatmap: boolean;
  boundaries: boolean;
  rivers: boolean;
  catchments: boolean;
  protected: boolean;
  [key: string]: boolean;
}

export interface SelectedFeature {
  type: 'site' | 'record' | 'taxon';
  id: number;
  properties: Record<string, unknown>;
}

interface MapState {
  // View state
  center: [number, number];
  zoom: number;
  bearing: number;
  pitch: number;

  // Selection state
  selectedSiteId: number | null;
  selectedRecordId: number | null;
  hoveredSiteId: number | null;
  selectedFeature: SelectedFeature | null;

  // Basemap state
  basemapStyle: BasemapStyle;

  // Layer state
  layers: LayerVisibility;
  layerOpacities: Record<string, number>;
  layerList: MapLayer[];
  visibleLayerIds: string[];

  // Interaction state
  drawMode: DrawMode;
  isLoading: boolean;
  isDrawing: boolean;

  // Drawn features
  drawnFeatures: GeoJSON.Feature[];
  drawnBbox: string | null;

  // Bounds
  currentBounds: [number, number, number, number] | null;

  // Actions
  setCenter: (center: [number, number]) => void;
  setZoom: (zoom: number) => void;
  setView: (center: [number, number], zoom: number) => void;
  setBearing: (bearing: number) => void;
  setPitch: (pitch: number) => void;
  flyTo: (center: [number, number], zoom?: number) => void;

  selectSite: (siteId: number | null) => void;
  selectRecord: (recordId: number | null) => void;
  setHoveredSite: (siteId: number | null) => void;
  setSelectedFeature: (feature: SelectedFeature | null) => void;

  setBasemapStyle: (style: BasemapStyle) => void;
  setLayerVisibility: (layerId: string, visible: boolean) => void;
  setLayerOpacity: (layerId: string, opacity: number) => void;
  toggleLayer: (layerId: string) => void;
  addLayer: (layer: MapLayer) => void;
  removeLayer: (layerId: string) => void;

  setDrawMode: (mode: DrawMode) => void;
  startDrawing: () => void;
  stopDrawing: () => void;
  clearDrawing: () => void;
  addDrawnFeature: (feature: GeoJSON.Feature) => void;
  clearDrawnFeatures: () => void;
  removeDrawnFeature: (index: number) => void;
  setDrawnBbox: (bbox: string | null) => void;

  setLoading: (loading: boolean) => void;
  setBounds: (bounds: [number, number, number, number] | null) => void;

  reset: () => void;
}

const initialState = {
  // Default center on South Africa
  center: [24.5, -29.0] as [number, number],
  zoom: 5,
  bearing: 0,
  pitch: 0,

  selectedSiteId: null as number | null,
  selectedRecordId: null as number | null,
  hoveredSiteId: null as number | null,
  selectedFeature: null as SelectedFeature | null,

  basemapStyle: 'streets' as BasemapStyle,
  layers: {
    sites: true,
    clusters: true,
    heatmap: false,
    boundaries: false,
    rivers: false,
    catchments: false,
    protected: false,
  } as LayerVisibility,
  layerOpacities: {} as Record<string, number>,
  layerList: [] as MapLayer[],
  visibleLayerIds: ['sites', 'clusters'] as string[],

  drawMode: 'none' as DrawMode,
  isLoading: false,
  isDrawing: false,

  drawnFeatures: [] as GeoJSON.Feature[],
  drawnBbox: null as string | null,
  currentBounds: null as [number, number, number, number] | null,
};

export const useMapStore = create<MapState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        setCenter: (center) => set({ center }),

        setZoom: (zoom) => set({ zoom }),

        setView: (center, zoom) => set({ center, zoom }),

        setBearing: (bearing) => set({ bearing }),

        setPitch: (pitch) => set({ pitch }),

        flyTo: (center, zoom) => {
          // This will be handled by the MapContainer component
          // We just update the state here
          set({ center, zoom: zoom || get().zoom });
        },

        selectSite: (siteId) =>
          set({
            selectedSiteId: siteId,
            selectedRecordId: null, // Clear record selection when site changes
          }),

        selectRecord: (recordId) => set({ selectedRecordId: recordId }),

        setHoveredSite: (siteId) => set({ hoveredSiteId: siteId }),

        setSelectedFeature: (feature) => set({ selectedFeature: feature }),

        setBasemapStyle: (style) => set({ basemapStyle: style }),

        setLayerVisibility: (layerId, visible) => {
          const layers = { ...get().layers, [layerId]: visible };
          const visibleLayerIds = Object.entries(layers)
            .filter(([, v]) => v)
            .map(([k]) => k);
          set({ layers, visibleLayerIds });
        },

        setLayerOpacity: (layerId, opacity) => {
          const layerOpacities = { ...get().layerOpacities, [layerId]: opacity };
          set({ layerOpacities });
        },

        toggleLayer: (layerId) => {
          const layers = { ...get().layers };
          layers[layerId] = !layers[layerId];
          const visibleLayerIds = Object.entries(layers)
            .filter(([, v]) => v)
            .map(([k]) => k);
          set({ layers, visibleLayerIds });
        },

        addLayer: (layer) => {
          // Prevent duplicates
          const existingIds = new Set(get().layerList.map(l => l.id));
          if (existingIds.has(layer.id)) {
            return; // Layer already exists, skip
          }
          const layerList = [...get().layerList, layer];
          const layers = { ...get().layers, [layer.id]: layer.visible };
          const visibleLayerIds = Object.entries(layers)
            .filter(([, v]) => v)
            .map(([k]) => k);
          set({ layerList, layers, visibleLayerIds });
        },

        removeLayer: (layerId) => {
          const layerList = get().layerList.filter((l) => l.id !== layerId);
          const layers = { ...get().layers };
          delete layers[layerId];
          const visibleLayerIds = Object.entries(layers)
            .filter(([, v]) => v)
            .map(([k]) => k);
          set({ layerList, layers, visibleLayerIds });
        },

        setDrawMode: (mode) => set({ drawMode: mode }),

        startDrawing: () => set({ isDrawing: true, drawMode: 'bbox' }),

        stopDrawing: () => set({ isDrawing: false, drawMode: 'none' }),

        clearDrawing: () =>
          set({
            isDrawing: false,
            drawMode: 'none',
            drawnBbox: null,
            drawnFeatures: [],
          }),

        addDrawnFeature: (feature) =>
          set({ drawnFeatures: [...get().drawnFeatures, feature] }),

        clearDrawnFeatures: () => set({ drawnFeatures: [] }),

        removeDrawnFeature: (index) => {
          const drawnFeatures = [...get().drawnFeatures];
          drawnFeatures.splice(index, 1);
          set({ drawnFeatures });
        },

        setDrawnBbox: (bbox) => set({ drawnBbox: bbox }),

        setLoading: (loading) => set({ isLoading: loading }),

        setBounds: (bounds) => set({ currentBounds: bounds }),

        reset: () => set(initialState),
      }),
      {
        name: 'bims-map-store',
        partialize: (state) => ({
          center: state.center,
          zoom: state.zoom,
          visibleLayerIds: state.visibleLayerIds,
        }),
      }
    ),
    { name: 'MapStore' }
  )
);

export default useMapStore;
