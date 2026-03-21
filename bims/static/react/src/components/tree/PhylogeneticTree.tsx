/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Main phylogenetic tree component with pan/zoom canvas.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useCallback, useMemo, useState } from 'react';
import {
  Box,
  Center,
  Spinner,
  Text,
  VStack,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { useTreeStore } from '../../stores/treeStore';
import useTreeLayout from '../../hooks/useTreeLayout';
import useTreeData from '../../hooks/useTreeData';
import usePanZoom from '../../hooks/usePanZoom';
import TreeNode from './TreeNode';
import TreeLink from './TreeLink';
import TreeControls from './TreeControls';
import TreeLegend from './TreeLegend';

export interface PhylogeneticTreeProps {
  taxonGroupId?: number;
  onNodeSelect?: (nodeId: number) => void;
  onNodeDoubleClick?: (nodeId: number) => void;
  showLegend?: boolean;
  showControls?: boolean;
  height?: string;
}

// CSS for spinner animation
const spinnerKeyframes = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const PhylogeneticTree: React.FC<PhylogeneticTreeProps> = ({
  taxonGroupId,
  onNodeSelect,
  onNodeDoubleClick,
  showLegend = true,
  showControls = true,
  height = '600px',
}) => {
  const {
    rootNodes,
    expandedNodeIds,
    selectedNodeId,
    highlightedNodeIds,
    loadingNodeIds,
    collapseAll,
    expandAll,
    selectNode,
    toggleNodeExpanded,
    reset,
  } = useTreeStore();

  const {
    loadRootNodes,
    loadNodeChildren,
    isLoading,
    error,
  } = useTreeData({ taxonGroupId, autoLoad: true });

  const {
    handlers,
    transform,
    isDragging,
    zoomIn,
    zoomOut,
    resetView,
    fitToView,
    containerRef,
  } = usePanZoom();

  // Calculate tree layout
  const { nodes, links, width, height: treeHeight } = useTreeLayout(
    rootNodes,
    expandedNodeIds
  );

  // Handle node toggle (expand/collapse)
  const handleNodeToggle = useCallback(
    async (nodeId: number) => {
      const node = rootNodes.find((n) => n.id === nodeId) ||
        nodes.find((n) => n.id === nodeId);

      if (expandedNodeIds.has(nodeId)) {
        // Collapse
        toggleNodeExpanded(nodeId);
      } else {
        // Expand - load children if needed
        const storeNode = useTreeStore.getState().getNode(nodeId);
        if (storeNode && (!storeNode.children || storeNode.children.length === 0)) {
          await loadNodeChildren(nodeId);
        } else {
          toggleNodeExpanded(nodeId);
        }
      }
    },
    [expandedNodeIds, loadNodeChildren, toggleNodeExpanded, rootNodes, nodes]
  );

  // Handle node selection (visual selection only)
  const handleNodeSelect = useCallback(
    (nodeId: number) => {
      selectNode(nodeId);
      onNodeSelect?.(nodeId);
    },
    [selectNode, onNodeSelect]
  );

  // Handle node double-click (opens edit form)
  const handleNodeDoubleClick = useCallback(
    (nodeId: number) => {
      onNodeDoubleClick?.(nodeId);
    },
    [onNodeDoubleClick]
  );

  // Handle fit to view
  const handleFitToView = useCallback(() => {
    if (width > 0 && treeHeight > 0) {
      fitToView(width, treeHeight);
    }
  }, [fitToView, width, treeHeight]);

  // Expand all nodes recursively (loads children from API)
  const [isExpandingAll, setIsExpandingAll] = useState(false);

  const handleExpandAll = useCallback(async () => {
    setIsExpandingAll(true);
    try {
      // Recursively load and expand all nodes
      const expandRecursively = async (nodeIds: number[]) => {
        for (const nodeId of nodeIds) {
          const node = useTreeStore.getState().getNode(nodeId);
          if (node?.hasChildren && (!node.children || node.children.length === 0)) {
            await loadNodeChildren(nodeId);
          }
          // Get updated node after loading
          const updatedNode = useTreeStore.getState().getNode(nodeId);
          if (updatedNode?.children && updatedNode.children.length > 0) {
            await expandRecursively(updatedNode.children.map(c => c.id));
          }
        }
      };

      await expandRecursively(rootNodes.map(n => n.id));
      expandAll();
    } finally {
      setIsExpandingAll(false);
    }
  }, [rootNodes, loadNodeChildren, expandAll]);

  // Reference to SVG element for printing
  const svgRef = React.useRef<SVGSVGElement>(null);

  // Handle print/export as PDF
  const handlePrint = useCallback(() => {
    const svgElement = svgRef.current;
    if (!svgElement) return;

    // Clone the SVG to avoid modifying the original
    const svgClone = svgElement.cloneNode(true) as SVGSVGElement;

    // Get the tree bounds
    const padding = 50;
    const treeWidth = width + padding * 2;
    const treeHeightWithPadding = treeHeight + padding * 2;

    // Set viewBox to show the entire tree
    svgClone.setAttribute('viewBox', `${-padding} ${-padding} ${treeWidth} ${treeHeightWithPadding}`);
    svgClone.setAttribute('width', `${treeWidth}`);
    svgClone.setAttribute('height', `${treeHeightWithPadding}`);

    // Remove the transform from the main group (we're using viewBox instead)
    const mainGroup = svgClone.querySelector('g');
    if (mainGroup) {
      mainGroup.removeAttribute('transform');
    }

    // Serialize the SVG
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgClone);

    // Create a new window for printing
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert('Please allow popups to export the tree as PDF');
      return;
    }

    // Write the HTML with the SVG and print styles
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Phylogenetic Tree</title>
          <style>
            @page {
              size: landscape;
              margin: 10mm;
            }
            body {
              margin: 0;
              padding: 20px;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            svg {
              max-width: 100%;
              height: auto;
              display: block;
            }
            h1 {
              font-size: 18px;
              margin-bottom: 10px;
              color: #333;
            }
            .print-info {
              font-size: 10px;
              color: #666;
              margin-top: 10px;
            }
            @media print {
              body { padding: 0; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <h1>Phylogenetic Tree</h1>
          ${svgString}
          <p class="print-info">Generated on ${new Date().toLocaleString()}</p>
          <p class="no-print" style="margin-top: 20px;">
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 14px; cursor: pointer;">
              Print / Save as PDF
            </button>
          </p>
        </body>
      </html>
    `);

    printWindow.document.close();
  }, [width, treeHeight]);

  // Reset store when taxon group changes
  useEffect(() => {
    reset();
    loadRootNodes();
  }, [taxonGroupId, reset, loadRootNodes]);

  // Auto-expand all nodes when root nodes are loaded
  const hasAutoExpanded = React.useRef(false);
  useEffect(() => {
    if (rootNodes.length > 0 && !hasAutoExpanded.current && !isExpandingAll) {
      hasAutoExpanded.current = true;
      handleExpandAll();
    }
  }, [rootNodes.length, isExpandingAll, handleExpandAll]);

  // Reset auto-expand flag when taxon group changes
  useEffect(() => {
    hasAutoExpanded.current = false;
  }, [taxonGroupId]);

  // Collect all visible ranks for legend
  const visibleRanks = useMemo(() => {
    const ranks = new Set<string>();
    nodes.forEach((node) => {
      if (node.rank) ranks.add(node.rank.toUpperCase());
    });
    return Array.from(ranks);
  }, [nodes]);

  // Check if a link is highlighted (connects highlighted nodes)
  const isLinkHighlighted = useCallback(
    (link: { source: { id: number }; target: { id: number } }) => {
      return (
        highlightedNodeIds.has(link.source.id) &&
        highlightedNodeIds.has(link.target.id)
      );
    },
    [highlightedNodeIds]
  );

  if (isLoading && rootNodes.length === 0) {
    return (
      <Center h={height}>
        <VStack spacing={4}>
          <Spinner size="xl" color="brand.500" />
          <Text color="gray.500">Loading taxonomy tree...</Text>
        </VStack>
      </Center>
    );
  }

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        {error}
      </Alert>
    );
  }

  if (rootNodes.length === 0) {
    return (
      <Center h={height}>
        <Text color="gray.500">
          No taxa found. Select a taxon group to view the phylogenetic tree.
        </Text>
      </Center>
    );
  }

  return (
    <Box position="relative" h={height} overflow="hidden">
      {/* Inject spinner animation CSS */}
      <style>{spinnerKeyframes}</style>

      {/* Controls */}
      {showControls && (
        <TreeControls
          onZoomIn={zoomIn}
          onZoomOut={zoomOut}
          onResetView={resetView}
          onFitToView={handleFitToView}
          onExpandAll={handleExpandAll}
          onCollapseAll={collapseAll}
          onPrint={handlePrint}
          scale={transform.scale}
          isExpandingAll={isExpandingAll}
        />
      )}

      {/* Legend */}
      {showLegend && <TreeLegend visibleRanks={visibleRanks} />}

      {/* Pan/Zoom Canvas */}
      <Box
        ref={containerRef as React.RefObject<HTMLDivElement>}
        h="100%"
        w="100%"
        overflow="hidden"
        bg="gray.50"
        borderRadius="md"
        border="1px solid"
        borderColor="gray.200"
        cursor={isDragging ? 'grabbing' : 'grab'}
        {...handlers}
      >
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          style={{
            display: 'block',
            overflow: 'visible',
          }}
        >
          <g
            transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}
          >
            {/* Links (rendered first, behind nodes) */}
            <g className="links">
              {links.map((link) => (
                <TreeLink
                  key={`${link.source.id}-${link.target.id}`}
                  link={link}
                  isHighlighted={isLinkHighlighted(link)}
                />
              ))}
            </g>

            {/* Nodes */}
            <g className="nodes">
              {nodes.map((node) => (
                <TreeNode
                  key={node.id}
                  node={node}
                  isExpanded={expandedNodeIds.has(node.id)}
                  isSelected={selectedNodeId === node.id}
                  isHighlighted={highlightedNodeIds.has(node.id)}
                  isLoading={loadingNodeIds.has(node.id)}
                  onToggle={handleNodeToggle}
                  onSelect={handleNodeSelect}
                  onDoubleClick={handleNodeDoubleClick}
                />
              ))}
            </g>
          </g>
        </svg>
      </Box>
    </Box>
  );
};

export default PhylogeneticTree;
