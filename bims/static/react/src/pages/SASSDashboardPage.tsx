/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * SASS Dashboard Page - South African Scoring System dashboard for a site
 * Displays SASS scores, taxa sensitivity, biotope ratings, and ecological conditions.
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
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatGroup,
  Select,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { ChevronRightIcon } from '@chakra-ui/icons';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
} from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title
);

// SASS ecological category colors
const ECOLOGICAL_COLORS: Record<string, string> = {
  'A': '#0000FF',  // Natural/Unmodified - Blue
  'B': '#00AA00',  // Largely Natural - Green
  'C': '#FFFF00',  // Moderately Modified - Yellow
  'D': '#FFA500',  // Largely Modified - Orange
  'E': '#FF0000',  // Seriously Modified - Red
  'F': '#800000',  // Critically Modified - Dark Red
};

// Sensitivity level colors
const SENSITIVITY_COLORS = {
  highly_tolerant: '#d9534f',
  tolerant: '#f0ad4e',
  sensitive: '#5bc0de',
  highly_sensitive: '#5cb85c',
};

// Chart colors
const CHART_COLORS = [
  '#8D2641', '#D7CD47', '#18A090', '#A2CE89', '#4E6440', '#525351',
  '#641f30', '#E6E188', '#9D9739', '#618295', '#2C495A', '#39B2A3',
];

interface SASSData {
  site_code: string;
  site_description: string;
  sass_version: number;
  latest_sass_score: number;
  latest_aspt: number;
  latest_taxa_count: number;
  latest_date: string;
  ecological_category: string;
  ecological_name: string;
  ecological_color: string;
  sass_scores: number[];
  aspt_list: number[];
  taxa_numbers: number[];
  date_labels: string[];
  sass_ids: number[];
  sensitivity_data: {
    highly_tolerant: number;
    tolerant: number;
    sensitive: number;
    highly_sensitive: number;
  };
  biotope_data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
    }>;
  };
  taxa_table: Array<{
    taxon_name: string;
    score: number;
    sensitivity: string;
    abundance: string;
    biotope: string;
  }>;
  ecoregion: string;
  geomorphological_zone: string;
  river_name: string;
}

