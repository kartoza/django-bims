/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Zustand store for context layers management.
 * Persists to localStorage and syncs with the map legend.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface ContextLayer {
  id: string;
  name: string;
  type: 'wms' | 'wmts' | 'xyz' | 'geojson' | 'vector';
  url: string;
  layerName?: string;
  enabled: boolean;
  visible: boolean;
  opacity: number;
  category: string;
  attribution?: string;
  description?: string;
  order: number;
}

interface ContextLayersState {
  layers: ContextLayer[];
  isLoading: boolean;
  error: string | null;

  // Actions
  setLayers: (layers: ContextLayer[]) => void;
  addLayer: (layer: Omit<ContextLayer, 'id'>) => void;
  updateLayer: (id: string, updates: Partial<ContextLayer>) => void;
  deleteLayer: (id: string) => void;
  toggleEnabled: (id: string) => void;
  toggleVisibility: (id: string) => void;
  setOpacity: (id: string, opacity: number) => void;
  reorderLayers: (layers: ContextLayer[]) => void;
  loadFromApi: () => Promise<void>;
}

// Default layers for initial state
const DEFAULT_CONTEXT_LAYERS: ContextLayer[] = [
  {
    id: '1',
    name: 'OpenStreetMap',
    type: 'xyz',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    enabled: true,
    visible: false,
    opacity: 1,
    category: 'Base Maps',
    attribution: '© OpenStreetMap contributors',
    order: 1,
  },
  {
    id: '2',
    name: 'Satellite Imagery',
    type: 'xyz',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    enabled: true,
    visible: false,
    opacity: 1,
    category: 'Base Maps',
    attribution: '© Esri',
    order: 2,
  },
  {
    id: '3',
    name: 'Rivers & Water Bodies',
    type: 'wms',
    url: 'https://maps.kartoza.com/geoserver/wms',
    layerName: 'rivers',
    enabled: true,
    visible: false,
    opacity: 0.8,
    category: 'Hydrology',
    description: 'Major rivers and water bodies of South Africa',
    order: 3,
  },
  {
    id: '4',
    name: 'Protected Areas',
    type: 'wms',
    url: 'https://maps.kartoza.com/geoserver/wms',
    layerName: 'protected_areas',
    enabled: true,
    visible: false,
    opacity: 0.7,
    category: 'Conservation',
    description: 'National parks and protected areas',
    order: 4,
  },
  {
    id: '5',
    name: 'Catchment Boundaries',
    type: 'geojson',
    url: '/api/v1/boundaries/catchments/',
    enabled: false,
    visible: false,
    opacity: 0.6,
    category: 'Administrative',
    description: 'River catchment boundaries',
    order: 5,
  },
  {
    id: '6',
    name: 'Provincial Boundaries',
    type: 'geojson',
    url: '/api/v1/boundaries/provinces/',
    enabled: true,
    visible: false,
    opacity: 0.7,
    category: 'Administrative',
    description: 'South African provincial boundaries',
    order: 6,
  },
];

export const useContextLayersStore = create<ContextLayersState>()(
  devtools(
    persist(
      (set, get) => ({
        layers: DEFAULT_CONTEXT_LAYERS,
        isLoading: false,
        error: null,

        setLayers: (layers) => set({ layers }),

        addLayer: (layer) => {
          const newLayer: ContextLayer = {
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

        loadFromApi: async () => {
          set({ isLoading: true, error: null });
          try {
            const response = await fetch('/api/list-non-biodiversity/');
            if (response.ok) {
              const data = await response.json();
              // Merge API layers with existing layers (API layers take precedence)
              const apiLayers: ContextLayer[] = data.map((item: any, index: number) => ({
                id: `api-${item.id}`,
                name: item.name,
                type: 'wms' as const,
                url: item.wms_url,
                layerName: item.wms_layer_name,
                enabled: true,
                visible: item.default_visibility || false,
                opacity: 0.7,
                category: 'Custom',
                order: 100 + index,
              }));

              // Keep existing non-API layers and add API layers
              const existingLayers = get().layers.filter((l) => !l.id.startsWith('api-'));
              set({ layers: [...existingLayers, ...apiLayers], isLoading: false });
            } else {
              set({ isLoading: false });
            }
          } catch (error) {
            set({ isLoading: false, error: 'Failed to load layers from API' });
          }
        },
      }),
      {
        name: 'bims-context-layers',
      }
    ),
    { name: 'ContextLayersStore' }
  )
);

export default useContextLayersStore;
