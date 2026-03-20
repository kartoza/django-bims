/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Search Panel - Main search interface for BIMS
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  InputGroup,
  InputLeftElement,
  IconButton,
  Heading,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Badge,
  useColorModeValue,
  Spinner,
  Text,
  Divider,
} from '@chakra-ui/react';
import { SearchIcon, CloseIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../stores/searchStore';
import { TaxonGroupFilter } from './filters/TaxonGroupFilter';
import { DateRangeFilter } from './filters/DateRangeFilter';
import { ConservationStatusFilter } from './filters/ConservationStatusFilter';
import { EndemismFilter } from './filters/EndemismFilter';
import { CollectorFilter } from './filters/CollectorFilter';
import { SpatialFilter } from './filters/SpatialFilter';
import { EcosystemTypeFilter } from './filters/EcosystemTypeFilter';
import { ReferenceCategoryFilter } from './filters/ReferenceCategoryFilter';
import { SourceCollectionFilter } from './filters/SourceCollectionFilter';
import { GBIFDatasetFilter } from './filters/GBIFDatasetFilter';
import { ValidationStatusFilter } from './filters/ValidationStatusFilter';
import { SearchResults } from './SearchResults';
import type { BiologicalRecord } from '../../types';

interface SearchPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onRecordSelect?: (record: BiologicalRecord) => void;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({
  isOpen,
  onClose,
  onRecordSelect,
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const {
    query,
    isLoading,
    totalCount,
    setQuery,
    clearFilters,
    search,
    activeFilterCount,
  } = useSearchStore();

  const [localQuery, setLocalQuery] = useState(query);

  const handleSearch = useCallback(() => {
    setQuery(localQuery);
    search();
  }, [localQuery, setQuery, search]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleSearch();
      }
    },
    [handleSearch]
  );

  const handleClear = useCallback(() => {
    setLocalQuery('');
    setQuery('');
    clearFilters();
  }, [setQuery, clearFilters]);

  if (!isOpen) return null;

  return (
    <Box
      position="absolute"
      left={0}
      top={0}
      bottom={0}
      width="380px"
      bg={bgColor}
      borderRight="1px"
      borderColor={borderColor}
      boxShadow="lg"
      zIndex={1000}
      display="flex"
      flexDirection="column"
      overflow="hidden"
    >
      {/* Header */}
      <HStack
        p={4}
        borderBottom="1px"
        borderColor={borderColor}
        justify="space-between"
      >
        <Heading size="md">Search</Heading>
        <HStack>
          {activeFilterCount > 0 && (
            <Badge colorScheme="blue" borderRadius="full">
              {activeFilterCount} filters
            </Badge>
          )}
          <IconButton
            aria-label="Close search"
            icon={<CloseIcon />}
            size="sm"
            variant="ghost"
            onClick={onClose}
          />
        </HStack>
      </HStack>

      {/* Search Input */}
      <Box p={4}>
        <InputGroup>
          <InputLeftElement pointerEvents="none">
            <SearchIcon color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Search species, sites, collectors..."
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            onKeyPress={handleKeyPress}
          />
        </InputGroup>
        <HStack mt={2} spacing={2}>
          <IconButton
            aria-label="Search"
            icon={<SearchIcon />}
            colorScheme="blue"
            size="sm"
            onClick={handleSearch}
            isLoading={isLoading}
          />
          <IconButton
            aria-label="Clear"
            icon={<CloseIcon />}
            size="sm"
            variant="outline"
            onClick={handleClear}
          />
        </HStack>
      </Box>

      <Divider />

      {/* Filters Accordion */}
      <Box flex={1} overflow="auto">
        <Accordion allowMultiple defaultIndex={[0]}>
          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Taxon Group
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <TaxonGroupFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Date Range
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <DateRangeFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Conservation Status
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <ConservationStatusFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Endemism
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <EndemismFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Collector
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <CollectorFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Spatial Filter
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <SpatialFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Ecosystem Type
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <EcosystemTypeFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Validation Status
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <ValidationStatusFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Reference Category
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <ReferenceCategoryFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                Source Collection
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <SourceCollectionFilter />
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem>
            <AccordionButton>
              <Box flex={1} textAlign="left" fontWeight="medium">
                GBIF Dataset
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <GBIFDatasetFilter />
            </AccordionPanel>
          </AccordionItem>
        </Accordion>

        <Divider />

        {/* Results Section */}
        <Box p={4}>
          <HStack justify="space-between" mb={3}>
            <Heading size="sm">Results</Heading>
            {totalCount !== null && (
              <Badge colorScheme="green">
                {totalCount.toLocaleString()} records
              </Badge>
            )}
          </HStack>

          {isLoading ? (
            <VStack py={8}>
              <Spinner size="lg" color="blue.500" />
              <Text color="gray.500">Searching...</Text>
            </VStack>
          ) : (
            <SearchResults onRecordSelect={onRecordSelect} />
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default SearchPanel;