const SASSDashboardPage: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const navigate = useNavigate();

  const [sassData, setSassData] = useState<SASSData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<string>('all');

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    const fetchSASSData = async () => {
      if (!siteId) return;
      setIsLoading(true);
      setError(null);

      try {
        // Fetch SASS dashboard data from the existing endpoint
        const response = await fetch(`/sass/dashboard/${siteId}/?format=json`);
        if (!response.ok) {
          if (response.status === 404) {
            setError('No SASS data available for this site');
          } else {
            throw new Error('Failed to fetch SASS data');
          }
          return;
        }

        const data = await response.json();
        setSassData(data);
      } catch (err) {
        console.error('Failed to load SASS dashboard:', err);
        setError('Failed to load SASS data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSASSData();
  }, [siteId, selectedYear]);

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

  if (error) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
        <Container maxW="7xl">
          <VStack spacing={4}>
            <Alert status="warning">
              <AlertIcon />
              {error}
            </Alert>
            <Button onClick={() => navigate(`/map/site/${siteId}`)}>Back to Site</Button>
          </VStack>
        </Container>
      </Box>
    );
  }

  if (!sassData) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
        <Container maxW="7xl">
          <VStack spacing={4}>
            <Text>No SASS data available</Text>
            <Button onClick={() => navigate(`/map/site/${siteId}`)}>Back to Site</Button>
          </VStack>
        </Container>
      </Box>
    );
  }

  // Prepare SASS score chart data
  const sassScoreChartData = {
    labels: sassData.date_labels || [],
    datasets: [
      {
        label: 'SASS Score',
        data: sassData.sass_scores || [],
        borderColor: '#8D2641',
        backgroundColor: 'rgba(141, 38, 65, 0.1)',
        fill: true,
        yAxisID: 'y',
      },
      {
        label: 'Number of Taxa',
        data: sassData.taxa_numbers || [],
        borderColor: '#18A090',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        yAxisID: 'y',
      },
      {
        label: 'ASPT',
        data: sassData.aspt_list || [],
        borderColor: '#D7CD47',
        backgroundColor: 'transparent',
        yAxisID: 'y1',
      },
    ],
  };

  const sassScoreChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'SASS Scores Over Time',
      },
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'SASS Score / Taxa Count',
        },
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'ASPT',
        },
        grid: {
          drawOnChartArea: false,
        },
        min: 0,
        max: 15,
      },
    },
  };

  // Prepare sensitivity pie chart data
  const sensitivityChartData = {
    labels: ['Highly Tolerant', 'Tolerant', 'Sensitive', 'Highly Sensitive'],
    datasets: [
      {
        data: sassData.sensitivity_data ? [
          sassData.sensitivity_data.highly_tolerant,
          sassData.sensitivity_data.tolerant,
          sassData.sensitivity_data.sensitive,
          sassData.sensitivity_data.highly_sensitive,
        ] : [0, 0, 0, 0],
        backgroundColor: [
          SENSITIVITY_COLORS.highly_tolerant,
          SENSITIVITY_COLORS.tolerant,
          SENSITIVITY_COLORS.sensitive,
          SENSITIVITY_COLORS.highly_sensitive,
        ],
      },
    ],
  };

  // Prepare biotope chart data
  const biotopeChartData = {
    labels: sassData.biotope_data?.labels || ['Stones', 'Vegetation', 'GSM'],
    datasets: (sassData.biotope_data?.datasets || []).map((ds, i) => ({
      label: ds.label,
      data: ds.data,
      backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
    })),
  };

  const biotopeChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Biotope Ratings',
      },
    },
    scales: {
      x: {
        stacked: true,
      },
      y: {
        stacked: true,
        min: 0,
        max: 5,
        title: {
          display: true,
          text: 'Rating',
        },
      },
    },
  };

  return (
    <Box bg={bgColor} minH="calc(100vh - 140px)" p={6} overflowY="auto">
      <Container maxW="7xl">
        <VStack spacing={6} align="stretch">
          {/* Breadcrumb */}
          <Breadcrumb separator={<ChevronRightIcon color="gray.500" />}>
            <BreadcrumbItem>
              <BreadcrumbLink as={RouterLink} to="/map">Map</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <BreadcrumbLink as={RouterLink} to={`/dashboard/site/${siteId}`}>
                {sassData.site_code || `Site ${siteId}`}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem isCurrentPage>
              <BreadcrumbLink>SASS Dashboard</BreadcrumbLink>
            </BreadcrumbItem>
          </Breadcrumb>

          {/* Header */}
          <HStack justify="space-between" align="flex-start">
            <VStack align="start" spacing={1}>
              <Heading size="lg">SASS Dashboard</Heading>
              <Text color="gray.600">{sassData.site_code} - {sassData.site_description}</Text>
              <HStack>
                <Badge colorScheme="blue">SASS Version {sassData.sass_version || 5}</Badge>
                {sassData.river_name && (
                  <Badge colorScheme="teal">{sassData.river_name}</Badge>
                )}
              </HStack>
            </VStack>
            <Button
              variant="outline"
              onClick={() => navigate(`/dashboard/site/${siteId}`)}
            >
              Back to Site Dashboard
            </Button>
          </HStack>

          {/* Summary Stats */}
          <StatGroup>
            <Card bg={cardBg} flex={1}>
              <CardBody>
                <Stat>
                  <StatLabel>Latest SASS Score</StatLabel>
                  <StatNumber color="brand.500">{sassData.latest_sass_score || '-'}</StatNumber>
                  <StatHelpText>{sassData.latest_date}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg} flex={1}>
              <CardBody>
                <Stat>
                  <StatLabel>Latest ASPT</StatLabel>
                  <StatNumber color="green.500">
                    {sassData.latest_aspt?.toFixed(2) || '-'}
                  </StatNumber>
                  <StatHelpText>Average Score Per Taxon</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg} flex={1}>
              <CardBody>
                <Stat>
                  <StatLabel>Number of Taxa</StatLabel>
                  <StatNumber color="purple.500">{sassData.latest_taxa_count || '-'}</StatNumber>
                  <StatHelpText>In latest assessment</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg} flex={1}>
              <CardBody>
                <Stat>
                  <StatLabel>Ecological Category</StatLabel>
                  <StatNumber>
                    <Badge
                      fontSize="xl"
                      px={3}
                      py={1}
                      bg={sassData.ecological_color || ECOLOGICAL_COLORS[sassData.ecological_category] || 'gray.500'}
                      color="white"
                    >
                      {sassData.ecological_category || '-'}
                    </Badge>
                  </StatNumber>
                  <StatHelpText>{sassData.ecological_name || 'Not assessed'}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </StatGroup>

          {/* Location Context */}
          {(sassData.ecoregion || sassData.geomorphological_zone) && (
            <Card bg={cardBg}>
              <CardBody>
                <HStack spacing={8}>
                  {sassData.ecoregion && (
                    <Box>
                      <Text fontSize="sm" color="gray.500">Ecoregion</Text>
                      <Text fontWeight="medium">{sassData.ecoregion}</Text>
                    </Box>
                  )}
                  {sassData.geomorphological_zone && (
                    <Box>
                      <Text fontSize="sm" color="gray.500">Geomorphological Zone</Text>
                      <Text fontWeight="medium">{sassData.geomorphological_zone}</Text>
                    </Box>
                  )}
                </HStack>
              </CardBody>
            </Card>
          )}

          {/* Charts */}
          <Tabs variant="enclosed" colorScheme="blue">
            <TabList>
              <Tab>SASS Trends</Tab>
              <Tab>Sensitivity Analysis</Tab>
              <Tab>Biotope Assessment</Tab>
              <Tab>Taxa List</Tab>
            </TabList>

            <TabPanels>
              {/* SASS Trends Tab */}
              <TabPanel p={0} pt={4}>
                <Card bg={cardBg}>
                  <CardBody>
                    <Box h="400px">
                      <Line data={sassScoreChartData} options={sassScoreChartOptions} />
                    </Box>
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Sensitivity Analysis Tab */}
              <TabPanel p={0} pt={4}>
                <Grid templateColumns="repeat(2, 1fr)" gap={6}>
                  <GridItem>
                    <Card bg={cardBg}>
                      <CardHeader>
                        <Heading size="md">Taxa Sensitivity Distribution</Heading>
                      </CardHeader>
                      <CardBody>
                        <Box h="300px" display="flex" justifyContent="center">
                          <Box w="300px" h="300px">
                            <Pie
                              data={sensitivityChartData}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                  legend: {
                                    position: 'bottom',
                                  },
                                },
                              }}
                            />
                          </Box>
                        </Box>
                      </CardBody>
                    </Card>
                  </GridItem>
                  <GridItem>
                    <Card bg={cardBg}>
                      <CardHeader>
                        <Heading size="md">Sensitivity Breakdown</Heading>
                      </CardHeader>
                      <CardBody>
                        <VStack align="stretch" spacing={4}>
                          <HStack justify="space-between">
                            <HStack>
                              <Box w={4} h={4} bg={SENSITIVITY_COLORS.highly_sensitive} borderRadius="sm" />
                              <Text>Highly Sensitive</Text>
                            </HStack>
                            <Text fontWeight="bold">{sassData.sensitivity_data?.highly_sensitive || 0}</Text>
                          </HStack>
                          <HStack justify="space-between">
                            <HStack>
                              <Box w={4} h={4} bg={SENSITIVITY_COLORS.sensitive} borderRadius="sm" />
                              <Text>Sensitive</Text>
                            </HStack>
                            <Text fontWeight="bold">{sassData.sensitivity_data?.sensitive || 0}</Text>
                          </HStack>
                          <HStack justify="space-between">
                            <HStack>
                              <Box w={4} h={4} bg={SENSITIVITY_COLORS.tolerant} borderRadius="sm" />
                              <Text>Tolerant</Text>
                            </HStack>
                            <Text fontWeight="bold">{sassData.sensitivity_data?.tolerant || 0}</Text>
                          </HStack>
                          <HStack justify="space-between">
                            <HStack>
                              <Box w={4} h={4} bg={SENSITIVITY_COLORS.highly_tolerant} borderRadius="sm" />
                              <Text>Highly Tolerant</Text>
                            </HStack>
                            <Text fontWeight="bold">{sassData.sensitivity_data?.highly_tolerant || 0}</Text>
                          </HStack>
                        </VStack>
                        <Text mt={6} fontSize="sm" color="gray.500">
                          A higher proportion of sensitive taxa indicates better water quality.
                          Tolerant taxa dominate in degraded conditions.
                        </Text>
                      </CardBody>
                    </Card>
                  </GridItem>
                </Grid>
              </TabPanel>

              {/* Biotope Assessment Tab */}
              <TabPanel p={0} pt={4}>
                <Card bg={cardBg}>
                  <CardHeader>
                    <Heading size="md">Biotope Ratings Over Time</Heading>
                  </CardHeader>
                  <CardBody>
                    <Box h="400px">
                      <Bar data={biotopeChartData} options={biotopeChartOptions} />
                    </Box>
                    <Text mt={4} fontSize="sm" color="gray.500">
                      Biotope ratings range from 0 (absent) to 5 (excellent condition).
                      Higher ratings indicate better habitat availability for macroinvertebrates.
                    </Text>
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Taxa List Tab */}
              <TabPanel p={0} pt={4}>
                <Card bg={cardBg}>
                  <CardHeader>
                    <Heading size="md">Taxa Observed (Latest Assessment)</Heading>
                  </CardHeader>
                  <CardBody>
                    {sassData.taxa_table && sassData.taxa_table.length > 0 ? (
                      <Table size="sm" variant="simple">
                        <Thead>
                          <Tr>
                            <Th>Taxon</Th>
                            <Th isNumeric>Score</Th>
                            <Th>Sensitivity</Th>
                            <Th>Abundance</Th>
                            <Th>Biotope</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {sassData.taxa_table.map((taxon, index) => (
                            <Tr key={index}>
                              <Td fontStyle="italic">{taxon.taxon_name}</Td>
                              <Td isNumeric>{taxon.score}</Td>
                              <Td>
                                <Badge
                                  colorScheme={
                                    taxon.sensitivity === 'highly_sensitive' ? 'green' :
                                    taxon.sensitivity === 'sensitive' ? 'blue' :
                                    taxon.sensitivity === 'tolerant' ? 'yellow' : 'red'
                                  }
                                >
                                  {taxon.sensitivity?.replace('_', ' ')}
                                </Badge>
                              </Td>
                              <Td>{taxon.abundance}</Td>
                              <Td>{taxon.biotope}</Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    ) : (
                      <Text color="gray.500" textAlign="center" py={8}>
                        No taxa data available
                      </Text>
                    )}
                  </CardBody>
                </Card>
              </TabPanel>
            </TabPanels>
          </Tabs>

          {/* Download Actions */}
          <Card bg={cardBg}>
            <CardBody>
              <HStack spacing={4}>
                <Button
                  colorScheme="blue"
                  variant="outline"
                  onClick={() => window.open(`/sass/download-sass-data-site/?siteId=${siteId}`, '_blank')}
                >
                  Download SASS Data (CSV)
                </Button>
                <Button
                  variant="outline"
                  onClick={() => window.open(`/sass/download-sass-summary-data/?siteId=${siteId}`, '_blank')}
                >
                  Download Summary
                </Button>
              </HStack>
            </CardBody>
          </Card>
        </VStack>
      </Container>
    </Box>
  );
};

export default SASSDashboardPage;
