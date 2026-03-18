/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Data Harvest page for importing data from external sources.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState } from 'react';
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
  FormHelperText,
  Input,
  Textarea,
  Button,
  useToast,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  SimpleGrid,
  Select,
  Progress,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Icon,
  Alert,
  AlertIcon,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Code,
} from '@chakra-ui/react';
import {
  DownloadIcon,
  SearchIcon,
  CheckCircleIcon,
  WarningIcon,
  TimeIcon,
  RepeatIcon,
} from '@chakra-ui/icons';

interface HarvestJob {
  id: string;
  source: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  recordsProcessed: number;
  recordsAdded: number;
  startedAt: string;
  completedAt?: string;
}

const HarvestPage: React.FC = () => {
  const toast = useToast();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  const [gbifQuery, setGbifQuery] = useState({
    scientificName: '',
    country: 'ZA',
    basisOfRecord: 'HUMAN_OBSERVATION',
    limit: 1000,
  });

  const [fishbaseQuery, setFishbaseQuery] = useState({
    genus: '',
    species: '',
    family: '',
  });

  const [harvestJobs, setHarvestJobs] = useState<HarvestJob[]>([
    {
      id: '1',
      source: 'GBIF',
      type: 'Occurrence Records',
      status: 'completed',
      progress: 100,
      recordsProcessed: 5420,
      recordsAdded: 342,
      startedAt: '2024-01-15T10:30:00Z',
      completedAt: '2024-01-15T10:45:00Z',
    },
    {
      id: '2',
      source: 'FishBase',
      type: 'Species Data',
      status: 'running',
      progress: 65,
      recordsProcessed: 128,
      recordsAdded: 45,
      startedAt: '2024-01-15T11:00:00Z',
    },
    {
      id: '3',
      source: 'IUCN',
      type: 'Conservation Status',
      status: 'pending',
      progress: 0,
      recordsProcessed: 0,
      recordsAdded: 0,
      startedAt: '2024-01-15T11:05:00Z',
    },
  ]);

  const [isHarvesting, setIsHarvesting] = useState(false);

  const startGBIFHarvest = async () => {
    setIsHarvesting(true);
    try {
      // In a real implementation, this would call the API
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const newJob: HarvestJob = {
        id: Date.now().toString(),
        source: 'GBIF',
        type: 'Occurrence Records',
        status: 'running',
        progress: 0,
        recordsProcessed: 0,
        recordsAdded: 0,
        startedAt: new Date().toISOString(),
      };
      setHarvestJobs((prev) => [newJob, ...prev]);

      toast({
        title: 'Harvest started',
        description: 'GBIF data harvest has been initiated.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Harvest failed',
        description: 'Failed to start GBIF harvest. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsHarvesting(false);
    }
  };

  const getStatusColor = (status: HarvestJob['status']) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'running':
        return 'blue';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status: HarvestJob['status']) => {
    switch (status) {
      case 'completed':
        return CheckCircleIcon;
      case 'running':
        return RepeatIcon;
      case 'failed':
        return WarningIcon;
      default:
        return TimeIcon;
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <HStack>
                <DownloadIcon />
                <Heading size="lg">Data Harvest</Heading>
              </HStack>
              <Text opacity={0.9}>
                Import biodiversity data from external sources
              </Text>
            </VStack>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        {/* Quick Stats */}
        <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} mb={8}>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Total Harvests</StatLabel>
                <StatNumber>{harvestJobs.length}</StatNumber>
                <StatHelpText>All time</StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Running</StatLabel>
                <StatNumber color="blue.500">
                  {harvestJobs.filter((j) => j.status === 'running').length}
                </StatNumber>
                <StatHelpText>In progress</StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Records Added</StatLabel>
                <StatNumber color="green.500">
                  {harvestJobs.reduce((sum, j) => sum + j.recordsAdded, 0).toLocaleString()}
                </StatNumber>
                <StatHelpText>From all harvests</StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Records Processed</StatLabel>
                <StatNumber>
                  {harvestJobs.reduce((sum, j) => sum + j.recordsProcessed, 0).toLocaleString()}
                </StatNumber>
                <StatHelpText>Total scanned</StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>

        <Tabs variant="enclosed" colorScheme="brand">
          <TabList>
            <Tab>GBIF</Tab>
            <Tab>FishBase</Tab>
            <Tab>IUCN Red List</Tab>
            <Tab>Harvest History</Tab>
          </TabList>

          <TabPanels>
            {/* GBIF Tab */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <HStack justify="space-between">
                    <VStack align="start" spacing={1}>
                      <Heading size="md">GBIF Occurrence Harvest</Heading>
                      <Text fontSize="sm" color="gray.500">
                        Import occurrence records from the Global Biodiversity Information
                        Facility
                      </Text>
                    </VStack>
                    <Badge colorScheme="green" fontSize="sm">
                      API Available
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <Alert status="info" borderRadius="md">
                      <AlertIcon />
                      GBIF provides access to millions of biodiversity occurrence records
                      worldwide.
                    </Alert>

                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <FormControl>
                        <FormLabel>Scientific Name</FormLabel>
                        <Input
                          value={gbifQuery.scientificName}
                          onChange={(e) =>
                            setGbifQuery((prev) => ({
                              ...prev,
                              scientificName: e.target.value,
                            }))
                          }
                          placeholder="e.g., Labeo umbratus"
                        />
                        <FormHelperText>Species or genus name to search</FormHelperText>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Country</FormLabel>
                        <Select
                          value={gbifQuery.country}
                          onChange={(e) =>
                            setGbifQuery((prev) => ({ ...prev, country: e.target.value }))
                          }
                        >
                          <option value="ZA">South Africa</option>
                          <option value="BW">Botswana</option>
                          <option value="NA">Namibia</option>
                          <option value="ZW">Zimbabwe</option>
                          <option value="MZ">Mozambique</option>
                          <option value="">All Countries</option>
                        </Select>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Basis of Record</FormLabel>
                        <Select
                          value={gbifQuery.basisOfRecord}
                          onChange={(e) =>
                            setGbifQuery((prev) => ({
                              ...prev,
                              basisOfRecord: e.target.value,
                            }))
                          }
                        >
                          <option value="HUMAN_OBSERVATION">Human Observation</option>
                          <option value="PRESERVED_SPECIMEN">Preserved Specimen</option>
                          <option value="MACHINE_OBSERVATION">Machine Observation</option>
                          <option value="">All Types</option>
                        </Select>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Record Limit</FormLabel>
                        <Select
                          value={gbifQuery.limit.toString()}
                          onChange={(e) =>
                            setGbifQuery((prev) => ({
                              ...prev,
                              limit: parseInt(e.target.value),
                            }))
                          }
                        >
                          <option value="100">100 records</option>
                          <option value="500">500 records</option>
                          <option value="1000">1,000 records</option>
                          <option value="5000">5,000 records</option>
                          <option value="10000">10,000 records</option>
                        </Select>
                      </FormControl>
                    </SimpleGrid>

                    <Button
                      colorScheme="brand"
                      size="lg"
                      leftIcon={<DownloadIcon />}
                      onClick={startGBIFHarvest}
                      isLoading={isHarvesting}
                      loadingText="Starting harvest..."
                    >
                      Start GBIF Harvest
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* FishBase Tab */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <HStack justify="space-between">
                    <VStack align="start" spacing={1}>
                      <Heading size="md">FishBase Species Harvest</Heading>
                      <Text fontSize="sm" color="gray.500">
                        Import species information from FishBase
                      </Text>
                    </VStack>
                    <Badge colorScheme="green" fontSize="sm">
                      API Available
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <Alert status="info" borderRadius="md">
                      <AlertIcon />
                      FishBase is a global database of fish species information including
                      ecology, distribution, and conservation status.
                    </Alert>

                    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                      <FormControl>
                        <FormLabel>Family</FormLabel>
                        <Input
                          value={fishbaseQuery.family}
                          onChange={(e) =>
                            setFishbaseQuery((prev) => ({
                              ...prev,
                              family: e.target.value,
                            }))
                          }
                          placeholder="e.g., Cyprinidae"
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Genus</FormLabel>
                        <Input
                          value={fishbaseQuery.genus}
                          onChange={(e) =>
                            setFishbaseQuery((prev) => ({ ...prev, genus: e.target.value }))
                          }
                          placeholder="e.g., Labeo"
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Species</FormLabel>
                        <Input
                          value={fishbaseQuery.species}
                          onChange={(e) =>
                            setFishbaseQuery((prev) => ({
                              ...prev,
                              species: e.target.value,
                            }))
                          }
                          placeholder="e.g., umbratus"
                        />
                      </FormControl>
                    </SimpleGrid>

                    <Button colorScheme="brand" size="lg" leftIcon={<SearchIcon />}>
                      Search FishBase
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* IUCN Tab */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <HStack justify="space-between">
                    <VStack align="start" spacing={1}>
                      <Heading size="md">IUCN Red List Sync</Heading>
                      <Text fontSize="sm" color="gray.500">
                        Update conservation status from IUCN Red List
                      </Text>
                    </VStack>
                    <Badge colorScheme="yellow" fontSize="sm">
                      API Key Required
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <Alert status="warning" borderRadius="md">
                      <AlertIcon />
                      IUCN API requires an API token. Configure it in Settings before
                      harvesting.
                    </Alert>

                    <FormControl>
                      <FormLabel>IUCN API Token</FormLabel>
                      <Input type="password" placeholder="Enter your IUCN API token" />
                      <FormHelperText>
                        Get your token from{' '}
                        <Code>https://apiv3.iucnredlist.org/api/v3/token</Code>
                      </FormHelperText>
                    </FormControl>

                    <Button colorScheme="brand" size="lg" leftIcon={<RepeatIcon />}>
                      Sync Conservation Status
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Harvest History Tab */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">Harvest History</Heading>
                </CardHeader>
                <CardBody>
                  <Table variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Source</Th>
                        <Th>Type</Th>
                        <Th>Status</Th>
                        <Th isNumeric>Processed</Th>
                        <Th isNumeric>Added</Th>
                        <Th>Started</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {harvestJobs.map((job) => (
                        <Tr key={job.id}>
                          <Td fontWeight="medium">{job.source}</Td>
                          <Td>{job.type}</Td>
                          <Td>
                            <HStack>
                              <Icon
                                as={getStatusIcon(job.status)}
                                color={`${getStatusColor(job.status)}.500`}
                              />
                              <Badge colorScheme={getStatusColor(job.status)}>
                                {job.status}
                              </Badge>
                              {job.status === 'running' && (
                                <Progress
                                  value={job.progress}
                                  size="sm"
                                  colorScheme="blue"
                                  width="60px"
                                  borderRadius="full"
                                />
                              )}
                            </HStack>
                          </Td>
                          <Td isNumeric>{job.recordsProcessed.toLocaleString()}</Td>
                          <Td isNumeric>{job.recordsAdded.toLocaleString()}</Td>
                          <Td>{new Date(job.startedAt).toLocaleString()}</Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </CardBody>
              </Card>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Container>
    </Box>
  );
};

export default HarvestPage;
