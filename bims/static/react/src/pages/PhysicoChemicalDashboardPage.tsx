/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Physico-Chemical Dashboard Page - Chemical parameters dashboard for a site
 * Displays water chemistry data including pH, conductivity, dissolved oxygen, etc.
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
  Alert,
  AlertIcon,
  Wrap,
  WrapItem,
} from '@chakra-ui/react';
import { ChevronRightIcon, DownloadIcon } from '@chakra-ui/icons';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Chart colors
const CHART_COLORS = [
  '#8D2641', '#D7CD47', '#18A090', '#A2CE89', '#4E6440', '#525351',
  '#641f30', '#E6E188', '#9D9739', '#618295', '#2C495A', '#39B2A3',
];

interface ChemicalValue {
  value: number;
  str_date: string;
}

interface ChemicalParameter {
  unit: string;
  name: string;
  values: ChemicalValue[];
  minimum?: number;
  maximum?: number;
}

interface ChemicalRecords {
  [chemCode: string]: ChemicalParameter;
}

interface SiteInfo {
  site_code: string;
  site_description: string;
}

const PhysicoChemicalDashboardPage: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const navigate = useNavigate();

  const [chemicalData, setChemicalData] = useState<ChemicalRecords | null>(null);
  const [siteInfo, setSiteInfo] = useState<SiteInfo | null>(null);
  const [selectedParameter, setSelectedParameter] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  // Fetch chemical data
  useEffect(() => {
    const fetchData = async () => {
      if (!siteId) return;
      setIsLoading(true);
      setError(null);

      try {
        // Fetch physico-chemical page data
        const response = await fetch(`/physico-chemical/${siteId}/?format=json`);
        if (!response.ok) {
          if (response.status === 404) {
            setError('No physico-chemical data available for this site');
          } else {
            throw new Error('Failed to fetch chemical data');
          }
          return;
        }

        const data = await response.json();

        // Parse the chemical_records if it's a string
        let records = data.chemical_records;
        if (typeof records === 'string') {
          records = JSON.parse(records);
        }

        setChemicalData(records || {});

        // Set default selected parameter
        const paramKeys = Object.keys(records || {});
        if (paramKeys.length > 0 && !selectedParameter) {
          setSelectedParameter(paramKeys[0]);
        }
      } catch (err) {
        console.error('Failed to load chemical data:', err);
        setError('Failed to load physico-chemical data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
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

  // Calculate statistics for a parameter
  const calculateStats = (values: ChemicalValue[]) => {
    if (!values || values.length === 0) {
      return { mean: 0, min: 0, max: 0, count: 0, latest: 0 };
    }

    const nums = values.map(v => v.value).filter(v => v !== null && !isNaN(v));
    if (nums.length === 0) {
      return { mean: 0, min: 0, max: 0, count: 0, latest: 0 };
    }

    return {
      mean: nums.reduce((a, b) => a + b, 0) / nums.length,
      min: Math.min(...nums),
      max: Math.max(...nums),
      count: nums.length,
      latest: nums[nums.length - 1],
    };
  };

  // Get parameter list with stats
  const parameterList = useMemo(() => {
    if (!chemicalData) return [];

    return Object.entries(chemicalData).map(([code, param]) => ({
      code,
      name: param.name || code,
      unit: param.unit || '',
      stats: calculateStats(param.values),
      minimum: param.minimum,
      maximum: param.maximum,
    }));
  }, [chemicalData]);

  // Prepare chart data for selected parameter
  const chartData = useMemo(() => {
    if (!chemicalData || !selectedParameter || !chemicalData[selectedParameter]) {
      return null;
    }

    const param = chemicalData[selectedParameter];
    const values = param.values || [];

    return {
      labels: values.map(v => v.str_date),
      datasets: [
        {
          label: `${param.name || selectedParameter} (${param.unit || ''})`,
          data: values.map(v => v.value),
          backgroundColor: CHART_COLORS[0],
          borderColor: CHART_COLORS[0],
          borderWidth: 1,
        },
      ],
    };
  }, [chemicalData, selectedParameter]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: selectedParameter && chemicalData?.[selectedParameter]
          ? `${chemicalData[selectedParameter].name || selectedParameter} Over Time`
          : 'Chemical Parameter',
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date',
        },
      },
      y: {
        title: {
          display: true,
          text: selectedParameter && chemicalData?.[selectedParameter]
            ? `Value (${chemicalData[selectedParameter].unit || ''})`
            : 'Value',
        },
        beginAtZero: true,
      },
    },
  };

  // Handle CSV download
  const handleDownloadCSV = () => {
    window.open(`/api/chemical-record/download/?siteId=${siteId}`, '_blank');
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

  if (!chemicalData || Object.keys(chemicalData).length === 0) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
        <Container maxW="7xl">
          <VStack spacing={4}>
            <Alert status="info">
              <AlertIcon />
              No physico-chemical data available for this site.
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
              <BreadcrumbLink>Physico-Chemical</BreadcrumbLink>
            </BreadcrumbItem>
          </Breadcrumb>

          {/* Header */}
          <HStack justify="space-between" align="flex-start">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Physico-Chemical Dashboard</Heading>
              <Text color="gray.600">{siteInfo?.site_code} - {siteInfo?.site_description}</Text>
              <Badge colorScheme="purple">
                {parameterList.length} Parameters Measured
              </Badge>
            </VStack>
            <HStack>
              <Button
                leftIcon={<DownloadIcon />}
                colorScheme="blue"
                variant="outline"
                onClick={handleDownloadCSV}
              >
                Download CSV
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/dashboard/site/${siteId}`)}
              >
                Back to Site
              </Button>
            </HStack>
          </HStack>

          {/* Parameter Quick Stats */}
          <Wrap spacing={4}>
            {parameterList.slice(0, 4).map((param, index) => (
              <WrapItem key={param.code}>
                <Card bg={cardBg} minW="200px">
                  <CardBody>
                    <Stat>
                      <StatLabel>{param.name}</StatLabel>
                      <StatNumber color={`${['green', 'blue', 'purple', 'orange'][index % 4]}.500`}>
                        {param.stats.latest.toFixed(2)} {param.unit}
                      </StatNumber>
                      <StatHelpText>Latest reading</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
              </WrapItem>
            ))}
          </Wrap>

          {/* Parameter Selection and Chart */}
          <Card bg={cardBg}>
            <CardHeader>
              <HStack justify="space-between">
                <Heading size="md">Parameter Trends</Heading>
                <Select
                  value={selectedParameter}
                  onChange={(e) => setSelectedParameter(e.target.value)}
                  w="250px"
                >
                  {parameterList.map(param => (
                    <option key={param.code} value={param.code}>
                      {param.name} ({param.unit})
                    </option>
                  ))}
                </Select>
              </HStack>
            </CardHeader>
            <CardBody>
              {chartData ? (
                <Box h="400px">
                  <Bar data={chartData} options={chartOptions} />
                </Box>
              ) : (
                <Text color="gray.500" textAlign="center" py={8}>
                  Select a parameter to view the chart
                </Text>
              )}
            </CardBody>
          </Card>

          {/* All Parameters Table */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">All Parameters Summary</Heading>
            </CardHeader>
            <CardBody>
              <Table size="sm" variant="simple">
                <Thead>
                  <Tr>
                    <Th>Parameter</Th>
                    <Th>Unit</Th>
                    <Th isNumeric>Latest</Th>
                    <Th isNumeric>Mean</Th>
                    <Th isNumeric>Min</Th>
                    <Th isNumeric>Max</Th>
                    <Th isNumeric>Records</Th>
                    <Th>Status</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {parameterList.map(param => {
                    const isOutOfRange = (param.minimum !== undefined && param.stats.latest < param.minimum) ||
                                        (param.maximum !== undefined && param.stats.latest > param.maximum);
                    return (
                      <Tr
                        key={param.code}
                        cursor="pointer"
                        _hover={{ bg: 'gray.50' }}
                        onClick={() => setSelectedParameter(param.code)}
                        bg={selectedParameter === param.code ? 'blue.50' : undefined}
                      >
                        <Td fontWeight="medium">{param.name}</Td>
                        <Td>{param.unit}</Td>
                        <Td isNumeric>{param.stats.latest.toFixed(2)}</Td>
                        <Td isNumeric>{param.stats.mean.toFixed(2)}</Td>
                        <Td isNumeric>{param.stats.min.toFixed(2)}</Td>
                        <Td isNumeric>{param.stats.max.toFixed(2)}</Td>
                        <Td isNumeric>{param.stats.count}</Td>
                        <Td>
                          {isOutOfRange ? (
                            <Badge colorScheme="red">Out of Range</Badge>
                          ) : (
                            <Badge colorScheme="green">Normal</Badge>
                          )}
                        </Td>
                      </Tr>
                    );
                  })}
                </Tbody>
              </Table>
            </CardBody>
          </Card>

          {/* Actions */}
          <Card bg={cardBg}>
            <CardBody>
              <HStack spacing={4}>
                <Button
                  colorScheme="blue"
                  onClick={() => window.open(`/physico-chemical-form/?siteId=${siteId}`, '_blank')}
                >
                  Add New Measurements
                </Button>
                <Button
                  variant="outline"
                  onClick={() => window.open(`/upload-physico-chemical/`, '_blank')}
                >
                  Bulk Upload Data
                </Button>
              </HStack>
            </CardBody>
          </Card>
        </VStack>
      </Container>
    </Box>
  );
};

export default PhysicoChemicalDashboardPage;
