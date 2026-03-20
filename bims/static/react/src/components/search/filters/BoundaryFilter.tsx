/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Boundary Filter - Filter by administrative/geographic boundaries
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  VStack,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
  Box,
  Text,
  Skeleton,
  HStack,
  Tag,
  TagLabel,
  TagCloseButton,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';
import { filterOptionsApi } from '../../../api/client';

interface Boundary {
  id: number;
  name: string;
  code?: string;
  type?: string;
}

interface BoundaryGroup {
  type: string;
  label: string;
  boundaries: Boundary[];
}

// Boundary type labels
const BOUNDARY_TYPE_LABELS: Record<string, string> = {
  province: 'Provinces',
  district: 'Districts',
  municipality: 'Municipalities',
  catchment: 'Catchments',
  water_management_area: 'Water Management Areas',
  ecoregion: 'Ecoregions',
  protected_area: 'Protected Areas',
  custom: 'Custom Boundaries',
};

export const BoundaryFilter: React.FC = () => {
  const [boundaries, setBoundaries] = useState<Boundary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('');

  const { filters, setFilter } = useSearchStore();
  const selectedBoundaryId = filters.boundaryId;

  // Fetch boundaries from API
  useEffect(() => {
    const fetchBoundaries = async () => {
      try {
        const data = await filterOptionsApi.boundaries();
        // Transform API response to boundary format
        const boundaryList: Boundary[] = (data || []).map((b: any) => ({
          id: b.id,
          name: b.name || b.code || `Boundary ${b.id}`,
          code: b.code,
          type: b.type?.toLowerCase() || 'custom',
        }));
        setBoundaries(boundaryList);
      } catch (error) {
        console.error('Failed to fetch boundaries:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchBoundaries();
  }, []);

  // Group boundaries by type
  const groupedBoundaries = useMemo(() => {
    const groups: Record<string, Boundary[]> = {};

    boundaries.forEach((boundary) => {
      const type = boundary.type || 'custom';
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(boundary);
    });

    // Convert to array and sort
    return Object.entries(groups)
      .map(([type, items]) => ({
        type,
        label: BOUNDARY_TYPE_LABELS[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        boundaries: items.sort((a, b) => a.name.localeCompare(b.name)),
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [boundaries]);

  // Get available types
  const boundaryTypes = useMemo(() => {
    return groupedBoundaries.map((g) => ({ value: g.type, label: g.label }));
  }, [groupedBoundaries]);

  // Filter boundaries based on search and type
  const filteredBoundaries = useMemo(() => {
    let result = boundaries;

    if (selectedType) {
      result = result.filter((b) => b.type === selectedType);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (b) =>
          b.name.toLowerCase().includes(term) ||
          (b.code && b.code.toLowerCase().includes(term))
      );
    }

    return result.slice(0, 50); // Limit to 50 results
  }, [boundaries, selectedType, searchTerm]);

  // Get selected boundary name
  const selectedBoundary = useMemo(() => {
    if (!selectedBoundaryId) return null;
    return boundaries.find((b) => b.id === selectedBoundaryId);
  }, [boundaries, selectedBoundaryId]);

  const handleSelect = useCallback(
    (boundaryId: number) => {
      setFilter('boundaryId', boundaryId);
    },
    [setFilter]
  );

  const handleClear = useCallback(() => {
    setFilter('boundaryId', undefined);
  }, [setFilter]);

  if (isLoading) {
    return (
      <VStack spacing={2} align="stretch">
        <Skeleton height="32px" />
        <Skeleton height="32px" />
        <Skeleton height="100px" />
      </VStack>
    );
  }

  return (
    <VStack spacing={3} align="stretch">
      {/* Selected boundary tag */}
      {selectedBoundary && (
        <HStack>
          <Tag size="md" colorScheme="blue" borderRadius="full">
            <TagLabel>
              {selectedBoundary.name}
              {selectedBoundary.type && (
                <Text as="span" fontSize="xs" ml={1} opacity={0.7}>
                  ({BOUNDARY_TYPE_LABELS[selectedBoundary.type] || selectedBoundary.type})
                </Text>
              )}
            </TagLabel>
            <TagCloseButton onClick={handleClear} />
          </Tag>
        </HStack>
      )}

      {/* Type selector */}
      <Select
        size="sm"
        placeholder="All boundary types"
        value={selectedType}
        onChange={(e) => setSelectedType(e.target.value)}
      >
        {boundaryTypes.map((type) => (
          <option key={type.value} value={type.value}>
            {type.label}
          </option>
        ))}
      </Select>

      {/* Search input */}
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchIcon color="gray.400" fontSize="xs" />
        </InputLeftElement>
        <Input
          placeholder="Search boundaries..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </InputGroup>

      {/* Boundary list */}
      <Box maxH="200px" overflow="auto" border="1px" borderColor="gray.200" borderRadius="md">
        {filteredBoundaries.length === 0 ? (
          <Text p={3} color="gray.500" fontSize="sm" textAlign="center">
            No boundaries found
          </Text>
        ) : (
          <VStack spacing={0} align="stretch">
            {filteredBoundaries.map((boundary) => (
              <Box
                key={boundary.id}
                px={3}
                py={2}
                cursor="pointer"
                bg={selectedBoundaryId === boundary.id ? 'blue.50' : 'transparent'}
                _hover={{ bg: selectedBoundaryId === boundary.id ? 'blue.100' : 'gray.50' }}
                onClick={() => handleSelect(boundary.id)}
                borderBottom="1px"
                borderColor="gray.100"
              >
                <Text fontSize="sm" fontWeight={selectedBoundaryId === boundary.id ? 'medium' : 'normal'}>
                  {boundary.name}
                </Text>
                {boundary.type && (
                  <Text fontSize="xs" color="gray.500">
                    {BOUNDARY_TYPE_LABELS[boundary.type] || boundary.type}
                  </Text>
                )}
              </Box>
            ))}
          </VStack>
        )}
      </Box>

      {/* Results info */}
      {searchTerm && (
        <Text fontSize="xs" color="gray.500">
          Showing {filteredBoundaries.length} of {boundaries.length} boundaries
        </Text>
      )}
    </VStack>
  );
};

export default BoundaryFilter;
