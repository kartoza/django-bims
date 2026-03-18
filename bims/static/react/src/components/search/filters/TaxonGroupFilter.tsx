/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Taxon Group Filter - Filter by taxon modules/groups
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  VStack,
  Checkbox,
  CheckboxGroup,
  Skeleton,
  Text,
  Input,
  InputGroup,
  InputLeftElement,
  Box,
  HStack,
  Icon,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';
import { apiClient } from '../../../api/client';
import { getTaxonGroupIcon } from '../../icons';

interface TaxonGroup {
  id: number;
  name: string;
  logo?: string;
  category?: string;
  record_count?: number;
}

export const TaxonGroupFilter: React.FC = () => {
  const [groups, setGroups] = useState<TaxonGroup[]>([]);
  const [filteredGroups, setFilteredGroups] = useState<TaxonGroup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const { filters, setFilter } = useSearchStore();
  const selectedGroups = filters.taxonGroups || [];

  // Fetch taxon groups
  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const response = await apiClient.get<{ data: TaxonGroup[] }>(
          'taxon-groups/'
        );
        const groupList = response.data?.data || [];
        setGroups(groupList);
        setFilteredGroups(groupList);
      } catch (error) {
        console.error('Failed to fetch taxon groups:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchGroups();
  }, []);

  // Filter groups by search term
  useEffect(() => {
    if (!searchTerm) {
      setFilteredGroups(groups);
    } else {
      const term = searchTerm.toLowerCase();
      setFilteredGroups(
        groups.filter((g) => g.name.toLowerCase().includes(term))
      );
    }
  }, [searchTerm, groups]);

  const handleChange = useCallback(
    (values: (string | number)[]) => {
      setFilter('taxonGroups', values.map(Number));
    },
    [setFilter]
  );

  if (isLoading) {
    return (
      <VStack spacing={2} align="stretch">
        <Skeleton height="20px" />
        <Skeleton height="20px" />
        <Skeleton height="20px" />
      </VStack>
    );
  }

  if (groups.length === 0) {
    return <Text color="gray.500" fontSize="sm">No taxon groups available</Text>;
  }

  return (
    <VStack spacing={3} align="stretch">
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchIcon color="gray.400" fontSize="xs" />
        </InputLeftElement>
        <Input
          placeholder="Filter groups..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </InputGroup>

      <Box maxH="200px" overflow="auto">
        <CheckboxGroup value={selectedGroups.map(String)} onChange={handleChange}>
          <VStack spacing={2} align="stretch">
            {filteredGroups.map((group) => {
              const GroupIcon = getTaxonGroupIcon(group.name);
              return (
                <Checkbox key={group.id} value={String(group.id)} size="sm">
                  <HStack spacing={2}>
                    <Icon as={GroupIcon} boxSize={4} color="brand.600" />
                    <Text fontSize="sm" noOfLines={1}>
                      {group.name}
                      {group.record_count !== undefined && (
                        <Text as="span" color="gray.500" ml={1}>
                          ({group.record_count.toLocaleString()})
                        </Text>
                      )}
                    </Text>
                  </HStack>
                </Checkbox>
              );
            })}
          </VStack>
        </CheckboxGroup>
      </Box>
    </VStack>
  );
};

export default TaxonGroupFilter;
