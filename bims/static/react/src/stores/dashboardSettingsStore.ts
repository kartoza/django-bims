/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Zustand store for dashboard settings management.
 * Persists to localStorage for user preferences.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface DashboardWidget {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  position: number;
}

export interface BrandingSettings {
  siteName: string;
  siteDescription: string;
  logoUrl: string;
  faviconUrl: string;
  primaryColor: string;
  bannerImage: string;
}

export interface LandingPageSettings {
  showStats: boolean;
  showPartners: boolean;
  showEcosystems: boolean;
  heroTitle: string;
  heroSubtitle: string;
  ctaButtonText: string;
  ctaButtonUrl: string;
}

export interface MapSettings {
  defaultLatitude: number;
  defaultLongitude: number;
  defaultZoom: number;
  defaultBaseMap: 'osm' | 'satellite' | 'terrain' | 'dark';
  enableClustering: boolean;
  showScaleBar: boolean;
  enableDrawingTools: boolean;
  showMiniMap: boolean;
}

// All available widget types that can be added
export const AVAILABLE_WIDGET_TYPES = [
  { id: 'species-stats', name: 'Species Statistics', type: 'stats', description: 'Show total species counts and breakdown' },
  { id: 'recent-records', name: 'Recent Records', type: 'table', description: 'Display recently added biological records' },
  { id: 'conservation-chart', name: 'Conservation Status Chart', type: 'chart', description: 'Pie chart of IUCN conservation statuses' },
  { id: 'endemism-chart', name: 'Endemism Chart', type: 'chart', description: 'Distribution of endemic vs alien species' },
  { id: 'map-overview', name: 'Map Overview', type: 'map', description: 'Mini map showing site distributions' },
  { id: 'recent-activity', name: 'Recent Activity', type: 'activity', description: 'Timeline of recent user actions' },
  { id: 'taxon-groups', name: 'Taxon Groups Summary', type: 'stats', description: 'Records per taxon group' },
  { id: 'validation-queue', name: 'Validation Queue', type: 'table', description: 'Pending items requiring validation' },
  { id: 'ecosystem-breakdown', name: 'Ecosystem Breakdown', type: 'chart', description: 'Sites by ecosystem type' },
  { id: 'data-quality', name: 'Data Quality Metrics', type: 'stats', description: 'Data completeness and quality scores' },
];

interface DashboardSettingsState {
  branding: BrandingSettings;
  landingPage: LandingPageSettings;
  mapSettings: MapSettings;
  widgets: DashboardWidget[];

  // Actions
  setBranding: (branding: Partial<BrandingSettings>) => void;
  setLandingPage: (settings: Partial<LandingPageSettings>) => void;
  setMapSettings: (settings: Partial<MapSettings>) => void;
  setWidgets: (widgets: DashboardWidget[]) => void;
  addWidget: (widgetTypeId: string) => void;
  removeWidget: (widgetId: string) => void;
  toggleWidget: (widgetId: string) => void;
  reorderWidgets: (widgets: DashboardWidget[]) => void;
  moveWidgetUp: (widgetId: string) => void;
  moveWidgetDown: (widgetId: string) => void;
  resetToDefaults: () => void;
}

const DEFAULT_BRANDING: BrandingSettings = {
  siteName: 'BIMS',
  siteDescription: 'Biodiversity Information Management System',
  logoUrl: '/static/img/logo.png',
  faviconUrl: '/static/img/favicon.ico',
  primaryColor: '#3182CE',
  bannerImage: '/static/img/landing_page_banner.jpeg',
};

const DEFAULT_LANDING_PAGE: LandingPageSettings = {
  showStats: true,
  showPartners: true,
  showEcosystems: true,
  heroTitle: 'Biodiversity Information Management System',
  heroSubtitle: 'Explore, analyze, and manage biodiversity data.',
  ctaButtonText: 'Explore Map',
  ctaButtonUrl: '/new/map',
};

