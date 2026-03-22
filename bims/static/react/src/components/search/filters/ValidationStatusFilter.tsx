/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Validation Status Filter - Filter by validated/unvalidated records
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useCallback } from 'react';
import {
  VStack,
  Radio,
  RadioGroup,
  Text,
  HStack,
  Icon,
  Button,
} from '@chakra-ui/react';
import { CheckIcon, CloseIcon, WarningIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../../stores/searchStore';

export const ValidationStatusFilter: React.FC = () => {
  const { filters, setFilter, clearFilter } = useSearchStore();

  // Convert boolean to string for RadioGroup
  const getStatusValue = (): string => {
    if (filters.validated === true) return 'validated';
    if (filters.validated === false) return 'unvalidated';
    return 'all';
  };

  const handleChange = useCallback(
    (value: string) => {
      if (value === 'all') {
        clearFilter('validated');
      } else {
        setFilter('validated', value === 'validated');
      }
    },
    [setFilter, clearFilter]
  );

  return (
    <VStack spacing={3} align="stretch">
      <RadioGroup value={getStatusValue()} onChange={handleChange}>
        <VStack spacing={2} align="stretch">
          <Radio value="all" size="sm">
            <HStack spacing={2}>
              <Text fontSize="sm">All Records</Text>
            </HStack>
          </Radio>

          <Radio value="validated" size="sm">
            <HStack spacing={2}>
              <Icon as={CheckIcon} color="green.500" boxSize={3} />
              <Text fontSize="sm">Validated Only</Text>
            </HStack>
          </Radio>

          <Radio value="unvalidated" size="sm">
            <HStack spacing={2}>
              <Icon as={WarningIcon} color="orange.500" boxSize={3} />
              <Text fontSize="sm">Unvalidated Only</Text>
            </HStack>
          </Radio>
        </VStack>
      </RadioGroup>

      <Text fontSize="xs" color="gray.500">
        Validated records have been reviewed and approved by administrators.
      </Text>
    </VStack>
  );
};

export default ValidationStatusFilter;
