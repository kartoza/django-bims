/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Reference Category Filter - Filter by source reference types
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
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';
import { apiClient } from '../../../api/client';

interface ReferenceCategory {
  id: number;
  name: string;
  description?: string;
  reference_count?: number;
}

export const ReferenceCategoryFilter: React.FC = () => {
  const [categories, setCategories] = useState<ReferenceCategory[]>([]);
  const [filteredCategories, setFilteredCategories] = useState<ReferenceCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const { filters, setFilter } = useSearchStore();
  const selectedCategories = filters.referenceCategories || [];

  // Fetch reference categories from legacy API
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        // Use legacy endpoint that returns [{category: "name"}, ...]
        const response = await fetch('/api/list-reference-category/');
        if (response.ok) {
          const data = await response.json();
          // Convert API format to our format
          const categoryList: ReferenceCategory[] = (data || []).map(
            (item: { category: string }, index: number) => ({
              id: index + 1,
              name: item.category,
            })
          );
          setCategories(categoryList);
          setFilteredCategories(categoryList);
        } else {
          throw new Error('Endpoint not available');
        }
      } catch (error) {
        // Silently use fallback categories - this is expected if endpoint doesn't exist
        console.log('Using fallback reference categories');
        const fallbackCategories: ReferenceCategory[] = [
          { id: 1, name: 'Published report' },
          { id: 2, name: 'Peer-reviewed scientific article' },
          { id: 3, name: 'Thesis' },
          { id: 4, name: 'Database' },
          { id: 5, name: 'Unpublished data' },
        ];
        setCategories(fallbackCategories);
        setFilteredCategories(fallbackCategories);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCategories();
  }, []);

  // Filter by search term
  useEffect(() => {
    if (!searchTerm) {
      setFilteredCategories(categories);
    } else {
      const term = searchTerm.toLowerCase();
      setFilteredCategories(
        categories.filter((c) => c.name.toLowerCase().includes(term))
      );
    }
  }, [searchTerm, categories]);

  const handleChange = useCallback(
    (values: (string | number)[]) => {
      setFilter('referenceCategories', values.length > 0 ? values.map(String) : undefined);
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

  if (categories.length === 0) {
    return <Text color="gray.500" fontSize="sm">No reference categories available</Text>;
  }

  return (
    <VStack spacing={3} align="stretch">
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchIcon color="gray.400" fontSize="xs" />
        </InputLeftElement>
        <Input
          placeholder="Filter categories..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </InputGroup>

      <Box maxH="200px" overflow="auto">
        <CheckboxGroup value={selectedCategories} onChange={handleChange}>
          <VStack spacing={2} align="stretch">
            {filteredCategories.map((category) => (
              <Checkbox key={category.id} value={category.name} size="sm">
                <Text fontSize="sm">
                  {category.name}
                  {category.reference_count !== undefined && (
                    <Text as="span" color="gray.500" ml={1}>
                      ({category.reference_count.toLocaleString()})
                    </Text>
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

export default ReferenceCategoryFilter;
