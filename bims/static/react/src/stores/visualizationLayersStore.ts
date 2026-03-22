/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Zustand store for visualization layers management.
 * Persists to localStorage and syncs with the map.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface VisualizationLayer {
  id: string;
  name: string;
  type: 'point' | 'polygon' | 'heatmap' | 'cluster';
  source: string;
  enabled: boolean;
  visible: boolean;
  opacity: number;
  minZoom: number;
  maxZoom: number;
  style: {
    color: string;
    fillColor?: string;
    radius?: number;
  };
  order: number;
}

interface VisualizationLayersState {
  layers: VisualizationLayer[];
  isLoading: boolean;
  error: string | null;

  // Actions
  setLayers: (layers: VisualizationLayer[]) => void;
  addLayer: (layer: Omit<VisualizationLayer, 'id'>) => void;
  updateLayer: (id: string, updates: Partial<VisualizationLayer>) => void;
  deleteLayer: (id: string) => void;
  toggleEnabled: (id: string) => void;
  toggleVisibility: (id: string) => void;
  setOpacity: (id: string, opacity: number) => void;
  reorderLayers: (layers: VisualizationLayer[]) => void;
}

// Default visualization layers
const DEFAULT_VISUALIZATION_LAYERS: VisualizationLayer[] = [
  {
    id: '1',
    name: 'Location Sites',
    type: 'cluster',
    source: 'sites',
    enabled: true,
    visible: true,
    opacity: 100,
    minZoom: 0,
    maxZoom: 22,
    style: { color: '#3182CE', fillColor: '#3182CE', radius: 8 },
    order: 1,
  },
  {
    id: '2',
    name: 'Fish Records',
    type: 'point',
    source: 'fish_records',
    enabled: true,
    visible: false,
    opacity: 80,
    minZoom: 5,
    maxZoom: 22,
    style: { color: '#38A169', fillColor: '#38A169', radius: 6 },
    order: 2,
  },
  {
    id: '3',
    name: 'Species Heatmap',
    type: 'heatmap',
    source: 'all_records',
    enabled: false,
    visible: false,
    opacity: 60,
    minZoom: 0,
    maxZoom: 10,
    style: { color: '#E53E3E' },
    order: 3,
  },
  {
    id: '4',
    name: 'River Catchments',
    type: 'polygon',
    source: 'catchments',
    enabled: true,
    visible: false,
    opacity: 50,
    minZoom: 0,
    maxZoom: 22,
    style: { color: '#0BC5EA', fillColor: '#0BC5EA' },
    order: 4,
  },
];

export const useVisualizationLayersStore = create<VisualizationLayersState>()(
  devtools(
    persist(
      (set, get) => ({
        layers: DEFAULT_VISUALIZATION_LAYERS,
        isLoading: false,
        error: null,

        setLayers: (layers) => set({ layers }),

        addLayer: (layer) => {
          const newLayer: VisualizationLayer = {
            ...layer,
            id: Date.now().toString(),
          };
          set((state) => ({ layers: [...state.layers, newLayer] }));
        },

        updateLayer: (id, updates) => {
          set((state) => ({
            layers: state.layers.map((layer) =>
              layer.id === id ? { ...layer, ...updates } : layer
            ),
          }));
        },

        deleteLayer: (id) => {
          set((state) => ({
            layers: state.layers.filter((layer) => layer.id !== id),
          }));
        },

        toggleEnabled: (id) => {
          set((state) => ({
            layers: state.layers.map((layer) =>
              layer.id === id ? { ...layer, enabled: !layer.enabled } : layer
            ),
          }));
        },

        toggleVisibility: (id) => {
          set((state) => ({
            layers: state.layers.map((layer) =>
              layer.id === id ? { ...layer, visible: !layer.visible } : layer
            ),
          }));
        },

        setOpacity: (id, opacity) => {
          set((state) => ({
            layers: state.layers.map((layer) =>
              layer.id === id ? { ...layer, opacity } : layer
            ),
          }));
        },

        reorderLayers: (layers) => set({ layers }),
      }),
      {
        name: 'bims-visualization-layers',
      }
    ),
    { name: 'VisualizationLayersStore' }
  )
);

export default useVisualizationLayersStore;
