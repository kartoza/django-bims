/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Site Detail Panel - Display detailed information about a location site
 * Matches the original BIMS side panel structure with collapsible sections.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  IconButton,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Table,
  Tbody,
  Tr,
  Td,
  Skeleton,
  SkeletonText,
  useColorModeValue,
  Button,
  Spinner,
  Grid,
  GridItem,
  Image,
  Tooltip,
} from '@chakra-ui/react';
import { CloseIcon, ChevronLeftIcon } from '@chakra-ui/icons';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, ArcElement, Tooltip as ChartTooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { apiClient } from '../../api/client';

// Register Chart.js components
ChartJS.register(ArcElement, ChartTooltip, Legend);

interface SiteDetailData {
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
  climate_exist?: boolean;
  geometry?: string;
}

interface SiteDetailPanelProps {
  siteId: number;
  onClose: () => void;
  onFlyTo?: (coords: [number, number], zoom?: number) => void;
}

// Chart colors matching the original BIMS
const CHART_COLORS = [
  '#8D2641', '#D7CD47', '#18A090', '#A2CE89', '#4E6440', '#525351',
  '#641f30', '#E6E188', '#9D9739', '#618295', '#2C495A', '#39B2A3',
];

const MiniPieChart: React.FC<{
  data: Array<{ name: string; count: number; colour?: string }>;
  size?: number;
}> = ({ data, size = 50 }) => {
  if (!data || data.length === 0) {
    return <Box w={`${size}px`} h={`${size}px`} bg="gray.100" borderRadius="full" />;
  }

  const chartData = {
    labels: data.map(d => d.name),
    datasets: [{
      data: data.map(d => d.count),
      backgroundColor: data.map((d, i) => d.colour || CHART_COLORS[i % CHART_COLORS.length]),
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

const ChartLegend: React.FC<{
  data: Array<{ name: string; count: number; colour?: string }>;
}> = ({ data }) => {
  if (!data || data.length === 0) return null;

  return (
    <VStack align="start" spacing={0} fontSize="xs">
      {data.map((item, idx) => (
        <HStack key={item.name} spacing={1}>
          <Box
            w="8px"
            h="8px"
            bg={item.colour || CHART_COLORS[idx % CHART_COLORS.length]}
          />
          <Text noOfLines={1} maxW="80px" title={item.name}>
            {item.name}
          </Text>
        </HStack>
      ))}
    </VStack>
  );
};

export const SiteDetailPanel: React.FC<SiteDetailPanelProps> = ({
  siteId,
  onClose,
  onFlyTo,
}) => {
  const navigate = useNavigate();
  const [siteData, setSiteData] = useState<SiteDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hasFetchedRef = useRef(false);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const headerBg = useColorModeValue('gray.50', 'gray.700');

  // Fetch site details from the original API endpoint
  useEffect(() => {
    if (hasFetchedRef.current) return;
    hasFetchedRef.current = true;

    const fetchSiteDetail = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Use the original location-site-detail API endpoint
        const response = await apiClient.get<SiteDetailData>(
          `/location-site-detail/?siteId=${siteId}`,
          { baseURL: '/api' } // Use the legacy API
        );
        setSiteData(response.data);

        // Fly to site location
        if (response.data?.site_detail_info?.site_coordinates && onFlyTo) {
          const coords = response.data.site_detail_info.site_coordinates.split(',');
          if (coords.length === 2) {
            const lon = parseFloat(coords[0].trim());
            const lat = parseFloat(coords[1].trim());
            if (!isNaN(lon) && !isNaN(lat)) {
              onFlyTo([lon, lat], 14);
            }
          }
        }
      } catch (err) {
        console.error('Failed to load site details:', err);
        setError('Failed to load site details');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSiteDetail();
  }, [siteId, onFlyTo]);

  // Reset fetch ref when siteId changes
  useEffect(() => {
    hasFetchedRef.current = false;
  }, [siteId]);

  if (isLoading) {
    return (
      <Box
        position="absolute"
        right={0}
        top={0}
        bottom={0}
        width="400px"
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

  if (error || !siteData) {
    return (
      <Box
        position="absolute"
        right={0}
        top={0}
        bottom={0}
        width="400px"
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

  const { site_detail_info, location_context, biodiversity_data, climate_data } = siteData;

  return (
    <Box
      position="absolute"
      right={0}
      top={0}
      bottom={0}
      width="400px"
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
        p={3}
        bg={headerBg}
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
          <Heading size="sm" noOfLines={1}>
            {site_detail_info?.site_code || 'Site Details'}
          </Heading>
        </HStack>
        <IconButton
          aria-label="Close"
          icon={<CloseIcon boxSize={3} />}
          variant="ghost"
          size="sm"
          onClick={onClose}
        />
      </HStack>

      {/* Content - Collapsible Sections */}
      <Box flex={1} overflow="auto">
        <Accordion defaultIndex={[0, 1]} allowMultiple>
          {/* Site Details Section */}
          <AccordionItem border="none">
            <AccordionButton bg={headerBg} _hover={{ bg: 'gray.100' }}>
              <Box flex="1" textAlign="left" fontWeight="bold">
                Site Details
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <Table size="sm" variant="simple">
                <Tbody>
                  {site_detail_info?.ecosystem_type && (
                    <Tr>
                      <Td fontWeight="medium" w="40%">Ecosystem Type</Td>
                      <Td>{site_detail_info.ecosystem_type}</Td>
                    </Tr>
                  )}
                  <Tr>
                    <Td fontWeight="medium">Site Code</Td>
                    <Td>{site_detail_info?.site_code}</Td>
                  </Tr>
                  {site_detail_info?.site_description && (
                    <Tr>
                      <Td fontWeight="medium">Site Description</Td>
                      <Td>{site_detail_info.site_description}</Td>
                    </Tr>
                  )}
                  <Tr>
                    <Td fontWeight="medium">Site Coordinates</Td>
                    <Td>{site_detail_info?.site_coordinates}</Td>
                  </Tr>
                  {/* Location Context */}
                  {location_context && Object.entries(location_context).map(([key, value]) => (
                    <Tr key={key}>
                      <Td fontWeight="medium">{key}</Td>
                      <Td>{value}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </AccordionPanel>
          </AccordionItem>

          {/* Biodiversity Data Section */}
          <AccordionItem border="none">
            <AccordionButton bg={headerBg} _hover={{ bg: 'gray.100' }}>
              <Box flex="1" textAlign="left" fontWeight="bold">
                Biodiversity Data
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              {biodiversity_data && Object.keys(biodiversity_data).length > 0 ? (
                <VStack spacing={3} align="stretch">
                  {/* Header Row */}
                  <Grid
                    templateColumns="60px 50px 55px 55px 55px 40px"
                    gap={1}
                    fontSize="xs"
                    fontWeight="bold"
                    textAlign="center"
                  >
                    <GridItem></GridItem>
                    <GridItem>Occur.</GridItem>
                    <GridItem>Origin</GridItem>
                    <GridItem>Endemic</GridItem>
                    <GridItem>Cons.</GridItem>
                    <GridItem>Taxa</GridItem>
                  </Grid>

                  {/* Data Rows */}
                  {Object.entries(biodiversity_data).map(([moduleName, moduleData]) => (
                    <Box
                      key={moduleName}
                      borderBottom="1px"
                      borderColor={borderColor}
                      pb={2}
                    >
                      <Grid
                        templateColumns="60px 50px 55px 55px 55px 40px"
                        gap={1}
                        alignItems="center"
                      >
                        {/* Module Icon */}
                        <GridItem>
                          <Tooltip label={moduleName}>
                            <Box>
                              {moduleData.icon ? (
                                <Image
                                  src={`/uploaded/${moduleData.icon}`}
                                  alt={moduleName}
                                  boxSize="40px"
                                  objectFit="contain"
                                  fallback={
                                    <Text fontSize="xs" noOfLines={1}>
                                      {moduleName}
                                    </Text>
                                  }
                                />
                              ) : (
                                <Text fontSize="xs" noOfLines={1}>
                                  {moduleName}
                                </Text>
                              )}
                            </Box>
                          </Tooltip>
                        </GridItem>

                        {/* Occurrences */}
                        <GridItem textAlign="center">
                          <Text fontSize="sm" fontWeight="medium">
                            {moduleData.occurrences || 0}
                          </Text>
                        </GridItem>

                        {/* Origin Chart */}
                        <GridItem>
                          <MiniPieChart data={moduleData.origin} size={45} />
                        </GridItem>

                        {/* Endemism Chart */}
                        <GridItem>
                          <MiniPieChart data={moduleData.endemism} size={45} />
                        </GridItem>

                        {/* Conservation Status Chart */}
                        <GridItem>
                          <MiniPieChart data={moduleData.cons_status} size={45} />
                        </GridItem>

                        {/* Number of Taxa */}
                        <GridItem textAlign="center">
                          <Text fontSize="sm" fontWeight="medium">
                            {moduleData.number_of_taxa || 0}
                          </Text>
                        </GridItem>
                      </Grid>

                      {/* Action Buttons */}
                      <HStack mt={2} spacing={2} justify="flex-end">
                        <Button
                          size="xs"
                          colorScheme="red"
                          variant="solid"
                          onClick={() => {
                            // Navigate to add record form (uses legacy routes for now)
                            const name = moduleName.toLowerCase();
                            let url = `/module-form/?siteId=${siteId}&module=${moduleData.module}`;
                            if (name === 'fish') url = `/fish-form/?siteId=${siteId}`;
                            else if (name === 'invertebrates') url = `/invert-form/?siteId=${siteId}`;
                            else if (name === 'algae') url = `/algae-form/?siteId=${siteId}`;
                            window.location.href = url;
                          }}
                        >
                          + Add
                        </Button>
                        <Button
                          size="xs"
                          colorScheme="blue"
                          variant="outline"
                          isDisabled={!moduleData.number_of_taxa}
                          onClick={() => {
                            // Navigate to React site dashboard with module filter
                            navigate(`/dashboard/site/${siteId}?module=${moduleData.module}`);
                          }}
                        >
                          Dashboard &gt;&gt;
                        </Button>
                      </HStack>
                    </Box>
                  ))}

                  {/* Summary Dashboard Button */}
                  <Button
                    size="sm"
                    colorScheme="blue"
                    width="100%"
                    onClick={() => {
                      // Navigate to React site dashboard
                      navigate(`/dashboard/site/${siteId}`);
                    }}
                  >
                    Summary Dashboard &gt;&gt;
                  </Button>

                  {/* Additional Buttons */}
                  <HStack spacing={2}>
                    <Button
                      size="sm"
                      flex={1}
                      isDisabled={!siteData.sass_exist}
                      onClick={() => {
                        // Navigate to React SASS dashboard
                        navigate(`/dashboard/sass/${siteId}`);
                      }}
                    >
                      SASS Dashboard
                    </Button>
                  </HStack>

                  <HStack spacing={2}>
                    <Button
                      size="sm"
                      flex={1}
                      isDisabled={!siteData.water_temperature_exist}
                      onClick={() => {
                        // Navigate to React water temperature dashboard
                        navigate(`/dashboard/water-temperature/${siteId}`);
                      }}
                    >
                      Water Temperature
                    </Button>
                    <Button
                      size="sm"
                      flex={1}
                      colorScheme="red"
                      onClick={() => {
                        // Legacy form route (until React form is implemented)
                        window.location.href = `/water-temperature-form/?siteId=${siteId}`;
                      }}
                    >
                      Add
                    </Button>
                  </HStack>

                  <HStack spacing={2}>
                    <Button
                      size="sm"
                      flex={1}
                      isDisabled={!siteData.physico_chemical_exist}
                      onClick={() => {
                        // Navigate to React physico-chemical dashboard
                        navigate(`/dashboard/physico-chemical/${siteId}`);
                      }}
                    >
                      Physico-chemical
                    </Button>
                    <Button
                      size="sm"
                      flex={1}
                      colorScheme="red"
                      onClick={() => {
                        // Legacy form route (until React form is implemented)
                        window.location.href = `/physico-chemical-form/?siteId=${siteId}`;
                      }}
                    >
                      Add
                    </Button>
                  </HStack>
                </VStack>
              ) : (
                <Text color="gray.500" textAlign="center" py={4}>
                  No biodiversity data available
                </Text>
              )}
            </AccordionPanel>
          </AccordionItem>

          {/* Climate Data Section */}
          {climate_data && Object.keys(climate_data).length > 0 && (
            <AccordionItem border="none">
              <AccordionButton bg={headerBg} _hover={{ bg: 'gray.100' }}>
                <Box flex="1" textAlign="left" fontWeight="bold">
                  Climate Data
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel pb={4}>
                <VStack spacing={4} align="stretch">
                  {Object.entries(climate_data).map(([key, data]) => (
                    <Box key={key}>
                      <Text fontWeight="medium" mb={2}>
                        {data.title}
                      </Text>
                      {/* Simple representation - could add line charts here */}
                      <Box bg="gray.100" p={2} borderRadius="md">
                        <Text fontSize="sm" color="gray.600">
                          {data.values?.length || 0} data points
                        </Text>
                      </Box>
                    </Box>
                  ))}
                </VStack>
              </AccordionPanel>
            </AccordionItem>
          )}
        </Accordion>
      </Box>

      {/* Footer */}
      <Box
        p={2}
        borderTop="1px"
        borderColor={borderColor}
        fontSize="xs"
        color="gray.500"
        textAlign="center"
      >
        Site ID: {siteId}
      </Box>
    </Box>
  );
};

export default SiteDetailPanel;
