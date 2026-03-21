/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for calculating D3 tree layout for phylogenetic dendrograms.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useMemo } from 'react';
import * as d3 from 'd3';
import type { HierarchyNode, HierarchyPointLink } from 'd3';
import { TreeNode } from '../stores/treeStore';

export interface LayoutNode {
  id: number;
  name: string;
  rank: string;
  x: number;
  y: number;
  depth: number;
  isLeaf: boolean;
  hasChildren: boolean;
  children: LayoutNode[];
  parent?: LayoutNode;
  data: TreeNode;
}

export interface LayoutLink {
  source: LayoutNode;
  target: LayoutNode;
}

export interface TreeLayoutResult {
  nodes: LayoutNode[];
  links: LayoutLink[];
  width: number;
  height: number;
}

export interface UseTreeLayoutOptions {
  nodeWidth?: number;
  nodeHeight?: number;
  horizontalSpacing?: number;
  verticalSpacing?: number;
}

const useTreeLayout = (
  rootNodes: TreeNode[],
  expandedNodeIds: Set<number>,
  options: UseTreeLayoutOptions = {}
): TreeLayoutResult => {
  const {
    nodeWidth = 200,
    nodeHeight = 30,
    horizontalSpacing = 250,
    verticalSpacing = 40,
  } = options;

  return useMemo(() => {
    if (!rootNodes.length) {
      return { nodes: [], links: [], width: 0, height: 0 };
    }

    // Create a virtual root if we have multiple root nodes
    const virtualRoot: TreeNode =
      rootNodes.length === 1
        ? rootNodes[0]
        : {
            id: -1,
            name: 'Root',
            rank: 'ROOT',
            children: rootNodes,
          };

    // Filter tree to only include expanded nodes and their visible children
    const filterExpanded = (
      node: TreeNode,
      depth: number = 0
    ): TreeNode | null => {
      // Always include the node itself
      const visibleChildren: TreeNode[] = [];

      // Only process children if this node is expanded (or it's the virtual root)
      if (
        node.children?.length &&
        (expandedNodeIds.has(node.id) || node.id === -1 || depth === 0)
      ) {
        for (const child of node.children) {
          const filtered = filterExpanded(child, depth + 1);
          if (filtered) {
            visibleChildren.push(filtered);
          }
        }
      }

      return {
        ...node,
        children: visibleChildren,
        hasChildren: node.children?.length > 0,
      };
    };

    const filteredTree = filterExpanded(virtualRoot);
    if (!filteredTree) {
      return { nodes: [], links: [], width: 0, height: 0 };
    }

    // Create D3 hierarchy
    const hierarchy = d3.hierarchy<TreeNode>(filteredTree, (d: TreeNode) => d.children);

    // Count visible leaves for proper spacing
    const leafCount = hierarchy.leaves().length;

    // Use cluster layout for dendrogram-style tree
    const treeLayout = d3.cluster<TreeNode>().nodeSize([verticalSpacing, horizontalSpacing]);

    // Apply layout
    const root = treeLayout(hierarchy);

    // Collect all nodes and links
    const allNodes: LayoutNode[] = [];
    const allLinks: LayoutLink[] = [];

    let minY = Infinity;
    let maxY = -Infinity;
    let maxX = -Infinity;

    // Process nodes - swap x/y for horizontal orientation
    root.each((d: HierarchyNode<TreeNode> & { x: number; y: number }) => {
      // Skip virtual root if we have multiple roots
      if (d.data.id === -1) return;

      const layoutNode: LayoutNode = {
        id: d.data.id,
        name: d.data.name,
        rank: d.data.rank,
        x: d.y, // Swap x and y for horizontal layout
        y: d.x,
        depth: d.depth,
        isLeaf: !d.children || d.children.length === 0,
        hasChildren: (d.data.children?.length || 0) > 0,
        children: [],
        data: d.data,
      };

      minY = Math.min(minY, layoutNode.y);
      maxY = Math.max(maxY, layoutNode.y);
      maxX = Math.max(maxX, layoutNode.x);

      allNodes.push(layoutNode);
    });

    // Normalize y coordinates to start from 0
    const yOffset = minY < 0 ? -minY + verticalSpacing : verticalSpacing;
    allNodes.forEach((node) => {
      node.y += yOffset;
    });

    // Create node lookup for links
    const nodeMap = new Map<number, LayoutNode>();
    allNodes.forEach((node) => nodeMap.set(node.id, node));

    // Process links
    root.links().forEach((link: HierarchyPointLink<TreeNode>) => {
      // Skip links from/to virtual root
      if (link.source.data.id === -1 || link.target.data.id === -1) return;

      const sourceNode = nodeMap.get(link.source.data.id);
      const targetNode = nodeMap.get(link.target.data.id);

      if (sourceNode && targetNode) {
        allLinks.push({
          source: sourceNode,
          target: targetNode,
        });
      }
    });

    // Calculate tree dimensions
    const width = maxX + nodeWidth + horizontalSpacing;
    const height = maxY - minY + yOffset + verticalSpacing * 2;

    return {
      nodes: allNodes,
      links: allLinks,
      width,
      height,
    };
  }, [
    rootNodes,
    expandedNodeIds,
    nodeWidth,
    nodeHeight,
    horizontalSpacing,
    verticalSpacing,
  ]);
};

export default useTreeLayout;
