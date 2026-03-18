/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Water Temperature Dashboard Page - Thermal analysis dashboard for a site
 * Displays temperature trends, thermograph data, and thermal indicators.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState, useMemo } from 'react';
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
  FormControl,
  FormLabel,
  Input,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  useToast,
} from '@chakra-ui/react';
import { ChevronRightIcon, SettingsIcon } from '@chakra-ui/icons';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ThermalData {
  date_time: string[];
  mean_7: number[];
  min_7: number[];
  max_7: number[];
  '95%_low': number[];
  '95%_up': number[];
  'L95%_1SD': number[];
  'U95%_1SD': number[];
  'L95%_2SD': number[];
  'U95%_2SD': number[];
}

interface ThresholdData {
  thermal_zone: string;
  maximum_threshold: number;
  minimum_threshold: number;
  mean_threshold: number;
  record_length: number;
  degree_days: number;
}

interface IndicatorsData {
  year: number;
  annual: {
    annual_mean: number;
    annual_max: number;
    annual_min: number;
    annual_range: number;
    annual_sd: number;
    annual_cv: number;
  };
  monthly: Record<string, {
    monthly_mean: number;
    monthly_max: number;
    monthly_min: number;
    monthly_range: number;
  }>;
  threshold: {
    weekly_mean: number;
    weekly_min: number;
    weekly_max: number;
    weekly_mean_dur: number;
    weekly_min_dur: number;
    weekly_max_dur: number;
  };
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const WaterTemperatureDashboardPage: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const [thermalData, setThermalData] = useState<ThermalData | null>(null);
  const [thresholds, setThresholds] = useState<ThresholdData | null>(null);
  const [indicators, setIndicators] = useState<IndicatorsData | null>(null);
  const [siteInfo, setSiteInfo] = useState<{ site_code: string; site_description: string } | null>(null);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Threshold edit modal
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [editThresholds, setEditThresholds] = useState({
    maximum_threshold: 23.2,
    minimum_threshold: 12.0,
    mean_threshold: 18.0,
  });

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  // Fetch thermal data
  useEffect(() => {
    const fetchData = async () => {
      if (!siteId) return;
      setIsLoading(true);
      setError(null);

      try {
        // Build URL with year parameter if selected
        let url = `/api/thermal-data/?site-id=${siteId}`;
        if (selectedYear) {
          url += `&year=${selectedYear}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
          if (response.status === 404) {
            setError('No water temperature data available for this site');
          } else {
            throw new Error('Failed to fetch thermal data');
          }
          return;
        }

        const data = await response.json();
        setThermalData(data);

        // Extract available years from data
        if (data.date_time && data.date_time.length > 0) {
          const years = [...new Set(data.date_time.map((d: string) => new Date(d).getFullYear()))];
          setAvailableYears(years.sort((a, b) => b - a));
          if (!selectedYear && years.length > 0) {
            setSelectedYear(String(years[0]));
          }
        }
      } catch (err) {
        console.error('Failed to load thermal data:', err);
        setError('Failed to load water temperature data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [siteId, selectedYear]);

  // Fetch thresholds
  useEffect(() => {
    const fetchThresholds = async () => {
      if (!siteId) return;

      try {
        const response = await fetch(`/api/water-temperature-threshold/?location_site=${siteId}`);
        if (response.ok) {
          const data = await response.json();
          setThresholds(data);
          setEditThresholds({
            maximum_threshold: data.maximum_threshold || 23.2,
            minimum_threshold: data.minimum_threshold || 12.0,
            mean_threshold: data.mean_threshold || 18.0,
          });
        }
      } catch (err) {
        console.error('Failed to fetch thresholds:', err);
      }
    };

    fetchThresholds();
  }, [siteId]);

  // Fetch site info
  useEffect(() => {
    const fetchSiteInfo = async () => {
      if (!siteId) return;

      try {
        const response = await fetch(`/api/location-site-detail/?siteId=${siteId}`);
        if (response.ok) {
          const data = await response.json();
          setSiteInfo({
            site_code: data.site_detail_info?.site_code || `Site ${siteId}`,
            site_description: data.site_detail_info?.site_description || '',
          });
        }
      } catch (err) {
        console.error('Failed to fetch site info:', err);
      }
    };

    fetchSiteInfo();
  }, [siteId]);

  // Calculate indicators from thermal data
  const calculatedIndicators = useMemo(() => {
    if (!thermalData || !thermalData.mean_7 || thermalData.mean_7.length === 0) {
      return null;
    }

    const mean7 = thermalData.mean_7.filter(v => v !== null && !isNaN(v));
    const min7 = thermalData.min_7?.filter(v => v !== null && !isNaN(v)) || [];
    const max7 = thermalData.max_7?.filter(v => v !== null && !isNaN(v)) || [];

    if (mean7.length === 0) return null;

    const annualMean = mean7.reduce((a, b) => a + b, 0) / mean7.length;
    const annualMax = max7.length > 0 ? Math.max(...max7) : Math.max(...mean7);
    const annualMin = min7.length > 0 ? Math.min(...min7) : Math.min(...mean7);
    const annualRange = annualMax - annualMin;

    // Standard deviation
    const variance = mean7.reduce((sum, val) => sum + Math.pow(val - annualMean, 2), 0) / mean7.length;
    const annualSD = Math.sqrt(variance);
    const annualCV = (annualSD / annualMean) * 100;

    return {
      annual_mean: annualMean,
      annual_max: annualMax,
      annual_min: annualMin,
      annual_range: annualRange,
      annual_sd: annualSD,
      annual_cv: annualCV,
    };
  }, [thermalData]);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!thermalData || !thermalData.date_time) {
      return null;
    }

    return {
      labels: thermalData.date_time,
      datasets: [
        {
          label: '95% Upper',
          data: thermalData['95%_up'],
          borderColor: 'rgba(255, 99, 132, 0.3)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          fill: '+1',
          pointRadius: 0,
          borderWidth: 1,
        },
        {
          label: '95% Lower',
          data: thermalData['95%_low'],
          borderColor: 'rgba(255, 99, 132, 0.3)',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
          borderWidth: 1,
        },
        {
          label: 'Max (7-day avg)',
          data: thermalData.max_7,
          borderColor: '#d9534f',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: 'Mean (7-day avg)',
          data: thermalData.mean_7,
          borderColor: '#5cb85c',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: 'Min (7-day avg)',
          data: thermalData.min_7,
          borderColor: '#5bc0de',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    };
  }, [thermalData]);

  const chartOptions = {
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
        text: 'Water Temperature Thermograph',
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y?.toFixed(1)}°C`;
          }
        }
      }
    },
    scales: {
      x: {
        type: 'category' as const,
        title: {
          display: true,
          text: 'Date',
        },
        ticks: {
          maxTicksLimit: 12,
        },
      },
      y: {
        title: {
          display: true,
          text: 'Temperature (°C)',
        },
      },
    },
  };

