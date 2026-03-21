/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for lazy loading tree data from the API.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useCallback, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import { useTreeStore, TreeNode } from '../stores/treeStore';

export interface UseTreeDataOptions {
  taxonGroupId?: number;
  autoLoad?: boolean;
}

export interface UseTreeDataReturn {
  loadRootNodes: () => Promise<void>;
  loadNodeChildren: (nodeId: number) => Promise<void>;
  searchNodes: (query: string) => Promise<void>;
  isLoading: boolean;
  isLoadingNode: (nodeId: number) => boolean;
  error: string | null;
}

const useTreeData = (options: UseTreeDataOptions = {}): UseTreeDataReturn => {
  const { taxonGroupId, autoLoad = true } = options;

  const errorRef = useRef<string | null>(null);

  const {
    setRootNodes,
    addChildrenToNode,
    setLoadingRoot,
    setNodeLoading,
    markNodeLoaded,
    loadedNodeIds,
    loadingNodeIds,
    isLoadingRoot,
    expandNode,
    setSearchQuery,
    setSearchResults,
    highlightNodes,
  } = useTreeStore();

  // Load root nodes (taxa without parents)
  const loadRootNodes = useCallback(async () => {
    setLoadingRoot(true);
    errorRef.current = null;

    try {
      const params: Record<string, unknown> = {
        has_parent: false,
        page_size: 100,
      };
      if (taxonGroupId) params.taxon_group = taxonGroupId;

      const response = await apiClient.get('taxa/', { params });
      const rootTaxa = response.data?.data || [];

      const treeNodes: TreeNode[] = rootTaxa.map(
        (taxon: {
          id: number;
          canonical_name?: string;
          scientific_name: string;
          rank: string;
          gbif_key?: number;
          taxonomic_status?: string;
        }) => ({
          id: taxon.id,
          name: taxon.canonical_name || taxon.scientific_name,
          rank: taxon.rank,
          children: [],
          hasChildren: true, // Assume all root nodes have children
          gbifKey: taxon.gbif_key,
          canonicalName: taxon.canonical_name,
          scientificName: taxon.scientific_name,
          taxonomicStatus: taxon.taxonomic_status,
        })
      );

      setRootNodes(treeNodes);
    } catch (error) {
      console.error('Failed to load root nodes:', error);
      errorRef.current = 'Failed to load taxonomy tree';
    } finally {
      setLoadingRoot(false);
    }
  }, [taxonGroupId, setRootNodes, setLoadingRoot]);

  // Load children for a specific node
  const loadNodeChildren = useCallback(
    async (nodeId: number) => {
      // Skip if already loaded or currently loading
      if (loadingNodeIds.has(nodeId)) return;

      setNodeLoading(nodeId, true);
      errorRef.current = null;

      try {
        const response = await apiClient.get(`taxa/${nodeId}/tree/`, {
          params: { direction: 'down', depth: 1 },
        });

        const data = response.data?.data;
        const children: TreeNode[] = [];

        // Ranks that are typically leaf nodes (no children expected)
        const leafRanks = ['SPECIES', 'SUBSPECIES', 'VARIETY', 'FORM'];

        if (data?.children) {
          data.children.forEach(
            (child: {
              id: number;
              name?: string;
              canonical_name?: string;
              scientific_name?: string;
              rank: string;
              children?: unknown[];
              has_children?: boolean;
              gbif_key?: number;
              taxonomic_status?: string;
            }) => {
              // Assume non-leaf ranks have children unless API explicitly says otherwise
              const isLeafRank = leafRanks.includes(child.rank?.toUpperCase());
              const hasChildren = child.has_children !== undefined
                ? child.has_children
                : !isLeafRank; // Assume non-leaf ranks have children

              children.push({
                id: child.id,
                name: child.name || child.canonical_name || child.scientific_name || '',
                rank: child.rank,
                children: [],
                hasChildren,
                parentId: nodeId,
                gbifKey: child.gbif_key,
                canonicalName: child.canonical_name,
                scientificName: child.scientific_name,
                taxonomicStatus: child.taxonomic_status,
              });
            }
          );
        }

        addChildrenToNode(nodeId, children);
        markNodeLoaded(nodeId);
        expandNode(nodeId);
      } catch (error) {
        console.error(`Failed to load children for node ${nodeId}:`, error);
        errorRef.current = 'Failed to load children';
      } finally {
        setNodeLoading(nodeId, false);
      }
    },
    [
      loadingNodeIds,
      setNodeLoading,
      addChildrenToNode,
      markNodeLoaded,
      expandNode,
    ]
  );

  // Search nodes by name
  const searchNodes = useCallback(
    async (query: string) => {
      setSearchQuery(query);

      if (!query.trim()) {
        setSearchResults([]);
        return;
      }

      try {
        const params: Record<string, unknown> = {
          search: query,
          page_size: 50,
        };
        if (taxonGroupId) params.taxon_group = taxonGroupId;

        const response = await apiClient.get('taxa/', { params });
        const results = response.data?.data || [];

        const matchingIds = results.map(
          (taxon: { id: number }) => taxon.id
        );
        setSearchResults(matchingIds);
        highlightNodes(matchingIds);
      } catch (error) {
        console.error('Search failed:', error);
        setSearchResults([]);
      }
    },
    [taxonGroupId, setSearchQuery, setSearchResults, highlightNodes]
  );

  // Check if a specific node is loading
  const isLoadingNode = useCallback(
    (nodeId: number) => loadingNodeIds.has(nodeId),
    [loadingNodeIds]
  );

  // Auto-load root nodes on mount
  useEffect(() => {
    if (autoLoad) {
      loadRootNodes();
    }
  }, [autoLoad, taxonGroupId, loadRootNodes]);

  return {
    loadRootNodes,
    loadNodeChildren,
    searchNodes,
    isLoading: isLoadingRoot,
    isLoadingNode,
    error: errorRef.current,
  };
};

export default useTreeData;
