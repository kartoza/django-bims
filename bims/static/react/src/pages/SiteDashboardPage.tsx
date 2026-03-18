/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Site Dashboard Page - Full page dashboard for a location site
 * Displays biodiversity data, charts, and analytics for a specific site.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  Heading,
  Text,
  Grid,
  GridItem,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Card,
  CardHeader,
  CardBody,
  Skeleton,
  Button,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  useColorModeValue,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Icon,
} from '@chakra-ui/react';
import { ChevronRightIcon } from '@chakra-ui/icons';
import { useParams, useSearchParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import { apiClient } from '../api/client';
import { getTaxonGroupIcon } from '../components/icons';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement);

interface SiteDashboardData {
  id: number;
  site_detail_info: {
    site_code: string;
    site_description: string;
    site_coordinates: string;
    ecosystem_type: string;
  };
  location_context: Record<string, string>;
  biodiversity_data: Record<string, {
    module: number;
    icon: string;
    occurrences: number;
    number_of_taxa: number;
    origin: Array<{ name: string; count: number; colour?: string }>;
    endemism: Array<{ name: string; count: number; colour?: string }>;
    cons_status: Array<{ name: string; count: number; colour?: string }>;
  }>;
  climate_data?: Record<string, {
    title: string;
    keys: string[];
    values: number[];
  }>;
  sass_exist?: boolean;
  water_temperature_exist?: boolean;
  physico_chemical_exist?: boolean;
}

// Chart colors matching the original BIMS
const CHART_COLORS = [
  '#8D2641', '#D7CD47', '#18A090', '#A2CE89', '#4E6440', '#525351',
  '#641f30', '#E6E188', '#9D9739', '#618295', '#2C495A', '#39B2A3',
];

