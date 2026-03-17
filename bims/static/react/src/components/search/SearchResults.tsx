/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Search Results - Display search results with pagination
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useCallback } from 'react';
import {
  VStack,
  HStack,
  Box,
  Text,
  Badge,
  IconButton,
  useColorModeValue,
} from '@chakra-ui/react';
import { ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';
import { useSearchStore } from '../../stores/searchStore';
import type { BiologicalRecord } from '../../types';

interface ResultCardProps {
  record: BiologicalRecord;
  onClick: () => void;
}

const ResultCard: React.FC<ResultCardProps> = ({ record, onClick }) => {
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const hoverBg = useColorModeValue('gray.100', 'gray.600');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const getIUCNColor = (category: string | undefined): string => {
    const colors: Record<string, string> = {
      LC: 'green',
      NT: 'yellow',
      VU: 'orange',
      EN: 'red',
      CR: 'red',
      EW: 'purple',
      EX: 'gray',
      DD: 'gray',
      NE: 'gray',
    };
    return colors[category || ''] || 'gray';
  };

  return (
    <Box
      p={3}
      bg={bgColor}
      borderRadius="md"
      border="1px"
      borderColor={borderColor}
      cursor="pointer"
      _hover={{ bg: hoverBg }}
      onClick={onClick}
      transition="background 0.2s"
    >
      <VStack align="start" spacing={1}>
        <Text fontWeight="bold" fontSize="sm" noOfLines={1}>
          {record.taxon_name || 'Unknown Species'}
        </Text>
        <Text fontSize="xs" color="gray.500" noOfLines={1}>
          {record.site_name || 'Unknown Site'}
        </Text>
        <HStack spacing={2} flexWrap="wrap">
          {record.collection_date && (
            <Badge size="sm" colorScheme="blue">
              {new Date(record.collection_date).toLocaleDateString()}
            </Badge>
          )}
          {record.iucn_status && (
            <Badge size="sm" colorScheme={getIUCNColor(record.iucn_status)}>
              {record.iucn_status}
            </Badge>
          )}
          {record.endemism && (
            <Badge size="sm" colorScheme="purple">
              {record.endemism}
            </Badge>
          )}
        </HStack>
      </VStack>
    </Box>
  );
};

interface SearchResultsProps {
  onRecordSelect?: (record: BiologicalRecord) => void;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  onRecordSelect,
}) => {
  const { results, page, totalPages, setPage, search } = useSearchStore();

  const handleRecordClick = useCallback(
    (record: BiologicalRecord) => {
      if (onRecordSelect) {
        onRecordSelect(record);
      }
    },
    [onRecordSelect]
  );

  const handlePrevPage = useCallback(() => {
    if (page > 1) {
      setPage(page - 1);
      search();
    }
  }, [page, setPage, search]);

  const handleNextPage = useCallback(() => {
    if (page < totalPages) {
      setPage(page + 1);
      search();
    }
  }, [page, totalPages, setPage, search]);

  if (!results || results.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="gray.500">No results found</Text>
        <Text fontSize="sm" color="gray.400" mt={2}>
          Try adjusting your filters or search query
        </Text>
      </Box>
    );
  }

  return (
    <VStack spacing={3} align="stretch">
      {results.map((record) => (
        <ResultCard
          key={record.id}
          record={record}
          onClick={() => handleRecordClick(record)}
        />
      ))}

      {/* Pagination */}
      {totalPages > 1 && (
        <HStack justify="center" pt={4} spacing={4}>
          <IconButton
            aria-label="Previous page"
            icon={<ChevronLeftIcon />}
            size="sm"
            variant="outline"
            isDisabled={page <= 1}
            onClick={handlePrevPage}
          />
          <Text fontSize="sm" color="gray.500">
            Page {page} of {totalPages}
          </Text>
          <IconButton
            aria-label="Next page"
            icon={<ChevronRightIcon />}
            size="sm"
            variant="outline"
            isDisabled={page >= totalPages}
            onClick={handleNextPage}
          />
        </HStack>
      )}
    </VStack>
  );
};

export default SearchResults;
