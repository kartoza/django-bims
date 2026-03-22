/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Ecosystem Type Filter - Filter by ecosystem/habitat type
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  VStack,
  Radio,
  RadioGroup,
  Skeleton,
  Text,
  Input,
  InputGroup,
  InputLeftElement,
  Box,
  Button,
  HStack,
} from '@chakra-ui/react';
import { SearchIcon, CloseIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';
import { apiClient } from '../../../api/client';

interface EcosystemType {
  id: number;
  name: string;
  description?: string;
  site_count?: number;
}

export const EcosystemTypeFilter: React.FC = () => {
  const [ecosystemTypes, setEcosystemTypes] = useState<EcosystemType[]>([]);
  const [filteredTypes, setFilteredTypes] = useState<EcosystemType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const { filters, setFilter, clearFilter } = useSearchStore();
  const selectedType = filters.ecosystemType || '';

  // Fetch ecosystem types
  useEffect(() => {
    const fetchEcosystemTypes = async () => {
      try {
        const response = await apiClient.get<{ data: EcosystemType[] }>(
          'ecosystem-types/'
        );
        const typeList = response.data?.data || [];
        setEcosystemTypes(typeList);
        setFilteredTypes(typeList);
      } catch (error) {
        console.error('Failed to fetch ecosystem types:', error);
        // Fallback to common ecosystem types if API fails
        const fallbackTypes: EcosystemType[] = [
          { id: 1, name: 'River' },
          { id: 2, name: 'Wetland' },
          { id: 3, name: 'Dam' },
          { id: 4, name: 'Lake' },
          { id: 5, name: 'Estuary' },
          { id: 6, name: 'Spring' },
          { id: 7, name: 'Stream' },
          { id: 8, name: 'Pond' },
        ];
        setEcosystemTypes(fallbackTypes);
        setFilteredTypes(fallbackTypes);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEcosystemTypes();
  }, []);

  // Filter by search term
  useEffect(() => {
    if (!searchTerm) {
      setFilteredTypes(ecosystemTypes);
    } else {
      const term = searchTerm.toLowerCase();
      setFilteredTypes(
        ecosystemTypes.filter((t) => t.name.toLowerCase().includes(term))
      );
    }
  }, [searchTerm, ecosystemTypes]);

  const handleChange = useCallback(
    (value: string) => {
      setFilter('ecosystemType', value || undefined);
    },
    [setFilter]
  );

  const handleClear = useCallback(() => {
    clearFilter('ecosystemType');
  }, [clearFilter]);

  if (isLoading) {
    return (
      <VStack spacing={2} align="stretch">
        <Skeleton height="20px" />
        <Skeleton height="20px" />
        <Skeleton height="20px" />
      </VStack>
    );
  }

  if (ecosystemTypes.length === 0) {
    return <Text color="gray.500" fontSize="sm">No ecosystem types available</Text>;
  }

  return (
    <VStack spacing={3} align="stretch">
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchIcon color="gray.400" fontSize="xs" />
        </InputLeftElement>
        <Input
          placeholder="Filter ecosystem types..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </InputGroup>

      <Box maxH="200px" overflow="auto">
        <RadioGroup value={selectedType} onChange={handleChange}>
          <VStack spacing={2} align="stretch">
            {filteredTypes.map((type) => (
              <Radio key={type.id} value={type.name} size="sm">
                <Text fontSize="sm">
                  {type.name}
                  {type.site_count !== undefined && (
                    <Text as="span" color="gray.500" ml={1}>
                      ({type.site_count.toLocaleString()})
                    </Text>
                  )}
                </Text>
              </Radio>
            ))}
          </VStack>
        </RadioGroup>
      </Box>

      {selectedType && (
        <HStack>
          <Button
            size="xs"
            variant="ghost"
            leftIcon={<CloseIcon />}
            onClick={handleClear}
          >
            Clear
          </Button>
        </HStack>
      )}
    </VStack>
  );
};

export default EcosystemTypeFilter;
