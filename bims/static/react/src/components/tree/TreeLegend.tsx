/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Tree legend component showing taxonomic rank colors.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Collapse,
  IconButton,
  useDisclosure,
} from '@chakra-ui/react';
import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import { RANK_COLORS } from './TreeNode';

// Ordered list of ranks for display
const RANK_ORDER = [
  'KINGDOM',
  'PHYLUM',
  'CLASS',
  'ORDER',
  'FAMILY',
  'GENUS',
  'SPECIES',
  'SUBSPECIES',
];

// Human-readable rank names
const RANK_LABELS: Record<string, string> = {
  KINGDOM: 'Kingdom',
  PHYLUM: 'Phylum',
  CLASS: 'Class',
  ORDER: 'Order',
  FAMILY: 'Family',
  GENUS: 'Genus',
  SPECIES: 'Species',
  SUBSPECIES: 'Subspecies',
};

export interface TreeLegendProps {
  visibleRanks?: string[];
  compact?: boolean;
}

const TreeLegend: React.FC<TreeLegendProps> = ({
  visibleRanks,
  compact = false,
}) => {
  const { isOpen, onToggle } = useDisclosure({ defaultIsOpen: !compact });

  // Filter ranks if visibleRanks is provided
  const ranksToShow = visibleRanks
    ? RANK_ORDER.filter((rank) =>
        visibleRanks.some((vr) => vr.toUpperCase() === rank)
      )
    : RANK_ORDER;

  if (ranksToShow.length === 0) {
    return null;
  }

  return (
    <Box
      position="absolute"
      left={4}
      bottom={4}
      bg="white"
      borderRadius="md"
      boxShadow="md"
      maxW="200px"
      zIndex={10}
    >
      <HStack
        px={3}
        py={2}
        cursor="pointer"
        onClick={onToggle}
        justify="space-between"
      >
        <Text fontSize="xs" fontWeight="semibold" color="gray.600">
          Taxonomic Ranks
        </Text>
        <IconButton
          aria-label={isOpen ? 'Collapse legend' : 'Expand legend'}
          icon={isOpen ? <ChevronDownIcon /> : <ChevronUpIcon />}
          size="xs"
          variant="ghost"
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
        />
      </HStack>

      <Collapse in={isOpen}>
        <VStack align="stretch" spacing={0} pb={2} px={3}>
          {ranksToShow.map((rank) => (
            <HStack key={rank} spacing={2} py={0.5}>
              <Box
                w={3}
                h={3}
                borderRadius="full"
                bg={RANK_COLORS[rank]}
                flexShrink={0}
              />
              <Text fontSize="xs" color="gray.700">
                {RANK_LABELS[rank]}
              </Text>
            </HStack>
          ))}
        </VStack>
      </Collapse>
    </Box>
  );
};

export default TreeLegend;
