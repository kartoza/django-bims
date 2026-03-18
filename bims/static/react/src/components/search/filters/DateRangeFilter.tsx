/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Date Range Filter - Filter by collection date range
 */
import React, { useCallback } from 'react';
import {
  VStack,
  HStack,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Text,
  RangeSlider,
  RangeSliderTrack,
  RangeSliderFilledTrack,
  RangeSliderThumb,
} from '@chakra-ui/react';
import { useSearchStore } from '../../../stores/searchStore';

const MIN_YEAR = 1900;
const MAX_YEAR = new Date().getFullYear();

export const DateRangeFilter: React.FC = () => {
  const { filters, setFilter } = useSearchStore();

  const yearFrom = filters.yearFrom || MIN_YEAR;
  const yearTo = filters.yearTo || MAX_YEAR;

  const handleYearFromChange = useCallback(
    (_: string, value: number) => {
      if (value >= MIN_YEAR && value <= yearTo) {
        setFilter('yearFrom', value);
      }
    },
    [yearTo, setFilter]
  );

  const handleYearToChange = useCallback(
    (_: string, value: number) => {
      if (value >= yearFrom && value <= MAX_YEAR) {
        setFilter('yearTo', value);
      }
    },
    [yearFrom, setFilter]
  );

  const handleSliderChange = useCallback(
    (values: number[]) => {
      setFilter('yearFrom', values[0]);
      setFilter('yearTo', values[1]);
    },
    [setFilter]
  );

  return (
    <VStack spacing={4} align="stretch">
      <RangeSlider
        aria-label={['Year from', 'Year to']}
        min={MIN_YEAR}
        max={MAX_YEAR}
        step={1}
        value={[yearFrom, yearTo]}
        onChange={handleSliderChange}
        colorScheme="blue"
      >
        <RangeSliderTrack>
          <RangeSliderFilledTrack />
        </RangeSliderTrack>
        <RangeSliderThumb index={0} />
        <RangeSliderThumb index={1} />
      </RangeSlider>

      <HStack spacing={4}>
        <FormControl size="sm">
          <FormLabel fontSize="xs">From</FormLabel>
          <NumberInput
            size="sm"
            min={MIN_YEAR}
            max={yearTo}
            value={yearFrom}
            onChange={handleYearFromChange}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <FormControl size="sm">
          <FormLabel fontSize="xs">To</FormLabel>
          <NumberInput
            size="sm"
            min={yearFrom}
            max={MAX_YEAR}
            value={yearTo}
            onChange={handleYearToChange}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>
      </HStack>

      <Text fontSize="xs" color="gray.500" textAlign="center">
        {yearFrom} - {yearTo}
      </Text>
    </VStack>
  );
};

export default DateRangeFilter;
