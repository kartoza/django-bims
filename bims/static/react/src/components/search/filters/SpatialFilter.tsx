/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Spatial Filter - Filter by geographic boundary or drawn area
 */
import React, { useCallback, useState, useEffect } from 'react';
import {
  VStack,
  HStack,
  Button,
  Select,
  Text,
  Badge,
  IconButton,
  Tooltip,
} from '@chakra-ui/react';
import { DeleteIcon, EditIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';
import { apiClient } from '../../../api/client';

interface Boundary {
  id: number;
  name: string;
  type: string;
}

export const SpatialFilter: React.FC = () => {
  const [boundaries, setBoundaries] = useState<Boundary[]>([]);
  const [isLoadingBoundaries, setIsLoadingBoundaries] = useState(false);

  const { filters, setFilter } = useSearchStore();

  const selectedBoundary = filters.boundaryId;
  const hasBbox = filters.bbox;

  // Fetch boundaries
  useEffect(() => {
    const fetchBoundaries = async () => {
      setIsLoadingBoundaries(true);
      try {
        const response = await apiClient.get<{ data: Boundary[] }>(
          'boundaries/'
        );
        setBoundaries(response.data?.data || []);
      } catch (error) {
        console.error('Failed to fetch boundaries:', error);
      } finally {
        setIsLoadingBoundaries(false);
      }
    };

    fetchBoundaries();
  }, []);

  const handleBoundaryChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const value = e.target.value ? parseInt(e.target.value, 10) : null;
      setFilter('boundaryId', value);
      // Clear bbox when selecting a boundary
      if (value) {
        setFilter('bbox', null);
      }
    },
    [setFilter]
  );

  const handleClearSpatial = useCallback(() => {
    setFilter('boundaryId', null);
    setFilter('bbox', null);
  }, [setFilter]);

  const hasSpatialFilter = selectedBoundary || hasBbox;

  return (
    <VStack spacing={3} align="stretch">
      {/* Boundary selector */}
      <Select
        placeholder="Select boundary..."
        size="sm"
        value={selectedBoundary || ''}
        onChange={handleBoundaryChange}
        isDisabled={isLoadingBoundaries}
      >
        {boundaries.map((boundary) => (
          <option key={boundary.id} value={boundary.id}>
            {boundary.name}
          </option>
        ))}
      </Select>

      <Text fontSize="xs" color="gray.500" textAlign="center">
        Select a predefined boundary to filter results
      </Text>

      {/* Current filter indicator */}
      {hasSpatialFilter && (
        <HStack justify="space-between" p={2} bg="blue.50" borderRadius="md">
          <HStack>
            <Badge colorScheme="blue">
              {selectedBoundary ? 'Boundary' : 'Custom Area'}
            </Badge>
            <Text fontSize="xs">
              {selectedBoundary
                ? boundaries.find((b) => b.id === selectedBoundary)?.name
                : 'Drawn area'}
            </Text>
          </HStack>
          <Tooltip label="Clear spatial filter">
            <IconButton
              aria-label="Clear spatial filter"
              icon={<DeleteIcon />}
              size="xs"
              variant="ghost"
              colorScheme="red"
              onClick={handleClearSpatial}
            />
          </Tooltip>
        </HStack>
      )}
    </VStack>
  );
};

export default SpatialFilter;
