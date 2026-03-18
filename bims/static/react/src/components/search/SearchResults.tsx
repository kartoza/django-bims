/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Search Results - Display filter summary with biodiversity data and dashboard links
 * Matches the original BIMS results panel structure.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  VStack,
  HStack,
  Box,
  Text,
  Badge,
  Button,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Skeleton,
  Image,
  Grid,
  GridItem,
  Divider,
  useColorModeValue,
  IconButton,
  Tooltip,
  Collapse,
} from '@chakra-ui/react';
import { ChevronDownIcon, ChevronUpIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, ArcElement, Tooltip as ChartTooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { useSearchStore } from '../../stores/searchStore';
import { apiClient } from '../../api/client';
import type { BiologicalRecord } from '../../types';

// Register Chart.js components
ChartJS.register(ArcElement, ChartTooltip, Legend);

// Chart colors matching the original BIMS
const CHART_COLORS = [
  '#8D2641', '#D7CD47', '#18A090', '#A2CE89', '#4E6440', '#525351',
  '#641f30', '#E6E188', '#9D9739', '#618295', '#2C495A', '#39B2A3',
];

// IUCN category colors
const IUCN_COLORS: Record<string, string> = {
  'CR': '#d41159',
  'EN': '#e66100',
  'VU': '#ffc107',
  'NT': '#5c88da',
  'LC': '#17a2b8',
  'DD': '#6c757d',
  'NE': '#adb5bd',
};

interface FilterSummaryData {
  total_sites: number;
  total_occurrences: number;
  total_taxa: number;
  date_range: {
    earliest: string | null;
    latest: string | null;
  };
  biodiversity_data: Record<string, {
    module_id: number;
    icon: string | null;
    occurrences: number;
    number_of_sites: number;
    number_of_taxa: number;
    origin: Array<{ name: string; count: number }>;
    endemism: Array<{ name: string; count: number }>;
    cons_status: Array<{ name: string; count: number }>;
  }>;
  species_list: Array<{
    id: number;
    name: string;
    rank: string;
    occurrences: number;
    sites: number;
  }>;
}

const MiniPieChart: React.FC<{
  data: Array<{ name: string; count: number }>;
  colorMap?: Record<string, string>;
  size?: number;
}> = ({ data, colorMap, size = 50 }) => {
  if (!data || data.length === 0) {
    return <Box w={`${size}px`} h={`${size}px`} bg="gray.100" borderRadius="full" />;
  }

  const chartData = {
    labels: data.map(d => d.name),
    datasets: [{
      data: data.map(d => d.count),
      backgroundColor: data.map((d, i) =>
        colorMap?.[d.name] || CHART_COLORS[i % CHART_COLORS.length]
      ),
      borderWidth: 0,
    }],
  };

  const options = {
    responsive: false,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: true },
    },
  };

  return (
    <Box w={`${size}px`} h={`${size}px`}>
      <Pie data={chartData} options={options} width={size} height={size} />
    </Box>
  );
};