  const handleSaveThresholds = async () => {
    try {
      const response = await fetch(`/api/water-temperature-threshold/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location_site: siteId,
          ...editThresholds,
        }),
      });

      if (response.ok) {
        toast({
          title: 'Thresholds updated',
          status: 'success',
          duration: 3000,
        });
        onClose();
        // Refresh thresholds
        const data = await response.json();
        setThresholds(data);
      } else {
        throw new Error('Failed to save thresholds');
      }
    } catch (err) {
      toast({
        title: 'Failed to update thresholds',
        status: 'error',
        duration: 3000,
      });
    }
  };

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
            <Button onClick={() => navigate(`/dashboard/site/${siteId}`)}>Back to Site Dashboard</Button>
          </VStack>
        </Container>
      </Box>
    );
  }

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
                {siteInfo?.site_code || `Site ${siteId}`}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem isCurrentPage>
              <BreadcrumbLink>Water Temperature</BreadcrumbLink>
            </BreadcrumbItem>
          </Breadcrumb>

          {/* Header */}
          <HStack justify="space-between" align="flex-start">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Water Temperature Dashboard</Heading>
              <Text color="gray.600">{siteInfo?.site_code} - {siteInfo?.site_description}</Text>
              {thresholds?.thermal_zone && (
                <Badge colorScheme={thresholds.thermal_zone === 'upper' ? 'blue' : 'orange'}>
                  {thresholds.thermal_zone.charAt(0).toUpperCase() + thresholds.thermal_zone.slice(1)} Thermal Zone
                </Badge>
              )}
            </VStack>
            <HStack>
              <Select
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
                w="120px"
              >
                {availableYears.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </Select>
              <Button
                leftIcon={<SettingsIcon />}
                variant="outline"
                onClick={onOpen}
              >
                Thresholds
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/dashboard/site/${siteId}`)}
              >
                Back to Site
              </Button>
            </HStack>
          </HStack>

          {/* Summary Stats */}
          {calculatedIndicators && (
            <StatGroup>
              <Card bg={cardBg} flex={1}>
                <CardBody>
                  <Stat>
                    <StatLabel>Annual Mean</StatLabel>
                    <StatNumber color="green.500">
                      {calculatedIndicators.annual_mean.toFixed(1)}°C
                    </StatNumber>
                    <StatHelpText>Average temperature</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg} flex={1}>
                <CardBody>
                  <Stat>
                    <StatLabel>Maximum</StatLabel>
                    <StatNumber color="red.500">
                      {calculatedIndicators.annual_max.toFixed(1)}°C
                    </StatNumber>
                    <StatHelpText>Highest recorded</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg} flex={1}>
                <CardBody>
                  <Stat>
                    <StatLabel>Minimum</StatLabel>
                    <StatNumber color="blue.500">
                      {calculatedIndicators.annual_min.toFixed(1)}°C
                    </StatNumber>
                    <StatHelpText>Lowest recorded</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg} flex={1}>
                <CardBody>
                  <Stat>
                    <StatLabel>Range</StatLabel>
                    <StatNumber color="purple.500">
                      {calculatedIndicators.annual_range.toFixed(1)}°C
                    </StatNumber>
                    <StatHelpText>Max - Min</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </StatGroup>
          )}

          {/* Thermograph Chart */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Temperature Thermograph</Heading>
            </CardHeader>
            <CardBody>
              {chartData ? (
                <Box h="400px">
                  <Line data={chartData} options={chartOptions} />
                </Box>
              ) : (
                <Text color="gray.500" textAlign="center" py={8}>
                  No temperature data available for visualization
                </Text>
              )}
            </CardBody>
          </Card>

          {/* Indicators Table */}
          <Tabs variant="enclosed" colorScheme="blue">
            <TabList>
              <Tab>Annual Statistics</Tab>
              <Tab>Threshold Exceedance</Tab>
              <Tab>Thresholds</Tab>
            </TabList>

            <TabPanels>
              {/* Annual Statistics */}
              <TabPanel p={0} pt={4}>
                <Card bg={cardBg}>
                  <CardBody>
                    {calculatedIndicators ? (
                      <Table size="sm" variant="simple">
                        <Thead>
                          <Tr>
                            <Th>Indicator</Th>
                            <Th isNumeric>Value</Th>
                            <Th>Unit</Th>
                            <Th>Description</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          <Tr>
                            <Td fontWeight="medium">Annual Mean</Td>
                            <Td isNumeric>{calculatedIndicators.annual_mean.toFixed(2)}</Td>
                            <Td>°C</Td>
                            <Td>Average temperature over the year</Td>
                          </Tr>
                          <Tr>
                            <Td fontWeight="medium">Annual Maximum</Td>
                            <Td isNumeric>{calculatedIndicators.annual_max.toFixed(2)}</Td>
                            <Td>°C</Td>
                            <Td>Highest temperature recorded</Td>
                          </Tr>
                          <Tr>
                            <Td fontWeight="medium">Annual Minimum</Td>
                            <Td isNumeric>{calculatedIndicators.annual_min.toFixed(2)}</Td>
                            <Td>°C</Td>
                            <Td>Lowest temperature recorded</Td>
                          </Tr>
                          <Tr>
                            <Td fontWeight="medium">Annual Range</Td>
                            <Td isNumeric>{calculatedIndicators.annual_range.toFixed(2)}</Td>
                            <Td>°C</Td>
                            <Td>Difference between max and min</Td>
                          </Tr>
                          <Tr>
                            <Td fontWeight="medium">Standard Deviation</Td>
                            <Td isNumeric>{calculatedIndicators.annual_sd.toFixed(2)}</Td>
                            <Td>°C</Td>
                            <Td>Temperature variability</Td>
                          </Tr>
                          <Tr>
                            <Td fontWeight="medium">Coefficient of Variation</Td>
                            <Td isNumeric>{calculatedIndicators.annual_cv.toFixed(2)}</Td>
                            <Td>%</Td>
                            <Td>Relative variability</Td>
                          </Tr>
                        </Tbody>
                      </Table>
                    ) : (
                      <Text color="gray.500" textAlign="center" py={8}>
                        No statistical data available
                      </Text>
                    )}
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Threshold Exceedance */}
              <TabPanel p={0} pt={4}>
                <Card bg={cardBg}>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <Alert status="info">
                        <AlertIcon />
                        Threshold exceedance analysis shows how often temperatures exceeded critical thresholds.
                      </Alert>
                      <Table size="sm" variant="simple">
                        <Thead>
                          <Tr>
                            <Th>Threshold Type</Th>
                            <Th isNumeric>Value (°C)</Th>
                            <Th isNumeric>Days Exceeded</Th>
                            <Th isNumeric>Max Duration (days)</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          <Tr>
                            <Td fontWeight="medium">Maximum</Td>
                            <Td isNumeric>{thresholds?.maximum_threshold || 23.2}</Td>
                            <Td isNumeric>-</Td>
                            <Td isNumeric>-</Td>
                          </Tr>
                          <Tr>
                            <Td fontWeight="medium">Mean</Td>
                            <Td isNumeric>{thresholds?.mean_threshold || 18.0}</Td>
                            <Td isNumeric>-</Td>
                            <Td isNumeric>-</Td>
                          </Tr>
                          <Tr>
                            <Td fontWeight="medium">Minimum</Td>
                            <Td isNumeric>{thresholds?.minimum_threshold || 12.0}</Td>
                            <Td isNumeric>-</Td>
                            <Td isNumeric>-</Td>
                          </Tr>
                        </Tbody>
                      </Table>
                      <Text fontSize="sm" color="gray.500">
                        Note: Detailed exceedance counts require full thermal indicator calculations.
                        Visit the full thermal dashboard for complete analysis.
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Current Thresholds */}
              <TabPanel p={0} pt={4}>
                <Card bg={cardBg}>
                  <CardHeader>
                    <HStack justify="space-between">
                      <Heading size="md">Current Thresholds</Heading>
                      <Button size="sm" colorScheme="blue" onClick={onOpen}>
                        Edit Thresholds
                      </Button>
                    </HStack>
                  </CardHeader>
                  <CardBody>
                    <Table size="sm" variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Parameter</Th>
                          <Th isNumeric>Value</Th>
                          <Th>Description</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        <Tr>
                          <Td fontWeight="medium">Maximum Threshold</Td>
                          <Td isNumeric>{thresholds?.maximum_threshold || 23.2}°C</Td>
                          <Td>Upper limit for thermal stress</Td>
                        </Tr>
                        <Tr>
                          <Td fontWeight="medium">Mean Threshold</Td>
                          <Td isNumeric>{thresholds?.mean_threshold || 18.0}°C</Td>
                          <Td>Optimal mean temperature</Td>
                        </Tr>
                        <Tr>
                          <Td fontWeight="medium">Minimum Threshold</Td>
                          <Td isNumeric>{thresholds?.minimum_threshold || 12.0}°C</Td>
                          <Td>Lower limit for cold stress</Td>
                        </Tr>
                        <Tr>
                          <Td fontWeight="medium">Thermal Zone</Td>
                          <Td isNumeric>-</Td>
                          <Td>{thresholds?.thermal_zone || 'Not determined'}</Td>
                        </Tr>
                      </Tbody>
                    </Table>
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
                  onClick={() => navigate(`/thermal-dashboard/?site-id=${siteId}&year=${selectedYear}`)}
                >
                  View Full Thermal Dashboard
                </Button>
                <Button
                  variant="outline"
                  onClick={() => window.open(`/water-temperature-form/?siteId=${siteId}`, '_blank')}
                >
                  Upload Temperature Data
                </Button>
              </HStack>
            </CardBody>
          </Card>
        </VStack>
      </Container>

      {/* Threshold Edit Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Edit Temperature Thresholds</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl>
                <FormLabel>Maximum Threshold (°C)</FormLabel>
                <Input
                  type="number"
                  step="0.1"
                  value={editThresholds.maximum_threshold}
                  onChange={(e) => setEditThresholds({
                    ...editThresholds,
                    maximum_threshold: parseFloat(e.target.value),
                  })}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Mean Threshold (°C)</FormLabel>
                <Input
                  type="number"
                  step="0.1"
                  value={editThresholds.mean_threshold}
                  onChange={(e) => setEditThresholds({
                    ...editThresholds,
                    mean_threshold: parseFloat(e.target.value),
                  })}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Minimum Threshold (°C)</FormLabel>
                <Input
                  type="number"
                  step="0.1"
                  value={editThresholds.minimum_threshold}
                  onChange={(e) => setEditThresholds({
                    ...editThresholds,
                    minimum_threshold: parseFloat(e.target.value),
                  })}
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>Cancel</Button>
            <Button colorScheme="blue" onClick={handleSaveThresholds}>
              Save Thresholds
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default WaterTemperatureDashboardPage;