const SiteDashboardPage: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const moduleFilter = searchParams.get('module');

  const [siteData, setSiteData] = useState<SiteDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    const fetchSiteData = async () => {
      if (!siteId) return;
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<SiteDashboardData>(
          `/location-site-detail/?siteId=${siteId}`,
          { baseURL: '/api' }
        );
        setSiteData(response.data);
      } catch (err) {
        console.error('Failed to load site dashboard:', err);
        setError('Failed to load site data');
      } finally {
        setIsLoading(false);
      }
    };
    fetchSiteData();
  }, [siteId]);

  if (isLoading) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
        <Container maxW="7xl">
          <VStack spacing={6} align="stretch">
            <Skeleton height="40px" width="300px" />
            <Grid templateColumns="repeat(4, 1fr)" gap={4}>
              {[1, 2, 3, 4].map(i => (
                <GridItem key={i}>
                  <Skeleton height="100px" />
                </GridItem>
              ))}
            </Grid>
            <Skeleton height="400px" />
          </VStack>
        </Container>
      </Box>
    );
  }

  if (error || !siteData) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
        <Container maxW="7xl">
          <VStack spacing={4}>
            <Text color="red.500" fontSize="lg">{error || 'Site not found'}</Text>
            <Button onClick={() => navigate('/map')}>Back to Map</Button>
          </VStack>
        </Container>
      </Box>
    );
  }

  const { site_detail_info, location_context, biodiversity_data, climate_data } = siteData;

  // Calculate totals
  const totalOccurrences = Object.values(biodiversity_data || {}).reduce((sum, m) => sum + (m.occurrences || 0), 0);
  const totalTaxa = Object.values(biodiversity_data || {}).reduce((sum, m) => sum + (m.number_of_taxa || 0), 0);
  const moduleCount = Object.keys(biodiversity_data || {}).length;

  // Prepare pie chart data for a category
  const preparePieData = (data: Array<{ name: string; count: number; colour?: string }>) => ({
    labels: data.map(d => d.name),
    datasets: [{
      data: data.map(d => d.count),
      backgroundColor: data.map((d, i) => d.colour || CHART_COLORS[i % CHART_COLORS.length]),
      borderWidth: 1,
    }],
  });

  return (
    <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
      <Container maxW="7xl">
        <VStack spacing={6} align="stretch">
          {/* Breadcrumb */}
          <Breadcrumb separator={<ChevronRightIcon color="gray.500" />}>
            <BreadcrumbItem>
              <BreadcrumbLink as={RouterLink} to="/map">Map</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem isCurrentPage>
              <BreadcrumbLink>{site_detail_info?.site_code || `Site ${siteId}`}</BreadcrumbLink>
            </BreadcrumbItem>
          </Breadcrumb>

          {/* Header */}
          <HStack justify="space-between" align="flex-start">
            <VStack align="start" spacing={1}>
              <Heading size="lg">{site_detail_info?.site_code || 'Site Dashboard'}</Heading>
              <Text color="gray.600">{site_detail_info?.site_description}</Text>
              {site_detail_info?.ecosystem_type && (
                <Badge colorScheme="blue">{site_detail_info.ecosystem_type}</Badge>
              )}
            </VStack>
            <Button
              variant="outline"
              onClick={() => navigate(`/map/site/${siteId}`)}
            >
              View on Map
            </Button>
          </HStack>

          {/* Summary Stats */}
          <StatGroup>
            <Card bg={cardBg} flex={1}>
              <CardBody>
                <Stat>
                  <StatLabel>Total Occurrences</StatLabel>
                  <StatNumber>{totalOccurrences.toLocaleString()}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg} flex={1}>
              <CardBody>
                <Stat>
                  <StatLabel>Total Taxa</StatLabel>
                  <StatNumber>{totalTaxa.toLocaleString()}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg} flex={1}>
              <CardBody>
                <Stat>
                  <StatLabel>Modules</StatLabel>
                  <StatNumber>{moduleCount}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg} flex={1}>
              <CardBody>
                <Stat>
                  <StatLabel>Coordinates</StatLabel>
                  <StatNumber fontSize="sm">{site_detail_info?.site_coordinates}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
          </StatGroup>

          {/* Location Context */}
          {location_context && Object.keys(location_context).length > 0 && (
            <Card bg={cardBg}>
              <CardHeader>
                <Heading size="md">Location Context</Heading>
              </CardHeader>
              <CardBody>
                <Table size="sm" variant="simple">
                  <Tbody>
                    {Object.entries(location_context).map(([key, value]) => (
                      <Tr key={key}>
                        <Td fontWeight="medium" w="30%">{key}</Td>
                        <Td>{value}</Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          )}

          {/* Biodiversity Data */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Biodiversity Data</Heading>
            </CardHeader>
            <CardBody>
              {biodiversity_data && Object.keys(biodiversity_data).length > 0 ? (
                <Tabs variant="enclosed" colorScheme="blue">
                  <TabList>
                    {Object.keys(biodiversity_data).map(moduleName => {
                      const ModuleIcon = getTaxonGroupIcon(moduleName);
                      return (
                        <Tab key={moduleName}>
                          <HStack spacing={2}>
                            <ModuleIcon boxSize={5} />
                            <Text>{moduleName}</Text>
                          </HStack>
                        </Tab>
                      );
                    })}
                  </TabList>
                  <TabPanels>
                    {Object.entries(biodiversity_data).map(([moduleName, moduleData]) => (
                      <TabPanel key={moduleName}>
                        <VStack spacing={6} align="stretch">
                          {/* Module Stats */}
                          <StatGroup>
                            <Stat>
                              <StatLabel>Occurrences</StatLabel>
                              <StatNumber>{moduleData.occurrences}</StatNumber>
                            </Stat>
                            <Stat>
                              <StatLabel>Number of Taxa</StatLabel>
                              <StatNumber>{moduleData.number_of_taxa}</StatNumber>
                            </Stat>
                          </StatGroup>

                          {/* Charts Grid */}
                          <Grid templateColumns="repeat(3, 1fr)" gap={6}>
                            {/* Origin Chart */}
                            {moduleData.origin && moduleData.origin.length > 0 && (
                              <GridItem>
                                <VStack>
                                  <Heading size="sm">Origin</Heading>
                                  <Box h="200px" w="200px">
                                    <Pie
                                      data={preparePieData(moduleData.origin)}
                                      options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: { legend: { position: 'bottom' } },
                                      }}
                                    />
                                  </Box>
                                </VStack>
                              </GridItem>
                            )}

                            {/* Endemism Chart */}
                            {moduleData.endemism && moduleData.endemism.length > 0 && (
                              <GridItem>
                                <VStack>
                                  <Heading size="sm">Endemism</Heading>
                                  <Box h="200px" w="200px">
                                    <Pie
                                      data={preparePieData(moduleData.endemism)}
                                      options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: { legend: { position: 'bottom' } },
                                      }}
                                    />
                                  </Box>
                                </VStack>
                              </GridItem>
                            )}

                            {/* Conservation Status Chart */}
                            {moduleData.cons_status && moduleData.cons_status.length > 0 && (
                              <GridItem>
                                <VStack>
                                  <Heading size="sm">Conservation Status</Heading>
                                  <Box h="200px" w="200px">
                                    <Pie
                                      data={preparePieData(moduleData.cons_status)}
                                      options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: { legend: { position: 'bottom' } },
                                      }}
                                    />
                                  </Box>
                                </VStack>
                              </GridItem>
                            )}
                          </Grid>
                        </VStack>
                      </TabPanel>
                    ))}
                  </TabPanels>
                </Tabs>
              ) : (
                <Text color="gray.500" textAlign="center" py={8}>
                  No biodiversity data available for this site
                </Text>
              )}
            </CardBody>
          </Card>

          {/* Climate Data */}
          {climate_data && Object.keys(climate_data).length > 0 && (
            <Card bg={cardBg}>
              <CardHeader>
                <Heading size="md">Climate Data</Heading>
              </CardHeader>
              <CardBody>
                <Grid templateColumns="repeat(2, 1fr)" gap={6}>
                  {Object.entries(climate_data).map(([key, data]) => (
                    <GridItem key={key}>
                      <VStack align="start">
                        <Heading size="sm">{data.title}</Heading>
                        {data.keys && data.values && (
                          <Box w="100%" h="200px">
                            <Bar
                              data={{
                                labels: data.keys,
                                datasets: [{
                                  label: data.title,
                                  data: data.values,
                                  backgroundColor: CHART_COLORS[0],
                                }],
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                              }}
                            />
                          </Box>
                        )}
                      </VStack>
                    </GridItem>
                  ))}
                </Grid>
              </CardBody>
            </Card>
          )}

          {/* Additional Dashboards */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Additional Data</Heading>
            </CardHeader>
            <CardBody>
              <HStack spacing={4} wrap="wrap">
                <Button
                  isDisabled={!siteData.sass_exist}
                  onClick={() => navigate(`/dashboard/sass/${siteId}`)}
                >
                  SASS Dashboard
                </Button>
                <Button
                  isDisabled={!siteData.water_temperature_exist}
                  onClick={() => navigate(`/dashboard/water-temperature/${siteId}`)}
                >
                  Water Temperature
                </Button>
                <Button
                  isDisabled={!siteData.physico_chemical_exist}
                  onClick={() => navigate(`/dashboard/physico-chemical/${siteId}`)}
                >
                  Physico-chemical
                </Button>
              </HStack>
            </CardBody>
          </Card>
        </VStack>
      </Container>
    </Box>
  );
};

export default SiteDashboardPage;
