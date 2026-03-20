/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Endemism Filter - Filter by endemism status
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  VStack,
  Checkbox,
  CheckboxGroup,
  Text,
  Skeleton,
} from '@chakra-ui/react';
import { useSearchStore } from '../../../stores/searchStore';
import { filterOptionsApi } from '../../../api/client';

interface EndemismOption {
  value: string;
  label: string;
  description?: string;
}

// Fallback options if API fails
const FALLBACK_OPTIONS: EndemismOption[] = [
  { value: 'Endemic', label: 'Endemic' },
  { value: 'Near-endemic', label: 'Near-Endemic' },
  { value: 'Non-endemic', label: 'Non-Endemic' },
  { value: 'Unknown', label: 'Unknown' },
];

export const EndemismFilter: React.FC = () => {
  const [options, setOptions] = useState<EndemismOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { filters, setFilter } = useSearchStore();
  const selectedEndemism = filters.endemism || [];

  // Fetch endemism options from API
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const data = await filterOptionsApi.endemism();
        // API returns array of [name, description] tuples
        const optionsList: EndemismOption[] = (data || []).map(
          (item: [string, string] | { name: string; description?: string }) => {
            if (Array.isArray(item)) {
              return {
                value: item[0],
                label: item[0],
                description: item[1],
              };
            }
            return {
              value: item.name,
              label: item.name,
              description: item.description,
            };
          }
        );
        setOptions(optionsList.length > 0 ? optionsList : FALLBACK_OPTIONS);
      } catch (error) {
        console.log('Using fallback endemism options');
        setOptions(FALLBACK_OPTIONS);
      } finally {
        setIsLoading(false);
      }
    };

    fetchOptions();
  }, []);

  const handleChange = useCallback(
    (values: (string | number)[]) => {
      setFilter('endemism', values.length > 0 ? (values as string[]) : undefined);
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

  return (
    <CheckboxGroup value={selectedEndemism} onChange={handleChange}>
      <VStack spacing={2} align="stretch">
        {options.map((option) => (
          <Checkbox key={option.value} value={option.value} size="sm">
            <Text fontSize="sm">{option.label}</Text>
          </Checkbox>
        ))}
      </VStack>
    </CheckboxGroup>
  );
};

export default EndemismFilter;
