/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Site Detail Panel - Display detailed information about a location site
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Badge,
  Divider,
  IconButton,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Skeleton,
  SkeletonText,
  useColorModeValue,
  Button,
  Link,
  Spinner,
} from '@chakra-ui/react';
import { CloseIcon, ExternalLinkIcon, ChevronLeftIcon } from '@chakra-ui/icons';
import { apiClient } from '../../api/client';
import type { LocationSiteDetail, BiologicalRecord } from '../../types';

interface SiteDetailPanelProps {
  siteId: number;
  onClose: () => void;
  onFlyTo?: (coords: [number, number], zoom?: number) => void;
}

export const SiteDetailPanel: React.FC<SiteDetailPanelProps> = ({
  siteId,
  onClose,
  onFlyTo,
}) => {
  const [site, setSite] = useState<LocationSiteDetail | null>(null);
  const [records, setRecords] = useState<BiologicalRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingRecords, setIsLoadingRecords] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordsPage, setRecordsPage] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Fetch site details
  useEffect(() => {
    const fetchSite = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<{ data: LocationSiteDetail }>(
          `/api/v1/sites/${siteId}/`
        );
        setSite(response.data?.data || null);

        // Fly to site location
        if (response.data?.data?.coordinates && onFlyTo) {
          const { latitude, longitude } = response.data.data.coordinates;
          onFlyTo([longitude, latitude], 14);
        }
      } catch (err) {
        setError('Failed to load site details');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSite();
  }, [siteId, onFlyTo]);

  // Fetch site records
  const fetchRecords = useCallback(async () => {
    setIsLoadingRecords(true);
    try {
      const response = await apiClient.get<{
        data: BiologicalRecord[];
        meta: { count: number };
      }>(`/api/v1/sites/${siteId}/records/`, {
        params: { page: recordsPage, page_size: 10 },
      });
      setRecords(response.data?.data || []);
      setTotalRecords(response.data?.meta?.count || 0);
    } catch (err) {
      console.error('Failed to load records:', err);
    } finally {
      setIsLoadingRecords(false);
    }
  }, [siteId, recordsPage]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  // Removed - handled by parent component

  if (isLoading) {
    return (
      <Box
        position="absolute"
        right={0}
        top={0}
        bottom={0}
        width="450px"
        bg={bgColor}
        borderLeft="1px"
        borderColor={borderColor}
        boxShadow="lg"
        zIndex={1000}
        p={4}
      >
        <VStack spacing={4} align="stretch">
          <Skeleton height="30px" />
          <SkeletonText noOfLines={4} spacing={2} />
          <Skeleton height="100px" />
          <SkeletonText noOfLines={6} spacing={2} />
        </VStack>
      </Box>
    );
  }

  if (error || !site) {
    return (
      <Box
        position="absolute"
        right={0}
        top={0}
        bottom={0}
        width="450px"
        bg={bgColor}
        borderLeft="1px"
        borderColor={borderColor}
        boxShadow="lg"
        zIndex={1000}
        p={4}
      >
        <HStack justify="space-between" mb={4}>
          <IconButton
            aria-label="Back"
            icon={<ChevronLeftIcon />}
            variant="ghost"
            onClick={onClose}
          />
          <IconButton
            aria-label="Close"
            icon={<CloseIcon />}
            variant="ghost"
            onClick={onClose}
          />
        </HStack>
        <Text color="red.500">{error || 'Site not found'}</Text>
      </Box>
    );
  }

  return (
    <Box
      position="absolute"
      right={0}
      top={0}
      bottom={0}
      width="450px"
      bg={bgColor}
      borderLeft="1px"
      borderColor={borderColor}
      boxShadow="lg"
      zIndex={1000}
      display="flex"
      flexDirection="column"
      overflow="hidden"
    >
      {/* Header */}
      <HStack p={4} borderBottom="1px" borderColor={borderColor} justify="space-between">
        <HStack>
          <IconButton
            aria-label="Back"
            icon={<ChevronLeftIcon />}
            variant="ghost"
            size="sm"
            onClick={onClose}
          />
          <VStack align="start" spacing={0}>
            <Heading size="md" noOfLines={1}>
              {site.name}
            </Heading>
            <Text fontSize="sm" color="gray.500">
              {site.site_code}
            </Text>
          </VStack>
        </HStack>
        <HStack>
          {site.validated && (
            <Badge colorScheme="green">Validated</Badge>
          )}
          <IconButton
            aria-label="Close"
            icon={<CloseIcon />}
            variant="ghost"
            size="sm"
            onClick={onClose}
          />
        </HStack>
      </HStack>

      {/* Content */}
      <Box flex={1} overflow="auto">
        <Tabs size="sm" colorScheme="blue" isLazy>
          <TabList px={4}>
            <Tab>Overview</Tab>
            <Tab>Records ({totalRecords})</Tab>
            <Tab>Context</Tab>
          </TabList>

          <TabPanels>
            {/* Overview Tab */}
            <TabPanel>
              <VStack spacing={4} align="stretch">
                {/* Stats */}
                <StatGroup>
                  <Stat>
                    <StatLabel>Records</StatLabel>
                    <StatNumber>{totalRecords}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Ecosystem</StatLabel>
                    <StatNumber fontSize="md">
                      {site.ecosystem_type || 'Unknown'}
                    </StatNumber>
                  </Stat>
                </StatGroup>

                <Divider />

                {/* Location Info */}
                <Box>
                  <Heading size="sm" mb={2}>
                    Location
                  </Heading>
                  <Table size="sm" variant="simple">
                    <Tbody>
                      {site.coordinates && (
                        <Tr>
                          <Td fontWeight="medium">Coordinates</Td>
                          <Td>
                            {site.coordinates.latitude.toFixed(6)},{' '}
                            {site.coordinates.longitude.toFixed(6)}
                          </Td>
                        </Tr>
                      )}
                      {site.river_name && (
                        <Tr>
                          <Td fontWeight="medium">River</Td>
                          <Td>{site.river_name}</Td>
                        </Tr>
                      )}
                      {site.location_type && (
                        <Tr>
                          <Td fontWeight="medium">Type</Td>
                          <Td>{site.location_type.name}</Td>
                        </Tr>
                      )}
                      {site.wetland_name && (
                        <Tr>
                          <Td fontWeight="medium">Wetland</Td>
                          <Td>{site.wetland_name}</Td>
                        </Tr>
                      )}
                    </Tbody>
                  </Table>
                </Box>

                {site.site_description && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>
                        Description
                      </Heading>
                      <Text fontSize="sm">{site.site_description}</Text>
                    </Box>
                  </>
                )}

                {/* Ownership */}
                {site.owner_name && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>
                        Ownership
                      </Heading>
                      <Text fontSize="sm">{site.owner_name}</Text>
                      {site.land_owner_detail && (
                        <Text fontSize="xs" color="gray.500">
                          {site.land_owner_detail}
                        </Text>
                      )}
                    </Box>
                  </>
                )}
              </VStack>
            </TabPanel>

            {/* Records Tab */}
            <TabPanel>
              <VStack spacing={3} align="stretch">
                {isLoadingRecords ? (
                  <HStack justify="center" py={4}>
                    <Spinner size="sm" />
                    <Text>Loading records...</Text>
                  </HStack>
                ) : records.length === 0 ? (
                  <Text color="gray.500" textAlign="center" py={4}>
                    No records found for this site
                  </Text>
                ) : (
                  <>
                    {records.map((record) => (
                      <Box
                        key={record.id}
                        p={3}
                        borderRadius="md"
                        border="1px"
                        borderColor={borderColor}
                        _hover={{ bg: 'gray.50' }}
                      >
                        <HStack justify="space-between">
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="bold" fontSize="sm">
                              {record.taxon_name}
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              {record.collection_date}
                            </Text>
                          </VStack>
                          {record.abundance_number && (
                            <Badge>{record.abundance_number}</Badge>
                          )}
                        </HStack>
                        {record.collector_name && (
                          <Text fontSize="xs" color="gray.500" mt={1}>
                            Collector: {record.collector_name}
                          </Text>
                        )}
                      </Box>
                    ))}

                    {totalRecords > 10 && (
                      <HStack justify="center" pt={2}>
                        <Button
                          size="sm"
                          variant="outline"
                          isDisabled={recordsPage === 1}
                          onClick={() => setRecordsPage((p) => p - 1)}
                        >
                          Previous
                        </Button>
                        <Text fontSize="sm" color="gray.500">
                          Page {recordsPage}
                        </Text>
                        <Button
                          size="sm"
                          variant="outline"
                          isDisabled={records.length < 10}
                          onClick={() => setRecordsPage((p) => p + 1)}
                        >
                          Next
                        </Button>
                      </HStack>
                    )}
                  </>
                )}
              </VStack>
            </TabPanel>

            {/* Context Tab */}
            <TabPanel>
              <VStack spacing={4} align="stretch">
                {site.location_context &&
                Object.keys(site.location_context).length > 0 ? (
                  <Table size="sm" variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Property</Th>
                        <Th>Value</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {Object.entries(site.location_context).map(
                        ([key, value]) => (
                          <Tr key={key}>
                            <Td fontWeight="medium">{key}</Td>
                            <Td>{String(value)}</Td>
                          </Tr>
                        )
                      )}
                    </Tbody>
                  </Table>
                ) : (
                  <Text color="gray.500" textAlign="center">
                    No context data available
                  </Text>
                )}

                {site.climate_data &&
                  Object.keys(site.climate_data).length > 0 && (
                    <>
                      <Divider />
                      <Heading size="sm">Climate Data</Heading>
                      <Table size="sm" variant="simple">
                        <Tbody>
                          {Object.entries(site.climate_data).map(
                            ([key, value]) => (
                              <Tr key={key}>
                                <Td fontWeight="medium">{key}</Td>
                                <Td>{String(value)}</Td>
                              </Tr>
                            )
                          )}
                        </Tbody>
                      </Table>
                    </>
                  )}
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Box>

      {/* Footer */}
      <Box
        p={3}
        borderTop="1px"
        borderColor={borderColor}
        fontSize="xs"
        color="gray.500"
        textAlign="center"
      >
        Last modified: {new Date(site.modified).toLocaleDateString()}
      </Box>
    </Box>
  );
};

export default SiteDetailPanel;