const DEFAULT_MAP_SETTINGS: MapSettings = {
  defaultLatitude: -30.5595,
  defaultLongitude: 22.9375,
  defaultZoom: 5,
  defaultBaseMap: 'osm',
  enableClustering: true,
  showScaleBar: true,
  enableDrawingTools: true,
  showMiniMap: false,
};

const DEFAULT_WIDGETS: DashboardWidget[] = [
  { id: 'species-stats', name: 'Species Statistics', type: 'stats', enabled: true, position: 1 },
  { id: 'recent-records', name: 'Recent Records', type: 'table', enabled: true, position: 2 },
  { id: 'conservation-chart', name: 'Conservation Status Chart', type: 'chart', enabled: true, position: 3 },
  { id: 'endemism-chart', name: 'Endemism Chart', type: 'chart', enabled: true, position: 4 },
  { id: 'map-overview', name: 'Map Overview', type: 'map', enabled: true, position: 5 },
];

export const useDashboardSettingsStore = create<DashboardSettingsState>()(
  devtools(
    persist(
      (set, get) => ({
        branding: DEFAULT_BRANDING,
        landingPage: DEFAULT_LANDING_PAGE,
        mapSettings: DEFAULT_MAP_SETTINGS,
        widgets: DEFAULT_WIDGETS,

        setBranding: (updates) =>
          set((state) => ({
            branding: { ...state.branding, ...updates },
          })),

        setLandingPage: (updates) =>
          set((state) => ({
            landingPage: { ...state.landingPage, ...updates },
          })),

        setMapSettings: (updates) =>
          set((state) => ({
            mapSettings: { ...state.mapSettings, ...updates },
          })),

        setWidgets: (widgets) => set({ widgets }),

        addWidget: (widgetTypeId) => {
          const widgetType = AVAILABLE_WIDGET_TYPES.find((wt) => wt.id === widgetTypeId);
          if (!widgetType) return;

          const widgets = get().widgets;
          if (widgets.some((w) => w.id === widgetTypeId)) return; // Already exists

          const newWidget: DashboardWidget = {
            id: widgetType.id,
            name: widgetType.name,
            type: widgetType.type,
            enabled: true,
            position: widgets.length + 1,
          };

          set({ widgets: [...widgets, newWidget] });
        },

        removeWidget: (widgetId) => {
          const widgets = get().widgets.filter((w) => w.id !== widgetId);
          // Reorder positions
          const reordered = widgets.map((w, idx) => ({ ...w, position: idx + 1 }));
          set({ widgets: reordered });
        },

        toggleWidget: (widgetId) => {
          set((state) => ({
            widgets: state.widgets.map((w) =>
              w.id === widgetId ? { ...w, enabled: !w.enabled } : w
            ),
          }));
        },

        reorderWidgets: (widgets) => set({ widgets }),

        moveWidgetUp: (widgetId) => {
          const widgets = [...get().widgets].sort((a, b) => a.position - b.position);
          const index = widgets.findIndex((w) => w.id === widgetId);
          if (index <= 0) return;

          // Swap positions
          const temp = widgets[index].position;
          widgets[index].position = widgets[index - 1].position;
          widgets[index - 1].position = temp;

          set({ widgets });
        },

        moveWidgetDown: (widgetId) => {
          const widgets = [...get().widgets].sort((a, b) => a.position - b.position);
          const index = widgets.findIndex((w) => w.id === widgetId);
          if (index < 0 || index >= widgets.length - 1) return;

          // Swap positions
          const temp = widgets[index].position;
          widgets[index].position = widgets[index + 1].position;
          widgets[index + 1].position = temp;

          set({ widgets });
        },

        resetToDefaults: () =>
          set({
            branding: DEFAULT_BRANDING,
            landingPage: DEFAULT_LANDING_PAGE,
            mapSettings: DEFAULT_MAP_SETTINGS,
            widgets: DEFAULT_WIDGETS,
          }),
      }),
      {
        name: 'bims-dashboard-settings',
      }
    ),
    { name: 'DashboardSettingsStore' }
  )
);

export default useDashboardSettingsStore;
