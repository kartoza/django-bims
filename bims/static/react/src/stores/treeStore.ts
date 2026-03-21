/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Zustand store for phylogenetic tree state management.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface TreeNode {
  id: number;
  name: string;
  rank: string;
  children: TreeNode[];
  parentId?: number;
  isLoading?: boolean;
  isExpanded?: boolean;
  hasChildren?: boolean;
  gbifKey?: number;
  canonicalName?: string;
  scientificName?: string;
  taxonomicStatus?: string;
}

export interface Transform {
  x: number;
  y: number;
  scale: number;
}

export interface TreeState {
  // Tree data
  rootNodes: TreeNode[];
  loadedNodeIds: Set<number>;
  expandedNodeIds: Set<number>;
  selectedNodeId: number | null;
  highlightedNodeIds: Set<number>;

  // Pan/Zoom state
  transform: Transform;
  isDragging: boolean;

  // Search state
  searchQuery: string;
  searchResults: number[];

  // Loading state
  isLoadingRoot: boolean;
  loadingNodeIds: Set<number>;

  // Actions - Tree data
  setRootNodes: (nodes: TreeNode[]) => void;
  addChildrenToNode: (parentId: number, children: TreeNode[]) => void;
  toggleNodeExpanded: (nodeId: number) => void;
  expandNode: (nodeId: number) => void;
  collapseNode: (nodeId: number) => void;
  collapseAll: () => void;
  expandAll: () => void;
  selectNode: (nodeId: number | null) => void;
  highlightNodes: (nodeIds: number[]) => void;
  clearHighlights: () => void;

  // Actions - Pan/Zoom
  setTransform: (transform: Transform) => void;
  pan: (dx: number, dy: number) => void;
  zoom: (scale: number, centerX?: number, centerY?: number) => void;
  resetView: () => void;
  fitToView: (width: number, height: number, treeWidth: number, treeHeight: number) => void;
  setDragging: (isDragging: boolean) => void;

  // Actions - Search
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: number[]) => void;

  // Actions - Loading
  setLoadingRoot: (loading: boolean) => void;
  setNodeLoading: (nodeId: number, loading: boolean) => void;
  markNodeLoaded: (nodeId: number) => void;

  // Utility
  getNode: (nodeId: number) => TreeNode | undefined;
  reset: () => void;
}

const MIN_SCALE = 0.1;
const MAX_SCALE = 4;

const initialState = {
  rootNodes: [] as TreeNode[],
  loadedNodeIds: new Set<number>(),
  expandedNodeIds: new Set<number>(),
  selectedNodeId: null as number | null,
  highlightedNodeIds: new Set<number>(),
  transform: { x: 50, y: 50, scale: 1 } as Transform,
  isDragging: false,
  searchQuery: '',
  searchResults: [] as number[],
  isLoadingRoot: false,
  loadingNodeIds: new Set<number>(),
};

// Helper to find a node in the tree
const findNode = (nodes: TreeNode[], nodeId: number): TreeNode | undefined => {
  for (const node of nodes) {
    if (node.id === nodeId) return node;
    if (node.children?.length) {
      const found = findNode(node.children, nodeId);
      if (found) return found;
    }
  }
  return undefined;
};

// Helper to update a node in the tree
const updateNodeInTree = (
  nodes: TreeNode[],
  nodeId: number,
  updater: (node: TreeNode) => TreeNode
): TreeNode[] => {
  return nodes.map((node) => {
    if (node.id === nodeId) {
      return updater(node);
    }
    if (node.children?.length) {
      return {
        ...node,
        children: updateNodeInTree(node.children, nodeId, updater),
      };
    }
    return node;
  });
};

