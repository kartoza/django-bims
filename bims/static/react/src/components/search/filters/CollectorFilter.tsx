/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Collector Filter - Filter by collector name with autocomplete
 */
import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  VStack,
  Input,
  InputGroup,
  InputLeftElement,
  Box,
  List,
  ListItem,
  Tag,
  TagLabel,
  TagCloseButton,
  HStack,
  Text,
  Spinner,
  useColorModeValue,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';
import { apiClient } from '../../../api/client';

interface CollectorSuggestion {
  id: number;
  name: string;
}

export const CollectorFilter: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<CollectorSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout>();

  const bgColor = useColorModeValue('white', 'gray.700');
  const hoverBg = useColorModeValue('gray.100', 'gray.600');

  const { filters, setFilter } = useSearchStore();
  const selectedCollectors = filters.collectors || [];

  // Fetch suggestions with debounce
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.get<{ data: CollectorSuggestion[] }>(
          'autocomplete/collectors/',
          { params: { q: query, limit: 10 } }
        );
        setSuggestions(response.data?.data || []);
      } catch (error) {
        console.error('Failed to fetch collector suggestions:', error);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query]);

  const handleSelect = useCallback(
    (collector: CollectorSuggestion) => {
      if (!selectedCollectors.includes(collector.name)) {
        setFilter('collectors', [...selectedCollectors, collector.name]);
      }
      setQuery('');
      setShowSuggestions(false);
    },
    [selectedCollectors, setFilter]
  );

  const handleRemove = useCallback(
    (name: string) => {
      setFilter(
        'collectors',
        selectedCollectors.filter((c: string) => c !== name)
      );
    },
    [selectedCollectors, setFilter]
  );

  return (
    <VStack spacing={3} align="stretch">
      {/* Selected collectors */}
      {selectedCollectors.length > 0 && (
        <HStack flexWrap="wrap" spacing={2}>
          {selectedCollectors.map((name: string) => (
            <Tag key={name} size="sm" colorScheme="blue" borderRadius="full">
              <TagLabel>{name}</TagLabel>
              <TagCloseButton onClick={() => handleRemove(name)} />
            </Tag>
          ))}
        </HStack>
      )}

      {/* Search input */}
      <Box position="relative">
        <InputGroup size="sm">
          <InputLeftElement pointerEvents="none">
            {isLoading ? (
              <Spinner size="xs" color="gray.400" />
            ) : (
              <SearchIcon color="gray.400" fontSize="xs" />
            )}
          </InputLeftElement>
          <Input
            placeholder="Search collectors..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          />
        </InputGroup>

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <Box
            position="absolute"
            top="100%"
            left={0}
            right={0}
            mt={1}
            bg={bgColor}
            border="1px solid"
            borderColor="gray.200"
            borderRadius="md"
            boxShadow="md"
            zIndex={100}
            maxH="200px"
            overflow="auto"
          >
            <List spacing={0}>
              {suggestions.map((suggestion) => (
                <ListItem
                  key={suggestion.id}
                  px={3}
                  py={2}
                  cursor="pointer"
                  _hover={{ bg: hoverBg }}
                  onClick={() => handleSelect(suggestion)}
                >
                  <Text fontSize="sm">{suggestion.name}</Text>
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Box>
    </VStack>
  );
};

export default CollectorFilter;
