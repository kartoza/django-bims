/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Analytics Dashboard - Real-time biodiversity metrics and visualizations.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect } from 'react';
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
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Select,
  Spinner,
  Center,
  useColorModeValue,
  Badge,
  Progress,
  Flex,
  Spacer,
  Icon,
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
} from '@chakra-ui/react';
import {
  FiMapPin,
  FiUsers,
  FiDatabase,
  FiTrendingUp,
  FiGlobe,
  FiCalendar,
} from 'react-icons/fi';
import { apiClient } from '../api/client';

interface DashboardStats {
  totalSites: number;
  totalRecords: number;
  totalTaxa: number;
  totalSurveys: number;
  totalUsers: number;
  validatedRecords: number;
  pendingRecords: number;
  recordsThisMonth: number;
  recordsLastMonth: number;
}

interface TaxonGroupStats {
  name: string;
  count: number;
  percentage: number;
  color: string;
}

interface RecentActivity {
  id: number;
  type: 'record' | 'site' | 'survey';
  description: string;
  user: string;
  timestamp: string;
}

interface TopContributor {
  rank: number;
  username: string;
  recordCount: number;
  siteCount: number;
}

const AnalyticsDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [taxonGroups, setTaxonGroups] = useState<TaxonGroupStats[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [topContributors, setTopContributors] = useState<TopContributor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('month');

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const headerBg = useColorModeValue('brand.500', 'brand.600');

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboard = async () => {
      setIsLoading(true);
      try {
        // Fetch summary stats
        const [sitesRes, recordsRes, taxaRes, surveysRes] = await Promise.all([
          apiClient.get('sites/summary/').catch(() => ({ data: { data: {} } })),
          apiClient.get('records/summary/').catch(() => ({ data: { data: {} } })),
          apiClient.get('taxa/').catch(() => ({ data: { data: [], count: 0 } })),
          apiClient.get('surveys/', { params: { page_size: 1 } }).catch(() => ({ data: { count: 0 } })),
        ]);

        const siteData = sitesRes.data?.data || {};
        const recordData = recordsRes.data?.data || {};

        setStats({
          totalSites: siteData.total_sites || 0,
          totalRecords: recordData.total_records || 0,
          totalTaxa: recordData.species_count || 0,
          totalSurveys: surveysRes.data?.count || 0,
          totalUsers: 0, // Would need user stats endpoint
          validatedRecords: recordData.validated_records || 0,
          pendingRecords: recordData.pending_records || 0,
          recordsThisMonth: 0, // Would need temporal stats
          recordsLastMonth: 0,
        });

        // Mock taxon group data (would come from API)
        setTaxonGroups([
          { name: 'Fish', count: 4500, percentage: 35, color: 'blue.500' },
          { name: 'Invertebrates', count: 5200, percentage: 40, color: 'green.500' },
          { name: 'Algae', count: 2100, percentage: 16, color: 'teal.500' },
          { name: 'Other', count: 1200, percentage: 9, color: 'gray.500' },
        ]);

        // Mock recent activity
        setRecentActivity([
          { id: 1, type: 'record', description: 'Added 15 fish records at Orange River', user: 'jsmith', timestamp: '2024-01-15T10:30:00Z' },
          { id: 2, type: 'site', description: 'New monitoring site created', user: 'mwilliams', timestamp: '2024-01-15T09:45:00Z' },
          { id: 3, type: 'survey', description: 'Survey completed at Berg River', user: 'kthomas', timestamp: '2024-01-15T08:20:00Z' },
          { id: 4, type: 'record', description: 'Validated 42 invertebrate records', user: 'admin', timestamp: '2024-01-14T16:30:00Z' },
          { id: 5, type: 'site', description: 'Site location updated', user: 'jsmith', timestamp: '2024-01-14T14:15:00Z' },
        ]);

        // Mock top contributors
        setTopContributors([
          { rank: 1, username: 'jsmith', recordCount: 2450, siteCount: 45 },
          { rank: 2, username: 'mwilliams', recordCount: 1890, siteCount: 32 },
          { rank: 3, username: 'kthomas', recordCount: 1650, siteCount: 28 },
          { rank: 4, username: 'ajonas', recordCount: 1420, siteCount: 25 },
          { rank: 5, username: 'psmith', recordCount: 1180, siteCount: 22 },
        ]);

      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboard();
  }, [timeRange]);

  if (isLoading) {
    return (
      <Center h="calc(100vh - 140px)">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  const growthRate = stats && stats.recordsLastMonth > 0
    ? ((stats.recordsThisMonth - stats.recordsLastMonth) / stats.recordsLastMonth * 100).toFixed(1)
    : '0';

  return (
    <Box bg={bgColor} minH="calc(100vh - 100px)">
      {/* Header */}
      <Box bg={headerBg} color="white" py={6}>
        <Container maxW="container.xl">
          <Flex align="center">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Analytics Dashboard</Heading>
              <Text opacity={0.9}>
                Real-time biodiversity data insights
              </Text>
            </VStack>
            <Spacer />
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              w="180px"
              bg="whiteAlpha.200"
              border="none"
              color="white"
              _focus={{ bg: 'whiteAlpha.300' }}
            >
              <option value="week" style={{ color: 'black' }}>Last 7 days</option>
              <option value="month" style={{ color: 'black' }}>Last 30 days</option>
              <option value="quarter" style={{ color: 'black' }}>Last 90 days</option>
              <option value="year" style={{ color: 'black' }}>Last year</option>
              <option value="all" style={{ color: 'black' }}>All time</option>
            </Select>
          </Flex>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        {/* Key Metrics */}
        <SimpleGrid columns={{ base: 2, md: 3, lg: 6 }} spacing={4} mb={8}>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <HStack mb={2}>
                  <Icon as={FiMapPin} color="brand.500" />
                  <StatLabel>Sites</StatLabel>
                </HStack>
                <StatNumber>{stats?.totalSites.toLocaleString()}</StatNumber>
                <StatHelpText>Monitoring locations</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <HStack mb={2}>
                  <Icon as={FiDatabase} color="green.500" />
                  <StatLabel>Records</StatLabel>
                </HStack>
                <StatNumber>{stats?.totalRecords.toLocaleString()}</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  {growthRate}% this month
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <HStack mb={2}>
                  <Icon as={FiGlobe} color="purple.500" />
                  <StatLabel>Taxa</StatLabel>
                </HStack>
                <StatNumber>{stats?.totalTaxa.toLocaleString()}</StatNumber>
                <StatHelpText>Species recorded</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <HStack mb={2}>
                  <Icon as={FiCalendar} color="orange.500" />
                  <StatLabel>Surveys</StatLabel>
                </HStack>
                <StatNumber>{stats?.totalSurveys.toLocaleString()}</StatNumber>
                <StatHelpText>Site visits</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <HStack mb={2}>
                  <Icon as={FiTrendingUp} color="teal.500" />
                  <StatLabel>Validated</StatLabel>
                </HStack>
                <StatNumber>{stats?.validatedRecords.toLocaleString()}</StatNumber>
                <StatHelpText>
                  {stats && stats.totalRecords > 0
                    ? `${((stats.validatedRecords / stats.totalRecords) * 100).toFixed(0)}% of total`
                    : '0%'}
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <HStack mb={2}>
                  <Icon as={FiUsers} color="pink.500" />
                  <StatLabel>Pending</StatLabel>
                </HStack>
                <StatNumber color="orange.500">{stats?.pendingRecords.toLocaleString()}</StatNumber>
                <StatHelpText>Awaiting validation</StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>

        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={8} mb={8}>
          {/* Taxon Group Distribution */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Records by Taxon Group</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                {taxonGroups.map((group) => (
                  <Box key={group.name}>
                    <Flex mb={1}>
                      <Text fontWeight="medium">{group.name}</Text>
                      <Spacer />
                      <Text color="gray.500">
                        {group.count.toLocaleString()} ({group.percentage}%)
                      </Text>
                    </Flex>
                    <Progress
                      value={group.percentage}
                      colorScheme={group.color.split('.')[0]}
                      borderRadius="full"
                      size="sm"
                    />
                  </Box>
                ))}
              </VStack>
            </CardBody>
          </Card>

          {/* Top Contributors */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Top Contributors</Heading>
            </CardHeader>
            <CardBody>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>#</Th>
                    <Th>User</Th>
                    <Th isNumeric>Records</Th>
                    <Th isNumeric>Sites</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {topContributors.map((contributor) => (
                    <Tr key={contributor.rank}>
                      <Td>
                        <Badge
                          colorScheme={
                            contributor.rank === 1
                              ? 'yellow'
                              : contributor.rank === 2
                              ? 'gray'
                              : contributor.rank === 3
                              ? 'orange'
                              : 'blue'
                          }
                        >
                          {contributor.rank}
                        </Badge>
                      </Td>
                      <Td fontWeight="medium">@{contributor.username}</Td>
                      <Td isNumeric>{contributor.recordCount.toLocaleString()}</Td>
                      <Td isNumeric>{contributor.siteCount}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Recent Activity */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Recent Activity</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {recentActivity.map((activity) => (
                <HStack key={activity.id} p={3} bg={bgColor} borderRadius="md">
                  <Badge
                    colorScheme={
                      activity.type === 'record'
                        ? 'green'
                        : activity.type === 'site'
                        ? 'blue'
                        : 'purple'
                    }
                  >
                    {activity.type}
                  </Badge>
                  <Text flex={1}>{activity.description}</Text>
                  <Text color="gray.500" fontSize="sm">
                    @{activity.user}
                  </Text>
                  <Text color="gray.400" fontSize="sm">
                    {new Date(activity.timestamp).toLocaleString()}
                  </Text>
                </HStack>
              ))}
            </VStack>
          </CardBody>
        </Card>
      </Container>
    </Box>
  );
};

export default AnalyticsDashboardPage;