export const useTreeStore = create<TreeState>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setRootNodes: (nodes) =>
        set({
          rootNodes: nodes,
          loadedNodeIds: new Set(nodes.map((n) => n.id)),
        }),

      addChildrenToNode: (parentId, children) =>
        set((state) => ({
          rootNodes: updateNodeInTree(state.rootNodes, parentId, (node) => ({
            ...node,
            children,
            hasChildren: children.length > 0,
          })),
          loadedNodeIds: new Set([
            ...state.loadedNodeIds,
            ...children.map((c) => c.id),
          ]),
        })),

      toggleNodeExpanded: (nodeId) =>
        set((state) => {
          const newExpanded = new Set(state.expandedNodeIds);
          if (newExpanded.has(nodeId)) {
            newExpanded.delete(nodeId);
          } else {
            newExpanded.add(nodeId);
          }
          return { expandedNodeIds: newExpanded };
        }),

      expandNode: (nodeId) =>
        set((state) => ({
          expandedNodeIds: new Set([...state.expandedNodeIds, nodeId]),
        })),

      collapseNode: (nodeId) =>
        set((state) => {
          const newExpanded = new Set(state.expandedNodeIds);
          newExpanded.delete(nodeId);
          return { expandedNodeIds: newExpanded };
        }),

      collapseAll: () => set({ expandedNodeIds: new Set() }),

      expandAll: () =>
        set((state) => {
          const allIds = new Set<number>();
          const collectIds = (nodes: TreeNode[]) => {
            nodes.forEach((node) => {
              if (node.children?.length) {
                allIds.add(node.id);
                collectIds(node.children);
              }
            });
          };
          collectIds(state.rootNodes);
          return { expandedNodeIds: allIds };
        }),

      selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

      highlightNodes: (nodeIds) =>
        set({ highlightedNodeIds: new Set(nodeIds) }),

      clearHighlights: () => set({ highlightedNodeIds: new Set() }),

      setTransform: (transform) => set({ transform }),

      pan: (dx, dy) =>
        set((state) => ({
          transform: {
            ...state.transform,
            x: state.transform.x + dx,
            y: state.transform.y + dy,
          },
        })),

      zoom: (newScale, centerX, centerY) =>
        set((state) => {
          const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, newScale));

          // If center point provided, zoom towards that point
          if (centerX !== undefined && centerY !== undefined) {
            const scaleRatio = scale / state.transform.scale;
            const newX =
              centerX - (centerX - state.transform.x) * scaleRatio;
            const newY =
              centerY - (centerY - state.transform.y) * scaleRatio;
            return { transform: { x: newX, y: newY, scale } };
          }

          return { transform: { ...state.transform, scale } };
        }),

      resetView: () =>
        set({ transform: { x: 50, y: 50, scale: 1 } }),

      fitToView: (containerWidth, containerHeight, treeWidth, treeHeight) =>
        set(() => {
          const padding = 100;
          const scaleX = (containerWidth - padding) / treeWidth;
          const scaleY = (containerHeight - padding) / treeHeight;
          const scale = Math.min(scaleX, scaleY, 1);
          const x = (containerWidth - treeWidth * scale) / 2;
          const y = (containerHeight - treeHeight * scale) / 2;
          return { transform: { x, y, scale } };
        }),

      setDragging: (isDragging) => set({ isDragging }),

      setSearchQuery: (query) => set({ searchQuery: query }),

      setSearchResults: (results) =>
        set({
          searchResults: results,
          highlightedNodeIds: new Set(results),
        }),

      setLoadingRoot: (loading) => set({ isLoadingRoot: loading }),

      setNodeLoading: (nodeId, loading) =>
        set((state) => {
          const newLoading = new Set(state.loadingNodeIds);
          if (loading) {
            newLoading.add(nodeId);
          } else {
            newLoading.delete(nodeId);
          }
          return { loadingNodeIds: newLoading };
        }),

      markNodeLoaded: (nodeId) =>
        set((state) => ({
          loadedNodeIds: new Set([...state.loadedNodeIds, nodeId]),
        })),

      getNode: (nodeId) => findNode(get().rootNodes, nodeId),

      reset: () => set(initialState),
    }),
    { name: 'TreeStore' }
  )
);

export default useTreeStore;
