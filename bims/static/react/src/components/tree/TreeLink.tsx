/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Tree link component for connecting nodes in phylogenetic tree.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { memo } from 'react';
import { LayoutLink } from '../../hooks/useTreeLayout';

export interface TreeLinkProps {
  link: LayoutLink;
  isHighlighted?: boolean;
}

const TreeLinkComponent: React.FC<TreeLinkProps> = ({ link, isHighlighted = false }) => {
  const { source, target } = link;

  // Create elbow path: horizontal -> vertical -> horizontal
  // This creates a right-angle connection typical of dendrograms
  const midX = (source.x + target.x) / 2;

  const path = `
    M ${source.x + 8} ${source.y}
    H ${midX}
    V ${target.y}
    H ${target.x - 20}
  `;

  return (
    <path
      d={path}
      fill="none"
      stroke={isHighlighted ? '#ecc94b' : '#cbd5e0'}
      strokeWidth={isHighlighted ? 2 : 1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      opacity={isHighlighted ? 1 : 0.8}
    />
  );
};

// Memoize to prevent unnecessary re-renders
export const TreeLink = memo(TreeLinkComponent);

export default TreeLink;
