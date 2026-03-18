/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Landing page for BIMS.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
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
} from '@chakra-ui/react';
import {
  SearchIcon,
  ViewIcon,
  DownloadIcon,
  AddIcon,
  InfoIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink } from 'react-router-dom';

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
  value: string;
  helpText: string;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, helpText, color }) => {
  const cardBg = useColorModeValue('white', 'gray.700');

  return (
    <Card bg={cardBg} shadow="sm">
      <CardBody>
        <Stat>
          <StatLabel color="gray.500">{label}</StatLabel>
          <StatNumber color={color} fontSize="3xl">
            {value}
          </StatNumber>
          <StatHelpText>{helpText}</StatHelpText>
        </Stat>
      </CardBody>
    </Card>
  );
};

const LandingPage: React.FC = () => {
  const heroBg = useColorModeValue('brand.500', 'brand.600');

  return (
    <Box>
      {/* Hero Section */}
      <Box bg={heroBg} color="white" py={{ base: 16, md: 24 }}>
        <Container maxW="container.xl">
          <VStack spacing={6} textAlign="center" maxW="3xl" mx="auto">
            <Badge colorScheme="whiteAlpha" fontSize="sm" px={3} py={1} rounded="full">
              Open Source Biodiversity Platform
            </Badge>
            <Heading size={{ base: 'xl', md: '2xl' }} fontWeight="bold">
              Biodiversity Information Management System
            </Heading>
            <Text fontSize={{ base: 'md', md: 'lg' }} opacity={0.9} maxW="2xl">
              Explore, analyze, and manage biodiversity data across South Africa.
              Access comprehensive records of species, habitats, and conservation status.
            </Text>
            <HStack spacing={4} pt={4}>
              <Button
                as={RouterLink}
                to="/map"
                size="lg"
                bg="white"
                color="brand.500"
                _hover={{ bg: 'gray.100' }}
                leftIcon={<SearchIcon />}
              >
                Explore Map
              </Button>
              <Button
                as="a"
                href="/accounts/signup/"
                size="lg"
                variant="outline"
                borderColor="white"
                color="white"
                _hover={{ bg: 'whiteAlpha.200' }}
              >
                Get Started
              </Button>
            </HStack>
          </VStack>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxW="container.xl" mt={-10}>
        <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
          <StatCard
            label="Location Sites"
            value="15,000+"
            helpText="Monitoring sites"
            color="brand.500"
          />
          <StatCard
            label="Species Records"
            value="500,000+"
            helpText="Occurrence records"
            color="green.500"
          />
          <StatCard
            label="Taxa"
            value="10,000+"
            helpText="Species catalogued"
            color="purple.500"
          />
          <StatCard
            label="Contributors"
            value="500+"
            helpText="Active researchers"
            color="orange.500"
          />
        </SimpleGrid>
      </Container>

      {/* Features Section */}
      <Container maxW="container.xl" py={16}>
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
              description="Upload your field observations and contribute to South Africa's biodiversity knowledge base."
              linkHref="/upload/"
              linkText="Upload Data"
            />
            <FeatureCard
              icon={DownloadIcon}
              title="Download & Export"
              description="Export filtered datasets in various formats for your research and conservation projects."
              linkHref="/download-request/"
              linkText="Request Download"
            />
          </SimpleGrid>
        </VStack>
      </Container>

      {/* Ecosystem Types Section */}
      <Box bg="gray.50" py={16}>
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

      {/* CTA Section */}
      <Container maxW="container.xl" py={16}>
        <Card bg="brand.500" color="white">
          <CardBody py={10}>
            <VStack spacing={6} textAlign="center">
              <Heading size="lg">Ready to Explore?</Heading>
              <Text maxW="xl" opacity={0.9}>
                Start exploring South Africa's biodiversity data today.
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
                  as="a"
                  href="/links/"
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
    </Box>
  );
};

export default LandingPage;
