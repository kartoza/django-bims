/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Analytics Dashboard - Multi-site summary dashboard matching original BIMS.
 * Shows biodiversity breakdown, charts, species lists, and download options.
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
  SimpleGrid,
  Grid,
  GridItem,
  Stat,
  StatLabel,
  StatNumber,
  Spinner,
  Center,
  useColorModeValue,
  Badge,
  Flex,
  Spacer,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Button,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  IconButton,
  Tooltip,
  Collapse,
} from '@chakra-ui/react';
import { ChevronRightIcon, DownloadIcon, ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import { useSearchParams, Link as RouterLink, useNavigate } from 'react-router-dom';
import { Chart as ChartJS, ArcElement, Tooltip as ChartTooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';
import { useSearchStore } from '../stores/searchStore';
import { apiClient } from '../api/client';
import { getTaxonGroupIcon } from '../components/icons';

// Register Chart.js components
ChartJS.register(ArcElement, ChartTooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title);

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

const AnalyticsDashboardPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const filters = useSearchStore((state) => state.filters);

  const [summaryData, setSummaryData] = useState<FilterSummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllSpecies, setShowAllSpecies] = useState(false);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const headerBg = useColorModeValue('brand.500', 'brand.600');

  // Build API params from filters
  const buildParams = useCallback(() => {
    const params: Record<string, string> = {};
    const moduleFilter = searchParams.get('module');

    if (moduleFilter) {
      params.taxon_group = moduleFilter;
    } else if (filters.taxonGroups && filters.taxonGroups.length > 0) {
      params.taxon_group = String(filters.taxonGroups[0]);
    }
    if (filters.yearFrom) params.year_from = String(filters.yearFrom);
    if (filters.yearTo) params.year_to = String(filters.yearTo);
    if (filters.iucnCategories && filters.iucnCategories.length > 0) {
      params.iucn_category = filters.iucnCategories.join(',');
    }
    if (filters.endemism && filters.endemism.length > 0) {
      params.endemism = filters.endemism.join(',');
    }
    if (filters.collectors && filters.collectors.length > 0) {
      params.collector = filters.collectors.join(',');
    }
    if (filters.boundaryId) params.boundary = String(filters.boundaryId);
    if (filters.bbox) params.bbox = filters.bbox;

    return params;
  }, [filters, searchParams]);

  // Fetch summary data
  useEffect(() => {
    const fetchData = async () => {
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
        console.error('Failed to load dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [buildParams]);

  // Prepare pie chart data
  const preparePieData = (data: Array<{ name: string; count: number }>, colorMap?: Record<string, string>) => ({
    labels: data.map(d => d.name),
    datasets: [{
      data: data.map(d => d.count),
      backgroundColor: data.map((d, i) => colorMap?.[d.name] || CHART_COLORS[i % CHART_COLORS.length]),
      borderWidth: 1,
    }],
  });

  // Prepare stacked bar chart data for all modules
  const prepareStackedBarData = (field: 'origin' | 'endemism' | 'cons_status') => {
    if (!summaryData?.biodiversity_data) return null;

    const modules = Object.keys(summaryData.biodiversity_data);
    const allLabels = new Set<string>();
    modules.forEach(mod => {
      summaryData.biodiversity_data[mod][field].forEach(item => allLabels.add(item.name));
    });
    const labels = Array.from(allLabels);

    const datasets = modules.map((mod, idx) => {
      const moduleData = summaryData.biodiversity_data[mod][field];
      return {
        label: mod,
        data: labels.map(label => {
          const item = moduleData.find(d => d.name === label);
          return item ? item.count : 0;
        }),
        backgroundColor: CHART_COLORS[idx % CHART_COLORS.length],
      };
    });

    return { labels, datasets };
  };

  if (isLoading) {
    return (
      <Center h="calc(100vh - 140px)">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (error || !summaryData) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
        <Container maxW="7xl">
          <VStack spacing={4}>
            <Text color="red.500" fontSize="lg">{error || 'No data available'}</Text>
            <Button onClick={() => navigate('/map')}>Back to Map</Button>
          </VStack>
        </Container>
      </Box>
    );
  }

  const { total_sites, total_occurrences, total_taxa, biodiversity_data, species_list, date_range } = summaryData;

  // Aggregate data across all modules for overview charts
  const aggregatedOrigin: Record<string, number> = {};
  const aggregatedEndemism: Record<string, number> = {};
  const aggregatedConsStatus: Record<string, number> = {};

  Object.values(biodiversity_data).forEach(mod => {
    mod.origin.forEach(o => { aggregatedOrigin[o.name] = (aggregatedOrigin[o.name] || 0) + o.count; });
    mod.endemism.forEach(e => { aggregatedEndemism[e.name] = (aggregatedEndemism[e.name] || 0) + e.count; });
    mod.cons_status.forEach(c => { aggregatedConsStatus[c.name] = (aggregatedConsStatus[c.name] || 0) + c.count; });
  });

  const originData = Object.entries(aggregatedOrigin).map(([name, count]) => ({ name, count }));
  const endemismData = Object.entries(aggregatedEndemism).map(([name, count]) => ({ name, count }));
  const consStatusData = Object.entries(aggregatedConsStatus).map(([name, count]) => ({ name, count }));

  return (
    <Box bg={bgColor} minH="calc(100vh - 140px)">
      {/* Header */}
      <Box bg={headerBg} color="white" py={6}>
        <Container maxW="7xl">
          <Breadcrumb separator={<ChevronRightIcon color="whiteAlpha.700" />} mb={2}>
            <BreadcrumbItem>
              <BreadcrumbLink as={RouterLink} to="/map" color="whiteAlpha.800">Map</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem isCurrentPage>
              <BreadcrumbLink color="white">Summary Dashboard</BreadcrumbLink>
            </BreadcrumbItem>
          </Breadcrumb>
          <Heading size="lg">Summary Dashboard</Heading>
          <Text opacity={0.9} mt={1}>
            Multi-site biodiversity overview
          </Text>
        </Container>
      </Box>

      <Container maxW="7xl" py={6}>
        <Grid templateColumns={{ base: '1fr', lg: '5fr 7fr' }} gap={6}>
          {/* Left Column */}
          <GridItem>
            {/* Overview Stats */}
            <Card bg={cardBg} mb={6}>
              <CardHeader pb={2}>
                <Heading size="md">Overview</Heading>
              </CardHeader>
              <CardBody>
                <Table size="sm" variant="simple">
                  <Tbody>
                    <Tr>
                      <Td fontWeight="medium">Sites</Td>
                      <Td isNumeric>{total_sites.toLocaleString()}</Td>
                    </Tr>
                    <Tr>
                      <Td fontWeight="medium">Occurrences</Td>
                      <Td isNumeric>{total_occurrences.toLocaleString()}</Td>
                    </Tr>
                    <Tr>
                      <Td fontWeight="medium">Taxa</Td>
                      <Td isNumeric>{total_taxa.toLocaleString()}</Td>
                    </Tr>
                    {date_range.earliest && (
                      <Tr>
                        <Td fontWeight="medium">Date Range</Td>
                        <Td isNumeric fontSize="xs">
                          {new Date(date_range.earliest).getFullYear()} - {date_range.latest ? new Date(date_range.latest).getFullYear() : 'Present'}
                        </Td>
                      </Tr>
                    )}
                    <Tr>
                      <Td fontWeight="medium">Modules</Td>
                      <Td isNumeric>{Object.keys(biodiversity_data).length}</Td>
                    </Tr>
                  </Tbody>
                </Table>
              </CardBody>
            </Card>

            {/* Biodiversity Breakdown by Module */}
            <Card bg={cardBg} mb={6}>
              <CardHeader pb={2}>
                <HStack justify="space-between">
                  <Heading size="md">Biodiversity by Module</Heading>
                  <Tooltip label="Download CSV">
                    <IconButton
                      aria-label="Download"
                      icon={<DownloadIcon />}
                      size="sm"
                      variant="ghost"
                      onClick={() => navigate('/downloads')}
                    />
                  </Tooltip>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  {Object.entries(biodiversity_data).map(([moduleName, moduleData]) => {
                    const ModuleIcon = getTaxonGroupIcon(moduleName);
                    return (
                    <Box key={moduleName} p={3} bg={bgColor} borderRadius="md">
                      <HStack justify="space-between" mb={2}>
                        <HStack spacing={2}>
                          <ModuleIcon boxSize={5} color="brand.600" />
                          <Text fontWeight="bold">{moduleName}</Text>
                        </HStack>
                        <Badge colorScheme="blue">{moduleData.occurrences}</Badge>
                      </HStack>
                      <SimpleGrid columns={3} spacing={2} fontSize="xs">
                        <Stat size="sm">
                          <StatLabel>Sites</StatLabel>
                          <StatNumber fontSize="sm">{moduleData.number_of_sites}</StatNumber>
                        </Stat>
                        <Stat size="sm">
                          <StatLabel>Taxa</StatLabel>
                          <StatNumber fontSize="sm">{moduleData.number_of_taxa}</StatNumber>
                        </Stat>
                        <Stat size="sm">
                          <StatLabel>Records</StatLabel>
                          <StatNumber fontSize="sm">{moduleData.occurrences}</StatNumber>
                        </Stat>
                      </SimpleGrid>
                      <Button
                        size="xs"
                        variant="outline"
                        colorScheme="blue"
                        mt={2}
                        w="100%"
                        onClick={() => navigate(`/analytics?module=${moduleData.module_id}`)}
                      >
                        View {moduleName} Dashboard
                      </Button>
                    </Box>
                    );
                  })}
                </VStack>
              </CardBody>
            </Card>
          </GridItem>

          {/* Right Column */}
          <GridItem>
            {/* Occurrence Pie Charts */}
            <Card bg={cardBg} mb={6}>
              <CardHeader pb={2}>
                <Heading size="md">Occurrence Charts</Heading>
              </CardHeader>
              <CardBody>
                <SimpleGrid columns={{ base: 2, md: 3 }} spacing={6}>
                  {/* Origin */}
                  <VStack>
                    <Text fontWeight="medium" fontSize="sm">Origin</Text>
                    <Box h="150px" w="150px">
                      <Pie
                        data={preparePieData(originData)}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } },
                        }}
                      />
                    </Box>
                  </VStack>

                  {/* Endemism */}
                  <VStack>
                    <Text fontWeight="medium" fontSize="sm">Endemism</Text>
                    <Box h="150px" w="150px">
                      <Pie
                        data={preparePieData(endemismData)}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } },
                        }}
                      />
                    </Box>
                  </VStack>

                  {/* Conservation Status */}
                  <VStack>
                    <Text fontWeight="medium" fontSize="sm">Conservation Status</Text>
                    <Box h="150px" w="150px">
                      <Pie
                        data={preparePieData(consStatusData, IUCN_COLORS)}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } },
                        }}
                      />
                    </Box>
                  </VStack>
                </SimpleGrid>
              </CardBody>
            </Card>

            {/* Stacked Bar Charts */}
            <Tabs variant="enclosed" colorScheme="blue" mb={6}>
              <TabList>
                <Tab>Conservation Status</Tab>
                <Tab>Origin</Tab>
                <Tab>Endemism</Tab>
              </TabList>
              <TabPanels>
                <TabPanel p={0} pt={4}>
                  <Card bg={cardBg}>
                    <CardBody>
                      {prepareStackedBarData('cons_status') && (
                        <Box h="250px">
                          <Bar
                            data={prepareStackedBarData('cons_status')!}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              scales: {
                                x: { stacked: true },
                                y: { stacked: true },
                              },
                              plugins: {
                                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } },
                                title: { display: true, text: 'Conservation Status by Module' },
                              },
                            }}
                          />
                        </Box>
                      )}
                    </CardBody>
                  </Card>
                </TabPanel>
                <TabPanel p={0} pt={4}>
                  <Card bg={cardBg}>
                    <CardBody>
                      {prepareStackedBarData('origin') && (
                        <Box h="250px">
                          <Bar
                            data={prepareStackedBarData('origin')!}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              scales: {
                                x: { stacked: true },
                                y: { stacked: true },
                              },
                              plugins: {
                                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } },
                                title: { display: true, text: 'Origin by Module' },
                              },
                            }}
                          />
                        </Box>
                      )}
                    </CardBody>
                  </Card>
                </TabPanel>
                <TabPanel p={0} pt={4}>
                  <Card bg={cardBg}>
                    <CardBody>
                      {prepareStackedBarData('endemism') && (
                        <Box h="250px">
                          <Bar
                            data={prepareStackedBarData('endemism')!}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              scales: {
                                x: { stacked: true },
                                y: { stacked: true },
                              },
                              plugins: {
                                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } },
                                title: { display: true, text: 'Endemism by Module' },
                              },
                            }}
                          />
                        </Box>
                      )}
                    </CardBody>
                  </Card>
                </TabPanel>
              </TabPanels>
            </Tabs>

            {/* Species List */}
            <Card bg={cardBg}>
              <CardHeader pb={2}>
                <HStack justify="space-between">
                  <Heading size="md">Species List</Heading>
                  <HStack>
                    <Button
                      size="sm"
                      leftIcon={<DownloadIcon />}
                      variant="outline"
                      onClick={() => navigate('/downloads')}
                    >
                      Download CSV
                    </Button>
                    <IconButton
                      aria-label="Toggle list"
                      icon={showAllSpecies ? <ChevronUpIcon /> : <ChevronDownIcon />}
                      size="sm"
                      variant="ghost"
                      onClick={() => setShowAllSpecies(!showAllSpecies)}
                    />
                  </HStack>
                </HStack>
              </CardHeader>
              <CardBody>
                <Table size="sm" variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Species</Th>
                      <Th>Rank</Th>
                      <Th isNumeric>Occurrences</Th>
                      <Th isNumeric>Sites</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {(showAllSpecies ? species_list : species_list.slice(0, 10)).map((species) => (
                      <Tr
                        key={species.id}
                        cursor="pointer"
                        _hover={{ bg: bgColor }}
                        onClick={() => navigate(`/map/taxon/${species.id}`)}
                      >
                        <Td fontStyle="italic" fontWeight="medium">{species.name}</Td>
                        <Td><Badge size="sm">{species.rank}</Badge></Td>
                        <Td isNumeric>{species.occurrences}</Td>
                        <Td isNumeric>{species.sites}</Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                {species_list.length > 10 && !showAllSpecies && (
                  <Button
                    size="sm"
                    variant="link"
                    mt={2}
                    onClick={() => setShowAllSpecies(true)}
                  >
                    Show all {species_list.length} species
                  </Button>
                )}
              </CardBody>
            </Card>
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
};

export default AnalyticsDashboardPage;
