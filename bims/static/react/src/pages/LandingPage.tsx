/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Landing page for BIMS.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  SimpleGrid,
  VStack,
  HStack,
  Icon,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
  Flex,
  Badge,
  Skeleton,
  Image,
} from '@chakra-ui/react';
import {
  SearchIcon,
  ViewIcon,
  DownloadIcon,
  AddIcon,
  InfoIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink } from 'react-router-dom';
import { apiClient, moduleSummaryApi, ModuleSummary } from '../api/client';
import { ModuleSummaryDonut, ConservationStatusData } from '../components/charts';
import { useDashboardSettingsStore } from '../stores/dashboardSettingsStore';

interface PlatformStats {
  total_sites: number;
  total_records: number;
  total_taxa: number;
  total_contributors: number;
}

interface ModuleCardData {
  name: string;
  slug: string;
  icon?: string;
  total: number;
  total_site: number;
  total_site_visit?: number;
  total_validated: number;
  total_sass?: number;
  color: string;
  bgColor: string;
  conservationStatus?: ConservationStatusData;
}

interface FeatureCardProps {
  icon: React.ElementType;
  title: string;
  description: string;
  linkTo?: string;
  linkHref?: string;
  linkText: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  description,
  linkTo,
  linkHref,
  linkText,
}) => {
  const cardBg = useColorModeValue('white', 'gray.700');

  return (
    <Card bg={cardBg} shadow="md" _hover={{ shadow: 'lg', transform: 'translateY(-2px)' }} transition="all 0.2s">
      <CardBody>
        <VStack align="start" spacing={4}>
          <Flex
            w={12}
            h={12}
            align="center"
            justify="center"
            rounded="xl"
            bg="brand.50"
            color="brand.500"
          >
            <Icon as={icon} boxSize={6} />
          </Flex>
          <Heading size="md">{title}</Heading>
          <Text color="gray.600" fontSize="sm">
            {description}
          </Text>
          {linkTo ? (
            <Button as={RouterLink} to={linkTo} variant="link" colorScheme="brand" size="sm">
              {linkText} &rarr;
            </Button>
          ) : (
            <Button as="a" href={linkHref} variant="link" colorScheme="brand" size="sm">
              {linkText} &rarr;
            </Button>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};

interface StatCardProps {
  label: string;
  value: string | number;
  helpText: string;
  color: string;
  isLoading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, helpText, color, isLoading = false }) => {
  const cardBg = useColorModeValue('white', 'gray.700');

  // Format number with locale string for thousands separator
  const formattedValue = typeof value === 'number' ? value.toLocaleString() : value;

  return (
    <Card bg={cardBg} shadow="sm">
      <CardBody>
        <Stat>
          <StatLabel color="gray.500">{label}</StatLabel>
          {isLoading ? (
            <Skeleton height="36px" width="80px" my={1} />
          ) : (
            <StatNumber color={color} fontSize="3xl">
              {formattedValue}
            </StatNumber>
          )}
          <StatHelpText>{helpText}</StatHelpText>
        </Stat>
      </CardBody>
    </Card>
  );
};

// Default colors for taxon groups
const MODULE_COLORS: Record<string, { color: string; bgColor: string }> = {
  fish: { color: 'blue.600', bgColor: 'blue.50' },
  invertebrates: { color: 'orange.600', bgColor: 'orange.50' },
  algae: { color: 'green.600', bgColor: 'green.50' },
  default: { color: 'purple.600', bgColor: 'purple.50' },
};

const LandingPage: React.FC = () => {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [modules, setModules] = useState<ModuleCardData[]>([]);
  const [isLoadingModules, setIsLoadingModules] = useState(true);

  // Get settings from the dashboard settings store
  const { branding, landingPage: landingPageSettings } = useDashboardSettingsStore();

  // Landing page section visibility - controlled directly by toggles
  const showStatsSection = landingPageSettings.showStats;
  const showEcosystemsSection = landingPageSettings.showEcosystems;
  const showTaxonGroups = true; // Always show taxon groups in hero

  // Fetch platform stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiClient.get<{ data: PlatformStats }>('platform/stats/');
        setStats(response.data?.data || null);
      } catch (error) {
        console.error('Failed to fetch platform stats:', error);
        setStats({
          total_sites: 0,
          total_records: 0,
          total_taxa: 0,
          total_contributors: 0,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Fetch module summary data with polling support
  useEffect(() => {
    let pollCount = 0;
    const maxPolls = 60; // Poll for up to 60 seconds
    let pollTimeout: ReturnType<typeof setTimeout> | null = null;

    const fetchModules = async () => {
      try {
        const data = await moduleSummaryApi.getSummary();

        // If still processing, poll again after 1 second
        if (data.status === 'processing') {
          pollCount++;
          if (pollCount < maxPolls) {
            pollTimeout = setTimeout(fetchModules, 1000);
            return;
          } else {
            // Timeout - show fallback
            console.log('[LandingPage] Module summary generation timed out');
            setIsLoadingModules(false);
            return;
          }
        }

        // Data is ready - extract module data
        const moduleCards: ModuleCardData[] = [];
        for (const [key, value] of Object.entries(data || {})) {
          if (key === 'general_summary' || key === 'status' || key === 'message') continue;
          if (typeof value === 'object' && value !== null && 'total' in value) {
            const moduleData = value as ModuleSummary;
            const slug = key.toLowerCase().replace(/\s+/g, '-');
            const colors = MODULE_COLORS[slug] || MODULE_COLORS.default;

            moduleCards.push({
              name: key,
              slug,
              icon: moduleData.icon,
              total: moduleData.total || 0,
              total_site: moduleData.total_site || 0,
              total_site_visit: moduleData.total_site_visit || 0,
              total_validated: moduleData.total_validated || 0,
              total_sass: (moduleData as any).total_sass || 0,
              color: colors.color,
              bgColor: colors.bgColor,
              conservationStatus: moduleData['conservation-status'],
            });
          }
        }

        setModules(moduleCards);
        setIsLoadingModules(false);
      } catch (error) {
        console.error('[LandingPage] Failed to fetch module summary:', error);
        setIsLoadingModules(false);
      }
    };

    fetchModules();

    // Cleanup polling on unmount
    return () => {
      if (pollTimeout) clearTimeout(pollTimeout);
    };
  }, []);

  return (
    <Box h="100%" overflowY="auto">
      {/* Hero Section - Full viewport with fixed background */}
      <Box
        position="relative"
        minH="100vh"
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        overflow="hidden"
      >
        {/* Fixed background image */}
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          backgroundImage={`url(${branding.bannerImage})`}
          backgroundSize="cover"
          backgroundPosition="center"
          backgroundAttachment={{ base: 'scroll', md: 'fixed' }}
          zIndex={0}
        />

        {/* Gradient overlay for depth */}
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bgGradient="linear(to-b, blackAlpha.400 0%, blackAlpha.600 50%, blackAlpha.800 100%)"
          zIndex={1}
        />

        {/* Hero Content with glassmorphism backdrop */}
        <Container maxW="container.lg" position="relative" zIndex={2} py={20}>
          <Box
            bg="blackAlpha.600"
            backdropFilter="blur(12px)"
            borderRadius="2xl"
            border="1px solid"
            borderColor="whiteAlpha.200"
            p={{ base: 8, md: 12 }}
            boxShadow="0 8px 32px rgba(0, 0, 0, 0.3)"
          >
            <VStack spacing={6} textAlign="center" color="white">
              <Badge
                colorScheme="green"
                fontSize="sm"
                px={4}
                py={1.5}
                rounded="full"
                textTransform="uppercase"
                letterSpacing="wider"
                fontWeight="semibold"
              >
                Open Source Biodiversity Platform
              </Badge>
              <Heading
                size={{ base: 'xl', md: '2xl', lg: '3xl' }}
                fontWeight="bold"
                lineHeight="shorter"
                color="white"
              >
                {landingPageSettings.heroTitle}
              </Heading>
              <Text
                fontSize={{ base: 'md', md: 'lg' }}
                opacity={0.9}
                maxW="2xl"
                lineHeight="tall"
              >
                {landingPageSettings.heroSubtitle}
              </Text>
              <HStack spacing={4} pt={4} flexWrap="wrap" justify="center">
                <Button
                  as={RouterLink}
                  to={landingPageSettings.ctaButtonUrl}
                  size="lg"
                  colorScheme="brand"
                  leftIcon={<SearchIcon />}
                  px={8}
                  _hover={{ transform: 'translateY(-2px)', boxShadow: 'lg' }}
                  transition="all 0.2s"
                >
                  {landingPageSettings.ctaButtonText}
                </Button>
                <Button
                  as={RouterLink}
                  to="/register"
                  size="lg"
                  variant="outline"
                  borderColor="white"
                  color="white"
                  borderWidth={2}
                  px={8}
                  _hover={{ bg: 'whiteAlpha.200', transform: 'translateY(-2px)' }}
                  transition="all 0.2s"
                >
                  Get Started
                </Button>
              </HStack>

              {/* Module Summary Donut Charts in Hero */}
              {showTaxonGroups && (
                <Box pt={8} w="100%">
                  {isLoadingModules ? (
                    <Flex justify="center" wrap="wrap" gap={6}>
                      {[1, 2, 3, 4].map((i) => (
                        <Box key={i} textAlign="center">
                          <Skeleton borderRadius="full" w="120px" h="120px" mx="auto" mb={3} />
                          <Skeleton height="20px" width="80px" mx="auto" mb={2} />
                          <Skeleton height="14px" width="60px" mx="auto" />
                        </Box>
                      ))}
                    </Flex>
                  ) : modules.length > 0 ? (
                    <Flex justify="center" wrap="wrap" gap={6}>
                      {modules.map((module, index) => (
                        <Box
                          key={module.slug}
                          as={RouterLink}
                          to={`/map?taxon_group=${module.slug}`}
                          _hover={{ textDecoration: 'none', transform: 'scale(1.05)' }}
                          transition="transform 0.2s"
                        >
                          <ModuleSummaryDonut
                            name={module.name}
                            icon={module.icon}
                            total={module.total}
                            totalSite={module.total_site}
                            totalSiteVisit={module.total_site_visit}
                            totalSass={module.total_sass}
                            conservationStatus={module.conservationStatus}
                            delay={index * 100}
                          />
                        </Box>
                      ))}
                    </Flex>
                  ) : null}
                </Box>
              )}
            </VStack>
          </Box>
        </Container>

        {/* Scroll indicator */}
        <Box
          position="absolute"
          bottom={8}
          left="50%"
          transform="translateX(-50%)"
          zIndex={2}
          color="white"
          opacity={0.7}
          animation="bounce 2s infinite"
          sx={{
            '@keyframes bounce': {
              '0%, 20%, 50%, 80%, 100%': { transform: 'translateX(-50%) translateY(0)' },
              '40%': { transform: 'translateX(-50%) translateY(-10px)' },
              '60%': { transform: 'translateX(-50%) translateY(-5px)' },
            },
          }}
        >
          <VStack spacing={1}>
            <Text fontSize="xs" textTransform="uppercase" letterSpacing="wider">
              Scroll to explore
            </Text>
            <Box
              w={6}
              h={10}
              border="2px solid"
              borderColor="currentColor"
              borderRadius="full"
              position="relative"
            >
              <Box
                position="absolute"
                top={2}
                left="50%"
                transform="translateX(-50%)"
                w={1.5}
                h={3}
                bg="currentColor"
                borderRadius="full"
                animation="scrollDown 1.5s infinite"
                sx={{
                  '@keyframes scrollDown': {
                    '0%': { opacity: 1, top: '8px' },
                    '100%': { opacity: 0, top: '20px' },
                  },
                }}
              />
            </Box>
          </VStack>
        </Box>
      </Box>

      {/* Stats Section - overlapping the transition */}
      {showStatsSection && (
        <Box bg="gray.50" position="relative" mt={-20} pt={24} pb={8}>
          <Container maxW="container.xl">
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
              <StatCard
                label="Location Sites"
                value={stats?.total_sites ?? 0}
                helpText="Monitoring sites"
                color="brand.500"
                isLoading={isLoading}
              />
              <StatCard
                label="Species Records"
                value={stats?.total_records ?? 0}
                helpText="Occurrence records"
                color="green.500"
                isLoading={isLoading}
              />
              <StatCard
                label="Taxa"
                value={stats?.total_taxa ?? 0}
                helpText="Species catalogued"
                color="purple.500"
                isLoading={isLoading}
              />
              <StatCard
                label="Contributors"
                value={stats?.total_contributors ?? 0}
                helpText="Active researchers"
                color="orange.500"
                isLoading={isLoading}
              />
            </SimpleGrid>
          </Container>
        </Box>
      )}

      {/* Features Section */}
      <Box bg="gray.50" pb={16} pt={showStatsSection ? 0 : 16}>
        <Container maxW="container.xl">
          <VStack spacing={12}>
            <VStack spacing={4} textAlign="center">
              <Heading size="lg">What You Can Do</Heading>
              <Text color="gray.600" maxW="2xl">
                BIMS provides powerful tools for biodiversity data management,
                analysis, and visualization.
              </Text>
            </VStack>

          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} w="100%">
            <FeatureCard
              icon={SearchIcon}
              title="Search & Explore"
              description="Search through thousands of biodiversity records using advanced filters for species, locations, and dates."
              linkTo="/map"
              linkText="Open Map"
            />
            <FeatureCard
              icon={ViewIcon}
              title="Visualize Data"
              description="View interactive maps, charts, and dashboards showing species distributions and conservation status."
              linkTo="/map"
              linkText="View Dashboard"
            />
            <FeatureCard
              icon={AddIcon}
              title="Contribute Data"
              description="Upload your field observations and contribute to the biodiversity knowledge base."
              linkTo="/upload"
              linkText="Upload Data"
            />
            <FeatureCard
              icon={DownloadIcon}
              title="Download & Export"
              description="Export filtered datasets in various formats for your research and conservation projects."
              linkTo="/downloads"
              linkText="Request Download"
            />
          </SimpleGrid>
        </VStack>
      </Container>
      </Box>

      {/* Ecosystem Types Section */}
      {showEcosystemsSection && (
        <Box bg="white" py={16}>
          <Container maxW="container.xl">
            <VStack spacing={8}>
              <VStack spacing={4} textAlign="center">
                <Heading size="lg">Ecosystems Covered</Heading>
                <Text color="gray.600">
                  Monitor and protect diverse freshwater ecosystems across the region
                </Text>
              </VStack>

              <SimpleGrid columns={{ base: 2, md: 3, lg: 5 }} spacing={4}>
                {[
                  { name: 'Rivers', color: 'blue.500', icon: '🏞️' },
                  { name: 'Wetlands', color: 'green.500', icon: '🌿' },
                  { name: 'Estuaries', color: 'teal.500', icon: '🌊' },
                  { name: 'Dams', color: 'cyan.500', icon: '💧' },
                  { name: 'Lakes', color: 'blue.400', icon: '🏔️' },
                ].map((ecosystem) => (
                  <Card key={ecosystem.name} bg="white" textAlign="center">
                    <CardBody>
                      <VStack>
                        <Text fontSize="3xl">{ecosystem.icon}</Text>
                        <Text fontWeight="600" color={ecosystem.color}>
                          {ecosystem.name}
                        </Text>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </VStack>
          </Container>
        </Box>
      )}

      {/* CTA Section */}
      <Container maxW="container.xl" py={16}>
        <Card bg="brand.500" color="white">
          <CardBody py={10}>
            <VStack spacing={6} textAlign="center">
              <Heading size="lg">Ready to Explore?</Heading>
              <Text maxW="xl" opacity={0.9}>
                Start exploring biodiversity data today.
                Search locations, discover species, and contribute to conservation.
              </Text>
              <HStack spacing={4}>
                <Button
                  as={RouterLink}
                  to="/map"
                  size="lg"
                  bg="white"
                  color="brand.500"
                  _hover={{ bg: 'gray.100' }}
                >
                  Open Interactive Map
                </Button>
                <Button
                  as={RouterLink}
                  to="/about"
                  size="lg"
                  variant="outline"
                  borderColor="white"
                  color="white"
                  _hover={{ bg: 'whiteAlpha.200' }}
                  leftIcon={<InfoIcon />}
                >
                  Learn More
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </Container>

      {/* Institutional Instance CTA Section */}
      <Box
        bg="gray.900"
        color="white"
        py={20}
        position="relative"
        overflow="hidden"
      >
        {/* Background pattern */}
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          opacity={0.1}
          bgImage="radial-gradient(circle at 25% 25%, brand.500 1px, transparent 1px), radial-gradient(circle at 75% 75%, brand.500 1px, transparent 1px)"
          bgSize="50px 50px"
        />

        <Container maxW="container.xl" position="relative" zIndex={1}>
          <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={12} alignItems="center">
            {/* Left side - Text content */}
            <VStack align={{ base: 'center', lg: 'start' }} spacing={6} textAlign={{ base: 'center', lg: 'left' }}>
              <Badge colorScheme="brand" fontSize="md" px={4} py={1}>
                For Institutions
              </Badge>
              <Heading size="xl" lineHeight="shorter">
                Create Your Own BIMS Instance
              </Heading>
              <Text fontSize="lg" opacity={0.9} maxW="lg">
                Get a dedicated biodiversity data platform for your institution with your
                branding, subdomain, and complete control over your data. Join leading
                research organizations and conservation agencies using BIMS.
              </Text>
              <SimpleGrid columns={3} spacing={4} w="100%">
                <VStack align={{ base: 'center', lg: 'start' }} spacing={1}>
                  <Text fontSize="3xl" fontWeight="bold" color="brand.400">
                    EUR 600
                  </Text>
                  <Text fontSize="sm" opacity={0.8}>
                    per month
                  </Text>
                </VStack>
                <VStack align={{ base: 'center', lg: 'start' }} spacing={1}>
                  <Text fontSize="3xl" fontWeight="bold" color="brand.400">
                    10h
                  </Text>
                  <Text fontSize="sm" opacity={0.8}>
                    onboarding included
                  </Text>
                </VStack>
                <VStack align={{ base: 'center', lg: 'start' }} spacing={1}>
                  <Text fontSize="3xl" fontWeight="bold" color="brand.400">
                    48h
                  </Text>
                  <Text fontSize="sm" opacity={0.8}>
                    setup time
                  </Text>
                </VStack>
              </SimpleGrid>
              <HStack spacing={4} pt={4}>
                <Button
                  as={RouterLink}
                  to="/institutional-signup"
                  size="lg"
                  colorScheme="brand"
                  px={8}
                  _hover={{ transform: 'translateY(-2px)', boxShadow: 'xl' }}
                  transition="all 0.2s"
                >
                  Get Started
                </Button>
                <Button
                  as={RouterLink}
                  to="/institutional-signup#signup-form"
                  size="lg"
                  variant="outline"
                  borderColor="white"
                  color="white"
                  px={8}
                  _hover={{ bg: 'whiteAlpha.200' }}
                >
                  Contact Us
                </Button>
              </HStack>
            </VStack>

            {/* Right side - Feature highlights */}
            <VStack spacing={4} align="stretch">
              {[
                { title: 'Dedicated Platform', desc: 'Your own domain or subdomain with custom branding' },
                { title: 'Fully Managed', desc: 'We handle hosting, backups, and security updates' },
                { title: 'GBIF Integration', desc: 'Publish your data to global biodiversity networks' },
                { title: 'Expert Support', desc: 'Access to biologist advice and technical consulting' },
                { title: 'Sustainability', desc: 'Your subscription supports ongoing BIMS development' },
              ].map((feature, index) => (
                <HStack
                  key={index}
                  bg="whiteAlpha.100"
                  p={4}
                  borderRadius="lg"
                  _hover={{ bg: 'whiteAlpha.200' }}
                  transition="all 0.2s"
                >
                  <Flex
                    w={8}
                    h={8}
                    bg="brand.500"
                    borderRadius="full"
                    align="center"
                    justify="center"
                    flexShrink={0}
                  >
                    <Icon as={ViewIcon} boxSize={4} />
                  </Flex>
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="semibold">{feature.title}</Text>
                    <Text fontSize="sm" opacity={0.8}>{feature.desc}</Text>
                  </VStack>
                </HStack>
              ))}
            </VStack>
          </SimpleGrid>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;