interface SearchResultsProps {
  onRecordSelect?: (record: BiologicalRecord) => void;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  onRecordSelect,
}) => {
  const navigate = useNavigate();
  const { filters, filterVersion } = useSearchStore();
  const [summaryData, setSummaryData] = useState<FilterSummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSpecies, setShowSpecies] = useState(false);

  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Build API params from filters
  const buildParams = useCallback(() => {
    const params: Record<string, string> = {};

    if (filters.taxonGroups && filters.taxonGroups.length > 0) {
      params.taxon_group = String(filters.taxonGroups[0]);
    }
    if (filters.yearFrom) {
      params.year_from = String(filters.yearFrom);
    }
    if (filters.yearTo) {
      params.year_to = String(filters.yearTo);
    }
    if (filters.iucnCategories && filters.iucnCategories.length > 0) {
      params.iucn_category = filters.iucnCategories.join(',');
    }
    if (filters.endemism && filters.endemism.length > 0) {
      params.endemism = filters.endemism.join(',');
    }
    if (filters.collectors && filters.collectors.length > 0) {
      params.collector = filters.collectors.join(',');
    }
    if (filters.validated !== undefined) {
      params.validated = String(filters.validated);
    }
    if (filters.search) {
      params.search = filters.search;
    }
    if (filters.boundaryId) {
      params.boundary = String(filters.boundaryId);
    }
    if (filters.bbox) {
      params.bbox = filters.bbox;
    }

    return params;
  }, [filters]);

  // Load filter summary when filters change
  useEffect(() => {
    const loadSummary = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const params = buildParams();
        const response = await apiClient.get<{ data: FilterSummaryData }>(
          'records/filter-summary/',
          { params }
        );
        setSummaryData(response.data?.data || null);
      } catch (err) {
        console.error('Failed to load filter summary:', err);
        setError('Failed to load summary');
      } finally {
        setIsLoading(false);
      }
    };

    loadSummary();
  }, [filterVersion, buildParams]);

  if (isLoading) {
    return (
      <VStack spacing={4} align="stretch">
        <Skeleton height="60px" />
        <Skeleton height="100px" />
        <Skeleton height="80px" />
      </VStack>
    );
  }

  if (error) {
    return (
      <Box textAlign="center" py={4}>
        <Text color="red.500">{error}</Text>
      </Box>
    );
  }

  if (!summaryData || summaryData.total_occurrences === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="gray.500">No results found</Text>
        <Text fontSize="sm" color="gray.400" mt={2}>
          Try adjusting your filters or search query
        </Text>
      </Box>
    );
  }

  const { total_sites, total_occurrences, total_taxa, biodiversity_data, species_list } = summaryData;

  return (
    <VStack spacing={4} align="stretch">
      {/* Summary Stats */}
      <StatGroup>
        <Stat size="sm">
          <StatLabel fontSize="xs">Sites</StatLabel>
          <StatNumber fontSize="lg">{total_sites.toLocaleString()}</StatNumber>
        </Stat>
        <Stat size="sm">
          <StatLabel fontSize="xs">Occurrences</StatLabel>
          <StatNumber fontSize="lg">{total_occurrences.toLocaleString()}</StatNumber>
        </Stat>
        <Stat size="sm">
          <StatLabel fontSize="xs">Taxa</StatLabel>
          <StatNumber fontSize="lg">{total_taxa.toLocaleString()}</StatNumber>
        </Stat>
      </StatGroup>

      {/* Multi-site Dashboard Button */}
      <Button
        size="sm"
        colorScheme="blue"
        width="100%"
        onClick={() => navigate('/analytics')}
        rightIcon={<ExternalLinkIcon />}
      >
        Multi-site Summary Dashboard
      </Button>

      <Divider />

      {/* Biodiversity Data by Module */}
      <Text fontWeight="bold" fontSize="sm">Biodiversity Data</Text>

      {Object.entries(biodiversity_data).map(([moduleName, moduleData]) => (
        <Box
          key={moduleName}
          p={3}
          bg={bgColor}
          borderRadius="md"
          border="1px"
          borderColor={borderColor}
        >
          {/* Module Header */}
          <HStack justify="space-between" mb={2}>
            <HStack>
              {moduleData.icon && (
                <Image
                  src={`/uploaded/${moduleData.icon}`}
                  alt={moduleName}
                  boxSize="24px"
                  objectFit="contain"
                />
              )}
              <Text fontWeight="medium" fontSize="sm">{moduleName}</Text>
            </HStack>
            <Badge colorScheme="blue">{moduleData.occurrences} records</Badge>
          </HStack>

          {/* Stats Row */}
          <HStack spacing={4} fontSize="xs" color="gray.600" mb={2}>
            <Text>{moduleData.number_of_sites} sites</Text>
            <Text>{moduleData.number_of_taxa} taxa</Text>
          </HStack>

          {/* Mini Charts */}
          <Grid templateColumns="repeat(3, 1fr)" gap={2} mb={2}>
            <GridItem>
              <VStack spacing={0}>
                <Text fontSize="xs" color="gray.500">Origin</Text>
                <MiniPieChart data={moduleData.origin} size={40} />
              </VStack>
            </GridItem>
            <GridItem>
              <VStack spacing={0}>
                <Text fontSize="xs" color="gray.500">Endemic</Text>
                <MiniPieChart data={moduleData.endemism} size={40} />
              </VStack>
            </GridItem>
            <GridItem>
              <VStack spacing={0}>
                <Text fontSize="xs" color="gray.500">IUCN</Text>
                <MiniPieChart data={moduleData.cons_status} colorMap={IUCN_COLORS} size={40} />
              </VStack>
            </GridItem>
          </Grid>

          {/* Dashboard Link */}
          <Button
            size="xs"
            variant="outline"
            colorScheme="blue"
            width="100%"
            onClick={() => navigate(`/analytics?module=${moduleData.module_id}`)}
          >
            {moduleName} Dashboard
          </Button>
        </Box>
      ))}

      <Divider />

      {/* Species List */}
      <HStack justify="space-between">
        <Text fontWeight="bold" fontSize="sm">Species List</Text>
        <IconButton
          aria-label="Toggle species list"
          icon={showSpecies ? <ChevronUpIcon /> : <ChevronDownIcon />}
          size="xs"
          variant="ghost"
          onClick={() => setShowSpecies(!showSpecies)}
        />
      </HStack>

      <Collapse in={showSpecies}>
        <VStack spacing={2} align="stretch">
          {species_list.map((species) => (
            <HStack
              key={species.id}
              p={2}
              bg={bgColor}
              borderRadius="md"
              justify="space-between"
              cursor="pointer"
              _hover={{ bg: 'gray.100' }}
              onClick={() => navigate(`/map/taxon/${species.id}`)}
            >
              <VStack align="start" spacing={0}>
                <Text fontSize="sm" fontWeight="medium" fontStyle="italic">
                  {species.name}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {species.rank}
                </Text>
              </VStack>
              <VStack align="end" spacing={0}>
                <Badge size="sm" colorScheme="blue">{species.occurrences}</Badge>
                <Text fontSize="xs" color="gray.500">{species.sites} sites</Text>
              </VStack>
            </HStack>
          ))}

          {species_list.length > 0 && (
            <Button
              size="xs"
              variant="link"
              colorScheme="blue"
              onClick={() => navigate('/analytics?tab=species')}
            >
              View all species &rarr;
            </Button>
          )}
        </VStack>
      </Collapse>

      <Divider />

      {/* Download Button */}
      <Button
        size="sm"
        variant="outline"
        width="100%"
        onClick={() => navigate('/downloads')}
      >
        Download Data
      </Button>
    </VStack>
  );
};

export default SearchResults;
