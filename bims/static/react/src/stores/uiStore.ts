/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Zustand store for UI state management.
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export type PanelType = 'search' | 'site' | 'siteDetail' | 'taxon' | 'taxonDetail' | 'record' | 'legend' | null;
export type ModalType = 'addSite' | 'addRecord' | 'validation' | 'download' | 'settings' | null;

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

interface UIState {
  // Panel state
  activePanel: PanelType;
  panelWidth: number;
  isPanelCollapsed: boolean;

  // Modal state
  activeModal: ModalType;
  modalData: Record<string, unknown> | null;

  // Notifications
  notifications: Notification[];

  // Loading states
  globalLoading: boolean;
  loadingMessage: string | null;

  // User preferences
  sidebarPosition: 'left' | 'right';
  theme: 'light' | 'dark' | 'system';
  compactMode: boolean;

  // Selection context
  selectedEntityId: number | null;
  selectedEntityType: 'site' | 'record' | 'taxon' | null;

  // Actions
  setActivePanel: (panel: PanelType) => void;
  openPanel: (panel: PanelType) => void;
  togglePanel: (panel: PanelType) => void;
  closePanel: () => void;
  setPanelWidth: (width: number) => void;
  togglePanelCollapsed: () => void;

  openModal: (modal: ModalType, data?: Record<string, unknown>) => void;
  closeModal: () => void;

  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  setGlobalLoading: (loading: boolean, message?: string) => void;

  setSidebarPosition: (position: 'left' | 'right') => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleCompactMode: () => void;

  selectEntity: (id: number | null, type: 'site' | 'record' | 'taxon' | null) => void;
  clearSelection: () => void;

  reset: () => void;
}

const initialState = {
  activePanel: null as PanelType,
  panelWidth: 400,
  isPanelCollapsed: false,
  activeModal: null as ModalType,
  modalData: null,
  notifications: [] as Notification[],
  globalLoading: false,
  loadingMessage: null,
  sidebarPosition: 'left' as const,
  theme: 'light' as const,
  compactMode: false,
  selectedEntityId: null,
  selectedEntityType: null,
};

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        setActivePanel: (panel) =>
          set({
            activePanel: panel,
            isPanelCollapsed: false,
          }),

        openPanel: (panel) =>
          set({
            activePanel: panel,
            isPanelCollapsed: false,
          }),

        togglePanel: (panel) => {
          const current = get().activePanel;
          if (current === panel) {
            set({ isPanelCollapsed: !get().isPanelCollapsed });
          } else {
            set({ activePanel: panel, isPanelCollapsed: false });
          }
        },

        closePanel: () =>
          set({
            activePanel: null,
            isPanelCollapsed: false,
          }),

        setPanelWidth: (width) => set({ panelWidth: width }),

        togglePanelCollapsed: () =>
          set({ isPanelCollapsed: !get().isPanelCollapsed }),

        openModal: (modal, data = null) =>
          set({
            activeModal: modal,
            modalData: data,
          }),

        closeModal: () =>
          set({
            activeModal: null,
            modalData: null,
          }),

        addNotification: (notification) => {
          const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
          const newNotification: Notification = {
            ...notification,
            id,
            duration: notification.duration ?? 5000,
          };

          set({
            notifications: [...get().notifications, newNotification],
          });

          // Auto-remove after duration
          if (newNotification.duration && newNotification.duration > 0) {
            setTimeout(() => {
              get().removeNotification(id);
            }, newNotification.duration);
          }
        },

        removeNotification: (id) =>
          set({
            notifications: get().notifications.filter((n) => n.id !== id),
          }),

        clearNotifications: () => set({ notifications: [] }),

        setGlobalLoading: (loading, message = null) =>
          set({
            globalLoading: loading,
            loadingMessage: message,
          }),

        setSidebarPosition: (position) => set({ sidebarPosition: position }),

        setTheme: (theme) => set({ theme }),

        toggleCompactMode: () => set({ compactMode: !get().compactMode }),

        selectEntity: (id, type) =>
          set({
            selectedEntityId: id,
            selectedEntityType: type,
            activePanel: type ?? get().activePanel,
          }),

        clearSelection: () =>
          set({
            selectedEntityId: null,
            selectedEntityType: null,
          }),

        reset: () => set(initialState),
      }),
      {
        name: 'bims-ui-store',
        partialize: (state) => ({
          sidebarPosition: state.sidebarPosition,
          theme: state.theme,
          compactMode: state.compactMode,
          panelWidth: state.panelWidth,
        }),
      }
    ),
    { name: 'UIStore' }
  )
);

export default useUIStore;
