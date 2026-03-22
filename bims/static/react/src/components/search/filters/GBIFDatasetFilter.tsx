/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * GBIF Dataset Filter - Filter by GBIF data sources
 *
 * Made with love by Kartoza | https://kartoza.com
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
  Badge,
  HStack,
  Link,
  Icon,
} from '@chakra-ui/react';
import { SearchIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';
import { apiClient } from '../../../api/client';

interface GBIFDataset {
  id: number;
  key: string;
  name: string;
  description?: string;
  record_count?: number;
  publisher?: string;
}

export const GBIFDatasetFilter: React.FC = () => {
  const [datasets, setDatasets] = useState<GBIFDataset[]>([]);
  const [filteredDatasets, setFilteredDatasets] = useState<GBIFDataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const { filters, setFilter } = useSearchStore();
  const selectedDatasets = filters.gbifDatasets || [];

  // Fetch GBIF datasets - this endpoint may not be available yet
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        // Try the legacy API endpoint first
        const response = await fetch('/api/dataset-autocomplete/?q=');
        if (response.ok) {
          const datasetList = await response.json();
          // Map to our expected format
          const mappedDatasets = (datasetList || []).map((d: any) => ({
            id: d.id,
            key: d.uuid || String(d.id),
            name: d.name || d.title || 'Unknown Dataset',
            description: d.description,
            record_count: d.record_count,
            publisher: d.publisher || d.owner,
          }));
          setDatasets(mappedDatasets);
          setFilteredDatasets(mappedDatasets);
        } else {
          // Endpoint not available, leave datasets empty
          console.log('GBIF datasets endpoint not available');
        }
      } catch (error) {
        // Silently fail - the filter will show "No GBIF datasets available"
        console.log('GBIF datasets not configured');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDatasets();
  }, []);

  // Filter by search term
  useEffect(() => {
    if (!searchTerm) {
      setFilteredDatasets(datasets);
    } else {
      const term = searchTerm.toLowerCase();
      setFilteredDatasets(
        datasets.filter(
          (d) =>
            d.name.toLowerCase().includes(term) ||
            (d.publisher && d.publisher.toLowerCase().includes(term))
        )
      );
    }
  }, [searchTerm, datasets]);

  const handleChange = useCallback(
    (values: (string | number)[]) => {
      setFilter('gbifDatasets', values.length > 0 ? values.map(String) : undefined);
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

  if (datasets.length === 0) {
    return (
      <VStack spacing={2} align="stretch">
        <Text color="gray.500" fontSize="sm">No GBIF datasets available</Text>
        <Link
          href="https://www.gbif.org/dataset/search"
          isExternal
          fontSize="sm"
          color="brand.500"
        >
          Browse GBIF datasets <Icon as={ExternalLinkIcon} mx="2px" />
        </Link>
      </VStack>
    );
  }

  return (
    <VStack spacing={3} align="stretch">
      <HStack>
        <Badge colorScheme="green" fontSize="xs">GBIF</Badge>
        <Text fontSize="xs" color="gray.500">
          Global Biodiversity Information Facility
        </Text>
      </HStack>

      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchIcon color="gray.400" fontSize="xs" />
        </InputLeftElement>
        <Input
          placeholder="Filter datasets..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </InputGroup>

      <Box maxH="200px" overflow="auto">
        <CheckboxGroup value={selectedDatasets} onChange={handleChange}>
          <VStack spacing={2} align="stretch">
            {filteredDatasets.map((dataset) => (
              <Checkbox key={dataset.id} value={dataset.key} size="sm">
                <VStack align="flex-start" spacing={0}>
                  <Text fontSize="sm" noOfLines={1}>
                    {dataset.name}
                  </Text>
                  {dataset.publisher && (
                    <Text fontSize="xs" color="gray.500" noOfLines={1}>
                      {dataset.publisher}
                    </Text>
                  )}
                  {dataset.record_count !== undefined && (
                    <Text fontSize="xs" color="gray.400">
                      {dataset.record_count.toLocaleString()} records
                    </Text>
                  )}
                </VStack>
              </Checkbox>
            ))}
          </VStack>
        </CheckboxGroup>
      </Box>
    </VStack>
  );
};

export default GBIFDatasetFilter;
