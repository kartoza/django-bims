/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Conservation Status Filter - Filter by IUCN categories
 */
import React, { useCallback } from 'react';
import {
  VStack,
  Checkbox,
  CheckboxGroup,
  HStack,
  Badge,
  Text,
} from '@chakra-ui/react';
import { useSearchStore } from '../../../stores/searchStore';

interface IUCNCategory {
  code: string;
  name: string;
  color: string;
}

const IUCN_CATEGORIES: IUCNCategory[] = [
  { code: 'LC', name: 'Least Concern', color: 'green' },
  { code: 'NT', name: 'Near Threatened', color: 'yellow' },
  { code: 'VU', name: 'Vulnerable', color: 'orange' },
  { code: 'EN', name: 'Endangered', color: 'red' },
  { code: 'CR', name: 'Critically Endangered', color: 'red' },
  { code: 'EW', name: 'Extinct in the Wild', color: 'purple' },
  { code: 'EX', name: 'Extinct', color: 'gray' },
  { code: 'DD', name: 'Data Deficient', color: 'gray' },
  { code: 'NE', name: 'Not Evaluated', color: 'gray' },
];

export const ConservationStatusFilter: React.FC = () => {
  const { filters, setFilter } = useSearchStore();
  const selectedStatuses = filters.iucnCategories || [];

  const handleChange = useCallback(
    (values: (string | number)[]) => {
      setFilter('iucnCategories', values as string[]);
    },
    [setFilter]
  );

  return (
    <CheckboxGroup value={selectedStatuses} onChange={handleChange}>
      <VStack spacing={2} align="stretch">
        {IUCN_CATEGORIES.map((category) => (
          <Checkbox key={category.code} value={category.code} size="sm">
            <HStack spacing={2}>
              <Badge colorScheme={category.color} size="sm" minW="24px">
                {category.code}
              </Badge>
              <Text fontSize="sm">{category.name}</Text>
            </HStack>
          </Checkbox>
        ))}
      </VStack>
    </CheckboxGroup>
  );
};

export default ConservationStatusFilter;
