/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Resources and Links page.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  SimpleGrid,
  VStack,
  HStack,
  Card,
  CardBody,
  CardHeader,
  Link,
  Icon,
  Badge,
  useColorModeValue,
  Divider,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import {
  ExternalLinkIcon,
  InfoIcon,
  DownloadIcon,
  LinkIcon,
} from '@chakra-ui/icons';

interface ResourceCardProps {
  title: string;
  description: string;
  links: {
    label: string;
    url: string;
    isExternal?: boolean;
  }[];
  icon: React.ElementType;
  category: string;
}

const ResourceCard: React.FC<ResourceCardProps> = ({
  title,
  description,
  links,
  icon,
  category,
}) => {
  const cardBg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Card bg={cardBg} borderWidth="1px" borderColor={borderColor}>
      <CardHeader pb={2}>
        <HStack justify="space-between" align="start">
          <HStack spacing={3}>
            <Icon as={icon} boxSize={5} color="brand.500" />
            <Heading size="md">{title}</Heading>
          </HStack>
          <Badge colorScheme="brand" variant="subtle">
            {category}
          </Badge>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack align="stretch" spacing={4}>
          <Text color="gray.600" fontSize="sm">
            {description}
          </Text>
          <Divider />
          <List spacing={2}>
            {links.map((link, index) => (
              <ListItem key={index}>
                <HStack>
                  <ListIcon as={LinkIcon} color="brand.500" />
                  <Link
                    href={link.url}
                    isExternal={link.isExternal}
                    color="brand.500"
                    fontSize="sm"
                    _hover={{ textDecoration: 'underline' }}
                  >
                    {link.label}
                    {link.isExternal && (
                      <ExternalLinkIcon mx={1} verticalAlign="text-bottom" />
                    )}
                  </Link>
                </HStack>
              </ListItem>
            ))}
          </List>
        </VStack>
      </CardBody>
    </Card>
  );
};

const ResourcesPage: React.FC = () => {
  const headerBg = useColorModeValue('brand.500', 'brand.600');

  const resources = [
    {
      title: 'BIMS Documentation',
      description:
        'Official documentation for the Biodiversity Information Management System, including user guides and technical documentation.',
      category: 'Documentation',
      icon: InfoIcon,
      links: [
        { label: 'User Guide', url: '/docs/user-guide/', isExternal: false },
        { label: 'API Documentation', url: '/api/docs/', isExternal: false },
        {
          label: 'GitHub Repository',
          url: 'https://github.com/kartoza/django-bims',
          isExternal: true,
        },
      ],
    },
    {
      title: 'Data Standards',
      description:
        'Information about biodiversity data standards, including Darwin Core and GBIF standards used in BIMS.',
      category: 'Standards',
      icon: InfoIcon,
      links: [
        {
          label: 'Darwin Core Standard',
          url: 'https://dwc.tdwg.org/',
          isExternal: true,
        },
        {
          label: 'GBIF Data Standards',
          url: 'https://www.gbif.org/standards',
          isExternal: true,
        },
        {
          label: 'TDWG Standards',
          url: 'https://www.tdwg.org/standards/',
          isExternal: true,
        },
      ],
    },
    {
      title: 'Partner Organizations',
      description:
        'Links to partner organizations and institutions involved in biodiversity research and conservation.',
      category: 'Partners',
      icon: LinkIcon,
      links: [
        { label: 'SANBI', url: 'https://www.sanbi.org/', isExternal: true },
        { label: 'GBIF', url: 'https://www.gbif.org/', isExternal: true },
        {
          label: 'IUCN Red List',
          url: 'https://www.iucnredlist.org/',
          isExternal: true,
        },
        {
          label: 'FishBase',
          url: 'https://www.fishbase.org/',
          isExternal: true,
        },
      ],
    },
    {
      title: 'Data Downloads',
      description:
        'Access datasets and exports from the BIMS platform for your research needs.',
      category: 'Data',
      icon: DownloadIcon,
      links: [
        { label: 'Request Data Download', url: '/new/downloads', isExternal: false },
        { label: 'Species Checklists', url: '/download-request/', isExternal: false },
        { label: 'Data Policy', url: '/about/#data-policy', isExternal: false },
      ],
    },
    {
      title: 'Mapping Resources',
      description:
        'Geographic and mapping resources useful for biodiversity data management.',
      category: 'GIS',
      icon: InfoIcon,
      links: [
        {
          label: 'OpenStreetMap',
          url: 'https://www.openstreetmap.org/',
          isExternal: true,
        },
        {
          label: 'Natural Earth Data',
          url: 'https://www.naturalearthdata.com/',
          isExternal: true,
        },
        {
          label: 'SA National Spatial Data',
          url: 'http://www.sasdi.net/',
          isExternal: true,
        },
      ],
    },
    {
      title: 'Training Materials',
      description:
        'Training videos, tutorials, and workshop materials for learning to use BIMS effectively.',
      category: 'Training',
      icon: InfoIcon,
      links: [
        { label: 'Video Tutorials', url: '/tutorials/', isExternal: false },
        { label: 'Workshop Materials', url: '/workshops/', isExternal: false },
        { label: 'FAQs', url: '/faq/', isExternal: false },
      ],
    },
  ];

  return (
    <Box>
      {/* Header */}
      <Box bg={headerBg} color="white" py={12}>
        <Container maxW="container.xl">
          <VStack spacing={4} textAlign="center">
            <Heading size="xl">Resources & Links</Heading>
            <Text fontSize="lg" maxW="2xl" opacity={0.9}>
              Explore useful resources, documentation, and partner links
              related to biodiversity information management.
            </Text>
          </VStack>
        </Container>
      </Box>

      {/* Resources Grid */}
      <Container maxW="container.xl" py={8}>
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
          {resources.map((resource, index) => (
            <ResourceCard key={index} {...resource} />
          ))}
        </SimpleGrid>
      </Container>

      {/* Additional Info */}
      <Box bg="gray.50" py={8}>
        <Container maxW="container.xl">
          <Card>
            <CardBody>
              <VStack spacing={4}>
                <Heading size="md">Need More Help?</Heading>
                <Text color="gray.600" textAlign="center">
                  If you cannot find what you are looking for, please{' '}
                  <Link href="/new/contact" color="brand.500">
                    contact us
                  </Link>{' '}
                  or{' '}
                  <Link href="/new/bug-report" color="brand.500">
                    report an issue
                  </Link>
                  .
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </Container>
      </Box>
    </Box>
  );
};

export default ResourcesPage;
