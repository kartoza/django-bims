/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Endemism Filter - Filter by endemism status
 */
import React, { useCallback } from 'react';
import {
  VStack,
  Checkbox,
  CheckboxGroup,
  Text,
} from '@chakra-ui/react';
import { useSearchStore } from '../../../stores/searchStore';

const ENDEMISM_OPTIONS = [
  { value: 'endemic', label: 'Endemic' },
  { value: 'near-endemic', label: 'Near-Endemic' },
  { value: 'non-endemic', label: 'Non-Endemic' },
  { value: 'unknown', label: 'Unknown' },
];

export const EndemismFilter: React.FC = () => {
  const { filters, setFilter } = useSearchStore();
  const selectedEndemism = filters.endemism || [];

  const handleChange = useCallback(
    (values: (string | number)[]) => {
      setFilter('endemism', values as string[]);
    },
    [setFilter]
  );

  return (
    <CheckboxGroup value={selectedEndemism} onChange={handleChange}>
      <VStack spacing={2} align="stretch">
        {ENDEMISM_OPTIONS.map((option) => (
          <Checkbox key={option.value} value={option.value} size="sm">
            <Text fontSize="sm">{option.label}</Text>
          </Checkbox>
        ))}
      </VStack>
    </CheckboxGroup>
  );
};

export default EndemismFilter;
