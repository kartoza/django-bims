/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Spatial Dashboard - Display aggregated statistics for filtered spatial data
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useMemo } from 'react';
import {
  Box,
  VStack,
  HStack,
  SimpleGrid,
  Heading,
  Text,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Card,
  CardBody,
  CardHeader,
  Skeleton,
  SkeletonText,
  Progress,
  Badge,
  Divider,
  useColorModeValue,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import {
  useSpatialSummary,
  useConservationStatus,
} from '../../hooks/useSpatialDashboard';
import { useSearchStore } from '../../stores/searchStore';

interface SpatialDashboardProps {
  compact?: boolean;
}

export const SpatialDashboard: React.FC<SpatialDashboardProps> = ({
  compact = false,
}) => {
  const { filters } = useSearchStore();
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Convert store filters to API format
  const apiFilters = useMemo(() => {
    const params: Record<string, unknown> = {};

    if (filters.taxonGroups?.length) {
      params.taxonGroup = filters.taxonGroups.join(',');
    }
    if (filters.yearFrom) {
      params.yearFrom = filters.yearFrom;
    }
    if (filters.yearTo) {
      params.yearTo = filters.yearTo;
    }
    if (filters.iucnCategories?.length) {
      params.conservationStatus = filters.iucnCategories.join(',');
    }
    if (filters.endemism?.length) {
      params.endemic = filters.endemism.join(',');
    }
    if (filters.boundaryId) {
      params.boundary = filters.boundaryId;
    }

    return params;
  }, [filters]);

  const hasFilters = Object.keys(apiFilters).length > 0;

  // Fetch summary data
  const {
    data: summaryData,
    isLoading: isLoadingSummary,
    isPolling: isPollingSummary,
    error: summaryError,
  } = useSpatialSummary(apiFilters, hasFilters);

  // Fetch conservation status data
  const {
    data: consData,
    isLoading: isLoadingCons,
    isPolling: isPollingCons,
    error: consError,
  } = useConservationStatus(apiFilters, hasFilters);

  const isLoading = isLoadingSummary || isLoadingCons;
  const isPolling = isPollingSummary || isPollingCons;
  const error = summaryError || consError;

  // Format large numbers
  const formatNumber = (num: number | undefined): string => {
    if (!num) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  if (!hasFilters) {
    return (
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardBody>
          <VStack spacing={3} py={4}>
            <Text color="gray.500" textAlign="center">
              Apply filters to view spatial dashboard data
            </Text>
            <Text fontSize="sm" color="gray.400" textAlign="center">
              Select taxon groups, date ranges, or boundaries to generate
              statistics
            </Text>
          </VStack>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert status="error" borderRadius="md">
        <AlertIcon />
        <Text fontSize="sm">{error}</Text>
      </Alert>
    );
  }

  if (compact) {
    return (
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardBody py={3}>
          {isLoading ? (
            <SimpleGrid columns={3} spacing={4}>
              <Skeleton height="50px" />
              <Skeleton height="50px" />
              <Skeleton height="50px" />
            </SimpleGrid>
          ) : (
            <>
              {isPolling && (
                <Progress size="xs" isIndeterminate colorScheme="blue" mb={2} />
              )}
              <SimpleGrid columns={3} spacing={4}>
                <Stat size="sm">
                  <StatLabel fontSize="xs">Occurrences</StatLabel>
                  <StatNumber fontSize="lg">
                    {formatNumber(summaryData?.total_occurrences)}
                  </StatNumber>
                </Stat>
                <Stat size="sm">
                  <StatLabel fontSize="xs">Taxa</StatLabel>
                  <StatNumber fontSize="lg">
                    {formatNumber(summaryData?.total_taxa)}
                  </StatNumber>
                </Stat>
                <Stat size="sm">
                  <StatLabel fontSize="xs">Sites</StatLabel>
                  <StatNumber fontSize="lg">
                    {formatNumber(summaryData?.total_sites)}
                  </StatNumber>
                </Stat>
              </SimpleGrid>
            </>
          )}
        </CardBody>
      </Card>
    );
  }

  return (
    <VStack spacing={4} align="stretch">
      {/* Summary Stats */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader py={3}>
          <HStack justify="space-between">
            <Heading size="sm">Filtered Area Summary</Heading>
            {isPolling && (
              <Badge colorScheme="blue" variant="subtle">
                Updating...
              </Badge>
            )}
          </HStack>
        </CardHeader>
        <CardBody pt={0}>
          {isLoading ? (
            <SimpleGrid columns={{ base: 2, md: 3 }} spacing={4}>
              <Skeleton height="80px" />
              <Skeleton height="80px" />
              <Skeleton height="80px" />
            </SimpleGrid>
          ) : (
            <SimpleGrid columns={{ base: 2, md: 3 }} spacing={4}>
              <Stat>
                <StatLabel>Total Occurrences</StatLabel>
                <StatNumber color="blue.500">
                  {formatNumber(summaryData?.total_occurrences)}
                </StatNumber>
                <StatHelpText>Species records</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Unique Taxa</StatLabel>
                <StatNumber color="green.500">
                  {formatNumber(summaryData?.total_taxa)}
                </StatNumber>
                <StatHelpText>Species identified</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Monitoring Sites</StatLabel>
                <StatNumber color="purple.500">
                  {formatNumber(summaryData?.total_sites)}
                </StatNumber>
                <StatHelpText>Locations sampled</StatHelpText>
              </Stat>
            </SimpleGrid>
          )}
        </CardBody>
      </Card>

      {/* Origin Distribution */}
      {summaryData?.origins && Object.keys(summaryData.origins).length > 0 && (
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader py={3}>
            <Heading size="sm">Origin Distribution</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <VStack spacing={2} align="stretch">
              {Object.entries(summaryData.origins).map(([origin, count]) => {
                const total = Object.values(summaryData.origins!).reduce(
                  (a, b) => a + b,
                  0
                );
                const percentage = ((count / total) * 100).toFixed(1);
                return (
                  <HStack key={origin} justify="space-between">
                    <Text fontSize="sm">{origin}</Text>
                    <HStack spacing={2}>
                      <Progress
                        value={parseFloat(percentage)}
                        size="sm"
                        width="100px"
                        colorScheme={origin === 'Indigenous' ? 'green' : 'orange'}
                        borderRadius="full"
                      />
                      <Text fontSize="sm" fontWeight="medium" minW="50px">
                        {percentage}%
                      </Text>
                    </HStack>
                  </HStack>
                );
              })}
            </VStack>
          </CardBody>
        </Card>
      )}

      {/* Conservation Status */}
      {consData && (
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader py={3}>
            <Heading size="sm">Conservation Status</Heading>
          </CardHeader>
          <CardBody pt={0}>
            {isLoadingCons ? (
              <SkeletonText noOfLines={5} spacing={3} />
            ) : (
              <VStack spacing={2} align="stretch">
                {consData.labels?.map((label, index) => {
                  const count = consData.data?.[index] || 0;
                  const total = consData.data?.reduce((a, b) => a + b, 0) || 1;
                  const percentage = ((count / total) * 100).toFixed(1);
                  const color = consData.colors?.[index] || '#888';

                  return (
                    <HStack key={label} justify="space-between">
                      <HStack spacing={2}>
                        <Box
                          w={3}
                          h={3}
                          borderRadius="sm"
                          bg={color}
                        />
                        <Text fontSize="sm">{label}</Text>
                      </HStack>
                      <HStack spacing={2}>
                        <Text fontSize="sm" color="gray.500">
                          {count}
                        </Text>
                        <Badge variant="subtle">{percentage}%</Badge>
                      </HStack>
                    </HStack>
                  );
                })}
              </VStack>
            )}
          </CardBody>
        </Card>
      )}

      {/* Endemism */}
      {summaryData?.endemism && Object.keys(summaryData.endemism).length > 0 && (
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader py={3}>
            <Heading size="sm">Endemism</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <VStack spacing={2} align="stretch">
              {Object.entries(summaryData.endemism).map(([status, count]) => {
                const total = Object.values(summaryData.endemism!).reduce(
                  (a, b) => a + b,
                  0
                );
                const percentage = ((count / total) * 100).toFixed(1);
                return (
                  <HStack key={status} justify="space-between">
                    <Text fontSize="sm">{status}</Text>
                    <HStack spacing={2}>
                      <Progress
                        value={parseFloat(percentage)}
                        size="sm"
                        width="100px"
                        colorScheme="purple"
                        borderRadius="full"
                      />
                      <Text fontSize="sm" fontWeight="medium" minW="50px">
                        {percentage}%
                      </Text>
                    </HStack>
                  </HStack>
                );
              })}
            </VStack>
          </CardBody>
        </Card>
      )}
    </VStack>
  );
};

export default SpatialDashboard;
