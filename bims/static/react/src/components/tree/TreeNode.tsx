/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Tree node component for phylogenetic tree visualization.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { memo, useCallback } from 'react';
import { LayoutNode } from '../../hooks/useTreeLayout';

export interface TreeNodeProps {
  node: LayoutNode;
  isExpanded: boolean;
  isSelected: boolean;
  isHighlighted: boolean;
  isLoading: boolean;
  onToggle: (nodeId: number) => void;
  onSelect: (nodeId: number) => void;
  onDoubleClick?: (nodeId: number) => void;
}

// Rank color scheme - vibrant colors for visual hierarchy
export const RANK_COLORS: Record<string, string> = {
  KINGDOM: '#9f7aea',    // Purple
  PHYLUM: '#4299e1',     // Blue
  CLASS: '#38b2ac',      // Teal
  ORDER: '#48bb78',      // Green
  FAMILY: '#68d391',     // Light Green
  GENUS: '#ecc94b',      // Yellow
  SPECIES: '#ed8936',    // Orange
  SUBSPECIES: '#fc8181', // Red
  VARIETY: '#f687b3',    // Pink
  FORM: '#b794f4',       // Light Purple
};

const DEFAULT_COLOR = '#a0aec0'; // Gray for unknown ranks

const TreeNodeComponent: React.FC<TreeNodeProps> = ({
  node,
  isExpanded,
  isSelected,
  isHighlighted,
  isLoading,
  onToggle,
  onSelect,
  onDoubleClick,
}) => {
  const handleToggle = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onToggle(node.id);
    },
    [node.id, onToggle]
  );

  const handleSelect = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onSelect(node.id);
    },
    [node.id, onSelect]
  );

  const handleDoubleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onDoubleClick?.(node.id);
    },
    [node.id, onDoubleClick]
  );

  const nodeColor = RANK_COLORS[node.rank?.toUpperCase()] || DEFAULT_COLOR;
  const isItalic = node.rank === 'SPECIES' || node.rank === 'GENUS' || node.rank === 'SUBSPECIES';

  // Node dimensions
  const circleRadius = 8;
  const textOffset = 16;
  const maxTextWidth = 180;

  return (
    <g
      transform={`translate(${node.x}, ${node.y})`}
      style={{ cursor: 'pointer' }}
      onClick={handleSelect}
      onDoubleClick={handleDoubleClick}
    >
      {/* Selection/highlight background */}
      {(isSelected || isHighlighted) && (
        <rect
          x={-circleRadius - 4}
          y={-14}
          width={maxTextWidth + circleRadius + 8}
          height={28}
          rx={4}
          fill={isSelected ? 'rgba(66, 153, 225, 0.2)' : 'rgba(236, 201, 75, 0.2)'}
          stroke={isSelected ? '#4299e1' : '#ecc94b'}
          strokeWidth={1.5}
        />
      )}

      {/* Expand/collapse indicator for nodes with children */}
      {node.hasChildren && (
        <g onClick={handleToggle} style={{ cursor: 'pointer' }}>
          <circle
            cx={-circleRadius - 12}
            cy={0}
            r={8}
            fill="white"
            stroke="#cbd5e0"
            strokeWidth={1}
          />
          {isLoading ? (
            // Loading spinner
            <g transform={`translate(${-circleRadius - 12}, 0)`}>
              <circle
                r={4}
                fill="none"
                stroke="#4299e1"
                strokeWidth={2}
                strokeDasharray="10 6"
                style={{
                  transformOrigin: 'center',
                  animation: 'spin 1s linear infinite',
                }}
              />
            </g>
          ) : (
            // Plus/minus indicator
            <>
              <line
                x1={-circleRadius - 16}
                y1={0}
                x2={-circleRadius - 8}
                y2={0}
                stroke="#718096"
                strokeWidth={1.5}
              />
              {!isExpanded && (
                <line
                  x1={-circleRadius - 12}
                  y1={-4}
                  x2={-circleRadius - 12}
                  y2={4}
                  stroke="#718096"
                  strokeWidth={1.5}
                />
              )}
            </>
          )}
        </g>
      )}

      {/* Main node circle */}
      <circle
        cx={0}
        cy={0}
        r={circleRadius}
        fill={nodeColor}
        stroke={isSelected ? '#2b6cb0' : 'white'}
        strokeWidth={isSelected ? 2 : 1.5}
        filter="drop-shadow(0 1px 2px rgba(0,0,0,0.1))"
      />

      {/* Rank abbreviation inside circle */}
      <text
        x={0}
        y={0}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={6}
        fontWeight="bold"
        fill="white"
        style={{ pointerEvents: 'none' }}
      >
        {node.rank?.substring(0, 2).toUpperCase()}
      </text>

      {/* Node label */}
      <text
        x={textOffset}
        y={0}
        dominantBaseline="central"
        fontSize={12}
        fontStyle={isItalic ? 'italic' : 'normal'}
        fontWeight={isSelected ? 600 : 400}
        fill="#2d3748"
        style={{ pointerEvents: 'none' }}
      >
        {node.name.length > 25 ? node.name.substring(0, 22) + '...' : node.name}
      </text>
    </g>
  );
};

// Memoize to prevent unnecessary re-renders
export const TreeNode = memo(TreeNodeComponent);

export default TreeNode;
