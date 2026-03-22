/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * About BIMS page.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardBody,
  SimpleGrid,
  Image,
  Link,
  Button,
  Divider,
  List,
  ListItem,
  ListIcon,
  Icon,
} from '@chakra-ui/react';
import {
  CheckCircleIcon,
  ExternalLinkIcon,
  StarIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink } from 'react-router-dom';

const AboutPage: React.FC = () => {
  const features = [
    'Interactive map-based data exploration',
    'Advanced search and filtering capabilities',
    'Species occurrence tracking',
    'Conservation status monitoring',
    'Multi-tenant architecture',
    'Data upload and validation workflows',
    'Integration with GBIF',
    'Custom dashboards and analytics',
  ];

  const partners = [
    { name: 'Kartoza', url: 'https://kartoza.com', role: 'Development Partner' },
    { name: 'FRCSA', url: 'https://www.frcsa.org.za/', role: 'Funding Partner' },
    { name: 'SANBI', url: 'https://www.sanbi.org', role: 'Data Partner' },
    { name: 'FBIS', url: 'https://freshwaterbiodiversity.org', role: 'Freshwater Biodiversity' },
  ];

  return (
    <Container maxW="container.lg" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Hero */}
        <Box textAlign="center" py={8}>
          <Heading size="2xl" mb={4}>
            About BIMS
          </Heading>
          <Text fontSize="lg" color="gray.600" maxW="2xl" mx="auto">
            The Biodiversity Information Management System (BIMS) is an open-source
            platform for managing, analyzing, and sharing biodiversity data.
          </Text>
        </Box>

        {/* Mission */}
        <Card>
          <CardBody>
            <Heading size="md" mb={4}>
              Our Mission
            </Heading>
            <Text color="gray.700">
              BIMS aims to support biodiversity conservation by providing researchers,
              conservation managers, and citizen scientists with powerful tools to
              collect, manage, and analyze species occurrence data. The platform
              focuses on freshwater ecosystems but can be configured for any
              taxonomic group or ecosystem type.
            </Text>
          </CardBody>
        </Card>

        {/* Features */}
        <Card>
          <CardBody>
            <Heading size="md" mb={4}>
              Key Features
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
              {features.map((feature, idx) => (
                <HStack key={idx} align="start">
                  <ListIcon as={CheckCircleIcon} color="green.500" mt={1} />
                  <Text>{feature}</Text>
                </HStack>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* Technology */}
        <Card>
          <CardBody>
            <Heading size="md" mb={4}>
              Technology Stack
            </Heading>
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
              <VStack>
                <Text fontWeight="600" color="brand.500">
                  Backend
                </Text>
                <Text fontSize="sm">Django + PostgreSQL</Text>
              </VStack>
              <VStack>
                <Text fontWeight="600" color="brand.500">
                  Frontend
                </Text>
                <Text fontSize="sm">React + TypeScript</Text>
              </VStack>
              <VStack>
                <Text fontWeight="600" color="brand.500">
                  Mapping
                </Text>
                <Text fontSize="sm">MapLibre GL JS</Text>
              </VStack>
              <VStack>
                <Text fontWeight="600" color="brand.500">
                  API
                </Text>
                <Text fontSize="sm">Django REST Framework</Text>
              </VStack>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* Partners */}
        <Card>
          <CardBody>
            <Heading size="md" mb={4}>
              Partners & Contributors
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
              {partners.map((partner) => (
                <Card key={partner.name} variant="outline">
                  <CardBody textAlign="center">
                    <Link href={partner.url} isExternal fontWeight="600" color="brand.500">
                      {partner.name} <ExternalLinkIcon mx={1} />
                    </Link>
                    <Text fontSize="sm" color="gray.500">
                      {partner.role}
                    </Text>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* Open Source */}
        <Card bg="brand.500" color="white">
          <CardBody textAlign="center" py={8}>
            <Icon as={StarIcon} boxSize={8} mb={4} />
            <Heading size="md" mb={2}>
              Open Source
            </Heading>
            <Text mb={4}>
              BIMS is free and open-source software licensed under AGPL-3.0.
              Contributions are welcome!
            </Text>
            <HStack justify="center" spacing={4}>
              <Button
                as="a"
                href="https://github.com/kartoza/django-bims"
                target="_blank"
                bg="white"
                color="brand.500"
                _hover={{ bg: 'gray.100' }}
              >
                View on GitHub
              </Button>
              <Button
                as="a"
                href="https://github.com/sponsors/kartoza"
                target="_blank"
                variant="outline"
                borderColor="white"
                _hover={{ bg: 'whiteAlpha.200' }}
              >
                Sponsor Development
              </Button>
            </HStack>
          </CardBody>
        </Card>

        {/* CTA */}
        <HStack justify="center" spacing={4}>
          <Button as={RouterLink} to="/contact" variant="outline">
            Contact Us
          </Button>
          <Button as={RouterLink} to="/resources" colorScheme="brand">
            View Documentation
          </Button>
        </HStack>
      </VStack>
    </Container>
  );
};

export default AboutPage;
