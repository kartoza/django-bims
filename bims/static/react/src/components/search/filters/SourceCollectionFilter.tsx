/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Source Collection Filter - Filter by data source/collection
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
  Box,
  Tooltip,
  Icon,
} from '@chakra-ui/react';
import { InfoIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';

interface SourceCollection {
  id: string;  // Use name as id since the API returns name:description pairs
  name: string;
  description?: string;
}

export const SourceCollectionFilter: React.FC = () => {
  const [collections, setCollections] = useState<SourceCollection[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const { filters, setFilter } = useSearchStore();
  const selectedCollections = filters.sourceCollections || [];

  // Fetch source collections from legacy API
  useEffect(() => {
    const fetchCollections = async () => {
      try {
        // Use legacy endpoint that returns {name: description} pairs
        const response = await fetch('/api/data-source-descriptions/');
        if (response.ok) {
          const data = await response.json();
          // Convert dictionary to array
          const collectionList: SourceCollection[] = Object.entries(data).map(
            ([name, description]) => ({
              id: name,
              name: name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' '),
              description: description as string,
            })
          );
          setCollections(collectionList);
        } else {
          console.log('Source collections endpoint not available');
        }
      } catch (error) {
        console.log('Source collections not configured');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCollections();
  }, []);

  const handleChange = useCallback(
    (values: (string | number)[]) => {
      // sourceCollections uses string IDs (source names like 'fbis', 'gbif')
      setFilter('sourceCollections', values.length > 0 ? values.map(String) : undefined);
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

  if (collections.length === 0) {
    return <Text color="gray.500" fontSize="sm">No source collections available</Text>;
  }

  return (
    <VStack spacing={3} align="stretch">
      <Box maxH="200px" overflow="auto">
        <CheckboxGroup value={selectedCollections.map(String)} onChange={handleChange}>
          <VStack spacing={2} align="stretch">
            {collections.map((collection) => (
              <Checkbox key={collection.id} value={collection.id} size="sm">
                <Text fontSize="sm" display="inline-flex" alignItems="center" gap={1}>
                  {collection.name.toUpperCase()}
                  {collection.description && (
                    <Tooltip label={collection.description} placement="right" hasArrow>
                      <span>
                        <Icon as={InfoIcon} color="gray.400" boxSize={3} cursor="help" />
                      </span>
                    </Tooltip>
                  )}
                </Text>
              </Checkbox>
            ))}
          </VStack>
        </CheckboxGroup>
      </Box>
    </VStack>
  );
};

export default SourceCollectionFilter;
