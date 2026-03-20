/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Summary Report generation page - connected to real backend APIs.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardBody,
  CardHeader,
  FormControl,
  FormLabel,
  Select,
  Button,
  useToast,
  useColorModeValue,
  SimpleGrid,
  Checkbox,
  CheckboxGroup,
  Divider,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  Alert,
  AlertIcon,
  Spinner,
  Center,
  Link,
  Skeleton,
  SkeletonText,
} from '@chakra-ui/react';
import { DownloadIcon, RepeatIcon, ViewIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import axios from 'axios';
import { apiClient } from '../api/client';

interface SummaryData {
  total_sites: number;
  total_duplicated_sites: number;
  total_records: number;
  total_duplicate_records: number;
  total_modules: number;
  total_species: number;
  species_per_module: Record<string, Record<string, number>>;
  records_per_modules: Record<string, Record<string, number>>;
  sites_per_modules: Record<string, Record<string, number>>;
  total_records_per_source_collection: Record<string, number>;
  total_species_per_source_collection: Record<string, number>;
  total_sites_per_source_collection: Record<string, number>;
  _cached?: boolean;
  _cache_version?: string;
}

interface DownloadRequest {
  id: number;
  task_id: string;
  request_date: string;
  request_type: string;
  status: string;
  download_url: string | null;
  progress: number;
  resource_name?: string;
  resource_type?: string;
  approved?: boolean;
  rejected?: boolean;
  processing?: boolean;
}

interface TaxonGroup {
  id: number;
  name: string;
  logo?: string;
}

const SummaryReportPage: React.FC = () => {
  const toast = useToast();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  // State
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [downloads, setDownloads] = useState<DownloadRequest[]>([]);
  const [loadingDownloads, setLoadingDownloads] = useState(true);
  const [taxonGroups, setTaxonGroups] = useState<TaxonGroup[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [pollingTaskId, setPollingTaskId] = useState<string | null>(null);

  // Report config
  const [reportType, setReportType] = useState('csv');
  const [selectedTaxonGroup, setSelectedTaxonGroup] = useState('');

  // Fetch summary data (uses legacy API endpoint, not v1)
  const fetchSummaryData = useCallback(async (forceRefresh = false) => {
    setLoadingSummary(true);
    try {
      // Use axios directly since this is a legacy endpoint, not under /api/v1/
      const url = forceRefresh
        ? '/api/summary-general-report/?refresh=true'
        : '/api/summary-general-report/';
      const response = await axios.get(url);
      setSummaryData(response.data);

      if (forceRefresh) {
        toast({
          title: 'Cache refreshed',
          description: 'Summary statistics have been recalculated.',
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      console.error('Failed to fetch summary data:', error);
      toast({
        title: 'Error loading summary',
        description: 'Could not load summary statistics. You may need superuser access.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoadingSummary(false);
    }
  }, [toast]);

  // Fetch download requests
  const fetchDownloads = useCallback(async () => {
    setLoadingDownloads(true);
    try {
      // apiClient already has baseURL /api/v1/, so just use relative path
      const response = await apiClient.get('downloads/');
      const data = response.data?.data || [];
      setDownloads(data);
    } catch (error) {
      console.error('Failed to fetch downloads:', error);
      // Don't show error toast - user might not be logged in
    } finally {
      setLoadingDownloads(false);
    }
  }, []);

  // Fetch taxon groups
  const fetchTaxonGroups = useCallback(async () => {
    try {
      // apiClient already has baseURL /api/v1/, so just use relative path
      const response = await apiClient.get('taxon-groups/');
      const data = response.data?.data || [];
      setTaxonGroups(data);
    } catch (error) {
      console.error('Failed to fetch taxon groups:', error);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchSummaryData();
    fetchDownloads();
    fetchTaxonGroups();
  }, [fetchSummaryData, fetchDownloads, fetchTaxonGroups]);

  // Poll for task status
  useEffect(() => {
    if (!pollingTaskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await apiClient.get(`downloads/${pollingTaskId}/status/`);
        const data = response.data?.data;

        if (data?.ready) {
          setIsGenerating(false);
          setGenerationProgress(100);
          setPollingTaskId(null);
          clearInterval(pollInterval);

          if (data.status === 'SUCCESS') {
            toast({
              title: 'Report ready',
              description: 'Your report is ready for download.',
              status: 'success',
              duration: 5000,
            });
            // Refresh downloads list
            fetchDownloads();
          } else {
            toast({
              title: 'Report generation failed',
              description: data.error || 'An error occurred while generating the report.',
              status: 'error',
              duration: 5000,
            });
          }
        } else {
          // Update progress (estimate based on time)
          setGenerationProgress((prev) => Math.min(prev + 10, 90));
        }
      } catch (error) {
        console.error('Failed to poll task status:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [pollingTaskId, toast, fetchDownloads]);

  // Generate CSV report
  const generateCsvReport = async () => {
    setIsGenerating(true);
    setGenerationProgress(0);

    try {
      const filters: Record<string, unknown> = {};
      if (selectedTaxonGroup) {
        filters.taxon_group = selectedTaxonGroup;
      }

      const response = await apiClient.post('downloads/csv/', { filters });
      const data = response.data?.data;

      if (data?.task_id) {
        setPollingTaskId(data.task_id);
        toast({
          title: 'Report generation started',
          description: 'Your CSV report is being generated. This may take a few minutes.',
          status: 'info',
          duration: 5000,
        });
      }
    } catch (error: any) {
      setIsGenerating(false);
      toast({
        title: 'Generation failed',
        description: error.response?.data?.errors?.detail || 'Failed to start report generation.',
        status: 'error',
        duration: 5000,
      });
    }
  };

  // Generate checklist report
  const generateChecklistReport = async () => {
    if (!selectedTaxonGroup) {
      toast({
        title: 'Taxon group required',
        description: 'Please select a taxon group to generate a checklist.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);

    try {
      const response = await apiClient.post('downloads/checklist/', {
        taxon_group_id: parseInt(selectedTaxonGroup),
      });
      const data = response.data?.data;

      if (data?.task_id) {
        setPollingTaskId(data.task_id);
        toast({
          title: 'Checklist generation started',
          description: 'Your checklist is being generated. This may take a few minutes.',
          status: 'info',
          duration: 5000,
        });
      }
    } catch (error: any) {
      setIsGenerating(false);
      const errorDetail = error.response?.data?.errors?.detail
        || error.response?.data?.detail
        || error.message
        || 'Failed to start checklist generation.';
      console.error('Checklist generation error:', error.response?.data || error);
      toast({
        title: 'Generation failed',
        description: errorDetail,
        status: 'error',
        duration: 5000,
      });
    }
  };

  // Handle generate click
  const handleGenerate = () => {
    if (reportType === 'csv') {
      generateCsvReport();
    } else if (reportType === 'checklist') {
      generateChecklistReport();
    }
  };

  // Get status badge color
  const getStatusColor = (status: string, approved?: boolean, rejected?: boolean) => {
    if (rejected) return 'red';
    if (approved) return 'green';
    if (status === 'SUCCESS') return 'green';
    if (status === 'PENDING' || status === 'STARTED') return 'blue';
    if (status === 'FAILURE') return 'red';
    return 'gray';
  };

  // Get status label
  const getStatusLabel = (download: DownloadRequest) => {
    if (download.rejected) return 'Rejected';
    if (download.approved && download.download_url) return 'Ready';
    if (download.processing) return 'Processing';
    if (download.status === 'SUCCESS') return 'Ready';
    if (download.status === 'PENDING') return 'Pending';
    if (download.status === 'STARTED') return 'Processing';
    if (download.status === 'FAILURE') return 'Failed';
    return download.status || 'Unknown';
  };

  // Format number with commas
  const formatNumber = (num: number | undefined): string => {
    if (num === undefined) return '—';
    return num.toLocaleString();
  };

  return (
    <Box h="100%" overflowY="auto">
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Summary Reports</Heading>
              <Text opacity={0.9}>
                View system statistics and generate biodiversity reports
              </Text>
            </VStack>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        {/* System Statistics */}
        <Card bg={cardBg} mb={8}>
          <CardHeader>
            <HStack justify="space-between">
              <HStack spacing={3}>
                <Heading size="md">System Statistics</Heading>
                {summaryData?._cached && (
                  <Badge colorScheme="blue" variant="subtle">
                    Cached
                  </Badge>
                )}
              </HStack>
              <Button
                size="sm"
                variant="ghost"
                leftIcon={<RepeatIcon />}
                onClick={() => fetchSummaryData(true)}
                isLoading={loadingSummary}
              >
                Refresh
              </Button>
            </HStack>
          </CardHeader>
          <CardBody>
            {loadingSummary ? (
              <SimpleGrid columns={{ base: 2, md: 3, lg: 6 }} spacing={4}>
                {[...Array(6)].map((_, i) => (
                  <Skeleton key={i} height="80px" />
                ))}
              </SimpleGrid>
            ) : summaryData ? (
              <SimpleGrid columns={{ base: 2, md: 3, lg: 6 }} spacing={4}>
                <Stat>
                  <StatLabel>Total Sites</StatLabel>
                  <StatNumber color="blue.500">{formatNumber(summaryData.total_sites)}</StatNumber>
                  <StatHelpText>
                    {summaryData.total_duplicated_sites > 0 && (
                      <Text as="span" color="orange.500">
                        {summaryData.total_duplicated_sites} duplicates
                      </Text>
                    )}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>Total Records</StatLabel>
                  <StatNumber color="green.500">{formatNumber(summaryData.total_records)}</StatNumber>
                  <StatHelpText>
                    {summaryData.total_duplicate_records > 0 && (
                      <Text as="span" color="orange.500">
                        {summaryData.total_duplicate_records} duplicates
                      </Text>
                    )}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>Total Species</StatLabel>
                  <StatNumber color="purple.500">{formatNumber(summaryData.total_species)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>Modules</StatLabel>
                  <StatNumber>{formatNumber(summaryData.total_modules)}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>Source Collections</StatLabel>
                  <StatNumber>
                    {Object.keys(summaryData.total_records_per_source_collection || {}).length}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>Data Quality</StatLabel>
                  <StatNumber color={summaryData.total_duplicate_records > 100 ? 'orange.500' : 'green.500'}>
                    {summaryData.total_duplicate_records > 100 ? 'Review' : 'Good'}
                  </StatNumber>
                </Stat>
              </SimpleGrid>
            ) : (
              <Alert status="warning">
                <AlertIcon />
                Could not load summary statistics. You may need to be logged in as a superuser.
              </Alert>
            )}
          </CardBody>
        </Card>

        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={8}>
          {/* Report Generation */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Generate Report</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={6} align="stretch">
                <FormControl>
                  <FormLabel>Report Type</FormLabel>
                  <Select
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value)}
                  >
                    <option value="csv">CSV Data Export</option>
                    <option value="checklist">Species Checklist (PDF)</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Taxon Group {reportType === 'checklist' && <Badge>Required</Badge>}</FormLabel>
                  <Select
                    value={selectedTaxonGroup}
                    onChange={(e) => setSelectedTaxonGroup(e.target.value)}
                    placeholder="All groups"
                  >
                    {taxonGroups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name}
                      </option>
                    ))}
                  </Select>
                </FormControl>

                <Divider />

                {isGenerating && (
                  <Box>
                    <Text fontSize="sm" mb={2}>
                      Generating report... {generationProgress}%
                    </Text>
                    <Progress
                      value={generationProgress}
                      colorScheme="brand"
                      borderRadius="full"
                      isIndeterminate={generationProgress < 10}
                    />
                  </Box>
                )}

                <Button
                  colorScheme="brand"
                  size="lg"
                  leftIcon={<RepeatIcon />}
                  onClick={handleGenerate}
                  isLoading={isGenerating}
                  loadingText="Generating..."
                >
                  Generate Report
                </Button>

                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  <Text fontSize="sm">
                    Reports are generated asynchronously. Large datasets may take several minutes.
                  </Text>
                </Alert>
              </VStack>
            </CardBody>
          </Card>

          {/* Quick Actions */}
          <VStack spacing={6} align="stretch">
            <Card bg={cardBg}>
              <CardHeader>
                <Heading size="md">Quick Reports</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={3} align="stretch">
                  <Button
                    variant="outline"
                    justifyContent="start"
                    leftIcon={<ExternalLinkIcon />}
                    as="a"
                    href="/summary-report/"
                    target="_blank"
                  >
                    Full System Summary (Admin)
                  </Button>
                  <Button
                    variant="outline"
                    justifyContent="start"
                    leftIcon={<DownloadIcon />}
                    as="a"
                    href="/download-taxa-list/"
                  >
                    Download Complete Taxa List
                  </Button>
                  <Button
                    variant="outline"
                    justifyContent="start"
                    leftIcon={<ViewIcon />}
                    as="a"
                    href="/download-request/"
                    target="_blank"
                  >
                    Manage Download Requests (Admin)
                  </Button>
                </VStack>
              </CardBody>
            </Card>

            {/* Module Statistics */}
            {summaryData && Object.keys(summaryData.records_per_modules || {}).length > 0 && (
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">Records by Module</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={2} align="stretch">
                    {Object.entries(summaryData.records_per_modules).map(([module, sources]) => {
                      const total = Object.values(sources).reduce((a, b) => a + b, 0);
                      return (
                        <HStack key={module} justify="space-between">
                          <Text fontSize="sm" fontWeight="medium">{module}</Text>
                          <Badge colorScheme="blue">{formatNumber(total)}</Badge>
                        </HStack>
                      );
                    })}
                  </VStack>
                </CardBody>
              </Card>
            )}
          </VStack>
        </SimpleGrid>

        {/* Download Requests */}
        <Card bg={cardBg} mt={8}>
          <CardHeader>
            <HStack justify="space-between">
              <Heading size="md">Your Download Requests</Heading>
              <Button size="sm" variant="ghost" onClick={fetchDownloads} leftIcon={<RepeatIcon />}>
                Refresh
              </Button>
            </HStack>
          </CardHeader>
          <CardBody>
            {loadingDownloads ? (
              <Center py={8}>
                <Spinner size="lg" />
              </Center>
            ) : downloads.length === 0 ? (
              <VStack spacing={3} py={4}>
                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  <Text>No download requests found. Generate a report above to get started.</Text>
                </Alert>
                <Text fontSize="sm" color="gray.500">
                  Note: You must be logged in to see your download requests.
                  If you just generated a report, click Refresh to update the list.
                </Text>
              </VStack>
            ) : (
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Date</Th>
                    <Th>Type</Th>
                    <Th>Status</Th>
                    <Th>Progress</Th>
                    <Th>Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {downloads.map((download) => (
                    <Tr key={download.id || download.task_id}>
                      <Td>
                        {download.request_date
                          ? new Date(download.request_date).toLocaleDateString()
                          : '—'}
                      </Td>
                      <Td>
                        <Badge colorScheme="purple">
                          {download.resource_type || download.request_type || 'Download'}
                        </Badge>
                      </Td>
                      <Td>
                        <Badge colorScheme={getStatusColor(download.status, download.approved, download.rejected)}>
                          {getStatusLabel(download)}
                        </Badge>
                      </Td>
                      <Td>
                        {download.processing && (
                          <Progress
                            value={download.progress || 0}
                            size="sm"
                            colorScheme="blue"
                            width="100px"
                            borderRadius="full"
                          />
                        )}
                        {!download.processing && download.progress > 0 && `${download.progress}%`}
                      </Td>
                      <Td>
                        <HStack spacing={2}>
                          {download.download_url && (
                            <Button
                              size="sm"
                              leftIcon={<DownloadIcon />}
                              colorScheme="brand"
                              variant="ghost"
                              as="a"
                              href={download.download_url}
                              download
                            >
                              Download
                            </Button>
                          )}
                          {!download.download_url && download.status === 'PENDING' && (
                            <Text fontSize="sm" color="gray.500">Waiting...</Text>
                          )}
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </CardBody>
        </Card>
      </Container>
    </Box>
  );
};

export default SummaryReportPage;
