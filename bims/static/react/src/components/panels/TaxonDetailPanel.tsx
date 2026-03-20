/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Taxon Detail Panel - Display detailed information about a taxon
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
  Wrap,
  WrapItem,
  Image,
  AspectRatio,
  Grid,
  GridItem,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Spinner,
} from '@chakra-ui/react';
import { CloseIcon, ChevronLeftIcon, ChevronRightIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import { taxonDetailApi, TaxonDetailResponse } from '../../api/client';
import type { BiologicalRecord } from '../../types';

interface TaxonDetailPanelProps {
  taxonId: number;
  onClose: () => void;
  onTaxonSelect?: (taxonId: number) => void;
}

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

export const TaxonDetailPanel: React.FC<TaxonDetailPanelProps> = ({
  taxonId,
  onClose,
  onTaxonSelect,
}) => {
  const [taxon, setTaxon] = useState<TaxonDetailResponse | null>(null);
  const [records, setRecords] = useState<BiologicalRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingRecords, setIsLoadingRecords] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordsPage, setRecordsPage] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Fetch taxon details
  useEffect(() => {
    const fetchTaxon = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await taxonDetailApi.getDetail(taxonId);
        setTaxon(data);
      } catch (err) {
        setError('Failed to load taxon details');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTaxon();
  }, [taxonId]);

  // Fetch taxon records
  const fetchRecords = useCallback(async () => {
    setIsLoadingRecords(true);
    try {
      const response = await taxonDetailApi.getRecords(taxonId, {
        page: recordsPage,
        page_size: 10,
      });
      setRecords(response?.data || response?.results || []);
      setTotalRecords(response?.meta?.count || response?.count || 0);
    } catch (err) {
      console.error('Failed to load records:', err);
    } finally {
      setIsLoadingRecords(false);
    }
  }, [taxonId, recordsPage]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const handleHierarchyClick = useCallback(
    (id: number) => {
      if (onTaxonSelect) {
        onTaxonSelect(id);
      }
    },
    [onTaxonSelect]
  );

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

  if (error || !taxon) {
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
        <Text color="red.500">{error || 'Taxon not found'}</Text>
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
      <HStack
        p={4}
        borderBottom="1px"
        borderColor={borderColor}
        justify="space-between"
      >
        <HStack>
          <IconButton
            aria-label="Back"
            icon={<ChevronLeftIcon />}
            variant="ghost"
            size="sm"
            onClick={onClose}
          />
          <VStack align="start" spacing={0}>
            <Heading size="md" noOfLines={1} fontStyle="italic">
              {taxon.scientific_name}
            </Heading>
            {taxon.common_name && (
              <Text fontSize="sm" color="gray.500">
                {taxon.common_name}
              </Text>
            )}
          </VStack>
        </HStack>
        <HStack>
          <Badge textTransform="capitalize">{taxon.rank}</Badge>
          {taxon.iucn_status && (
            <Badge colorScheme={getIUCNColor(taxon.iucn_status.category)}>
              {taxon.iucn_status.category}
            </Badge>
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
            <Tab>Classification</Tab>
            {taxon.images && taxon.images.length > 0 && <Tab>Images</Tab>}
          </TabList>

          <TabPanels>
            {/* Overview Tab */}
            <TabPanel>
              <VStack spacing={4} align="stretch">
                {/* Stats */}
                <StatGroup>
                  <Stat>
                    <StatLabel>Records</StatLabel>
                    <StatNumber>{taxon.count || taxon.record_count || 0}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Sites</StatLabel>
                    <StatNumber>{taxon.total_sites || 0}</StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Status</StatLabel>
                    <StatNumber fontSize="md">
                      {taxon.iucn_status?.category || 'NE'}
                    </StatNumber>
                  </Stat>
                </StatGroup>

                {/* Origin */}
                {taxon.origin && (
                  <>
                    <Box>
                      <Heading size="sm" mb={2}>
                        Origin
                      </Heading>
                      <Badge colorScheme={taxon.origin === 'Indigenous' ? 'green' : 'orange'}>
                        {taxon.origin}
                      </Badge>
                    </Box>
                    <Divider />
                  </>
                )}

                <Divider />

                {/* Taxonomy Info */}
                <Box>
                  <Heading size="sm" mb={2}>
                    Taxonomy
                  </Heading>
                  <Table size="sm" variant="simple">
                    <Tbody>
                      <Tr>
                        <Td fontWeight="medium">Scientific Name</Td>
                        <Td fontStyle="italic">{taxon.scientific_name}</Td>
                      </Tr>
                      <Tr>
                        <Td fontWeight="medium">Canonical Name</Td>
                        <Td fontStyle="italic">{taxon.canonical_name}</Td>
                      </Tr>
                      <Tr>
                        <Td fontWeight="medium">Rank</Td>
                        <Td textTransform="capitalize">{taxon.rank}</Td>
                      </Tr>
                      <Tr>
                        <Td fontWeight="medium">Status</Td>
                        <Td>{taxon.taxonomic_status}</Td>
                      </Tr>
                      {taxon.author && (
                        <Tr>
                          <Td fontWeight="medium">Author</Td>
                          <Td>{taxon.author}</Td>
                        </Tr>
                      )}
                      {taxon.gbif_key && (
                        <Tr>
                          <Td fontWeight="medium">GBIF</Td>
                          <Td>
                            <HStack spacing={2}>
                              <Text>{taxon.gbif_key}</Text>
                              <IconButton
                                as="a"
                                href={`https://www.gbif.org/species/${taxon.gbif_key}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                aria-label="View on GBIF"
                                icon={<ExternalLinkIcon />}
                                size="xs"
                                variant="ghost"
                              />
                            </HStack>
                          </Td>
                        </Tr>
                      )}
                    </Tbody>
                  </Table>
                </Box>

                {/* Conservation Status */}
                {(taxon.iucn_status || taxon.national_conservation_status) && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>
                        Conservation Status
                      </Heading>
                      <VStack spacing={2} align="stretch">
                        {taxon.iucn_status && (
                          <HStack justify="space-between">
                            <Text fontSize="sm">IUCN Global</Text>
                            <Badge
                              colorScheme={getIUCNColor(
                                taxon.iucn_status.category
                              )}
                            >
                              {taxon.iucn_status.category}
                            </Badge>
                          </HStack>
                        )}
                        {taxon.national_conservation_status && (
                          <HStack justify="space-between">
                            <Text fontSize="sm">National</Text>
                            <Badge
                              colorScheme={getIUCNColor(
                                taxon.national_conservation_status.category
                              )}
                            >
                              {taxon.national_conservation_status.category}
                            </Badge>
                          </HStack>
                        )}
                      </VStack>
                    </Box>
                  </>
                )}

                {/* Endemism */}
                {taxon.endemism && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>
                        Endemism
                      </Heading>
                      <Badge colorScheme="purple">{taxon.endemism.name}</Badge>
                      {taxon.endemism.description && (
                        <Text fontSize="sm" mt={1} color="gray.600">
                          {taxon.endemism.description}
                        </Text>
                      )}
                    </Box>
                  </>
                )}

                {/* Vernacular Names */}
                {taxon.vernacular_names && taxon.vernacular_names.length > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>
                        Common Names
                      </Heading>
                      <Wrap spacing={2}>
                        {taxon.vernacular_names.map((vn) => (
                          <WrapItem key={vn.id}>
                            <Badge variant="outline">
                              {vn.name}
                              {vn.language && (
                                <Text as="span" fontSize="xs" ml={1}>
                                  ({vn.language})
                                </Text>
                              )}
                            </Badge>
                          </WrapItem>
                        ))}
                      </Wrap>
                    </Box>
                  </>
                )}

                {/* Tags */}
                {taxon.tags && taxon.tags.length > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>
                        Tags
                      </Heading>
                      <Wrap spacing={2}>
                        {taxon.tags.map((tag, i) => (
                          <WrapItem key={i}>
                            <Badge colorScheme="blue">{tag}</Badge>
                          </WrapItem>
                        ))}
                      </Wrap>
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
                    No records found for this taxon
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
                              {record.site_name}
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

            {/* Classification Tab */}
            <TabPanel>
              <VStack spacing={4} align="stretch">
                {/* Taxonomic Rank Fields */}
                {(taxon.kingdom || taxon.phylum || taxon.class_name || taxon.order || taxon.family || taxon.genus || taxon.species) && (
                  <Box>
                    <Heading size="sm" mb={3}>
                      Classification
                    </Heading>
                    <Table size="sm" variant="simple">
                      <Tbody>
                        {taxon.kingdom && (
                          <Tr>
                            <Td fontWeight="medium" width="100px">Kingdom</Td>
                            <Td>{taxon.kingdom}</Td>
                          </Tr>
                        )}
                        {taxon.phylum && (
                          <Tr>
                            <Td fontWeight="medium">Phylum</Td>
                            <Td>{taxon.phylum}</Td>
                          </Tr>
                        )}
                        {taxon.class_name && (
                          <Tr>
                            <Td fontWeight="medium">Class</Td>
                            <Td>{taxon.class_name}</Td>
                          </Tr>
                        )}
                        {taxon.order && (
                          <Tr>
                            <Td fontWeight="medium">Order</Td>
                            <Td>{taxon.order}</Td>
                          </Tr>
                        )}
                        {taxon.family && (
                          <Tr>
                            <Td fontWeight="medium">Family</Td>
                            <Td>{taxon.family}</Td>
                          </Tr>
                        )}
                        {taxon.genus && (
                          <Tr>
                            <Td fontWeight="medium">Genus</Td>
                            <Td fontStyle="italic">{taxon.genus}</Td>
                          </Tr>
                        )}
                        {taxon.species && (
                          <Tr>
                            <Td fontWeight="medium">Species</Td>
                            <Td fontStyle="italic">{taxon.species}</Td>
                          </Tr>
                        )}
                      </Tbody>
                    </Table>
                  </Box>
                )}

                {/* Hierarchy (visual tree) */}
                {taxon.hierarchy && taxon.hierarchy.length > 0 && (
                  <Box>
                    <Heading size="sm" mb={3}>
                      Taxonomic Hierarchy
                    </Heading>
                    <VStack spacing={1} align="stretch">
                      {taxon.hierarchy.map((level, index) => (
                        <HStack
                          key={level.id}
                          pl={index * 4}
                          py={1}
                          _hover={{ bg: 'gray.50' }}
                          cursor="pointer"
                          onClick={() => handleHierarchyClick(level.id)}
                          borderRadius="md"
                        >
                          <Badge
                            size="sm"
                            variant="outline"
                            textTransform="capitalize"
                          >
                            {level.rank}
                          </Badge>
                          <Text
                            fontSize="sm"
                            fontStyle={
                              ['genus', 'species', 'subspecies'].includes(
                                level.rank.toLowerCase()
                              )
                                ? 'italic'
                                : 'normal'
                            }
                          >
                            {level.name}
                          </Text>
                          <ChevronRightIcon color="gray.400" />
                        </HStack>
                      ))}
                    </VStack>
                  </Box>
                )}

                {/* Parent */}
                {taxon.parent && (
                  <>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={2}>
                        Parent Taxon
                      </Heading>
                      <HStack
                        p={2}
                        borderRadius="md"
                        border="1px"
                        borderColor={borderColor}
                        cursor="pointer"
                        _hover={{ bg: 'gray.50' }}
                        onClick={() => handleHierarchyClick(taxon.parent!.id)}
                      >
                        <Badge textTransform="capitalize">
                          {taxon.parent.rank}
                        </Badge>
                        <Text fontStyle="italic">
                          {taxon.parent.scientific_name}
                        </Text>
                      </HStack>
                    </Box>
                  </>
                )}

                {/* Biographic Distributions */}
                {taxon.biographic_distributions &&
                  taxon.biographic_distributions.length > 0 && (
                    <>
                      <Divider />
                      <Box>
                        <Heading size="sm" mb={2}>
                          Distribution
                        </Heading>
                        <Wrap spacing={2}>
                          {taxon.biographic_distributions.map((dist, i) => (
                            <WrapItem key={i}>
                              <Badge
                                colorScheme={dist.doubtful ? 'yellow' : 'green'}
                              >
                                {dist.name}
                                {dist.doubtful && ' (?)'}
                              </Badge>
                            </WrapItem>
                          ))}
                        </Wrap>
                      </Box>
                    </>
                  )}
              </VStack>
            </TabPanel>

            {/* Images Tab */}
            {taxon.images && taxon.images.length > 0 && (
              <TabPanel>
                <Grid templateColumns="repeat(2, 1fr)" gap={3}>
                  {taxon.images.map((image) => (
                    <GridItem key={image.id}>
                      <AspectRatio ratio={1}>
                        <Image
                          src={image.url || ''}
                          alt={taxon.scientific_name}
                          objectFit="cover"
                          borderRadius="md"
                          fallbackSrc="https://via.placeholder.com/150?text=No+Image"
                        />
                      </AspectRatio>
                    </GridItem>
                  ))}
                </Grid>
              </TabPanel>
            )}
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
        {taxon.verified ? (
          <Badge colorScheme="green" mr={2}>
            Verified
          </Badge>
        ) : (
          <Badge colorScheme="yellow" mr={2}>
            Unverified
          </Badge>
        )}
        ID: {taxon.id}
      </Box>
    </Box>
  );
};

export default TaxonDetailPanel;
