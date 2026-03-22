/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Breadcrumb navigation component for page hierarchy
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
import {
  Breadcrumb as ChakraBreadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Box,
  Icon,
} from '@chakra-ui/react';
import { ChevronRightIcon } from '@chakra-ui/icons';
import { Link as RouterLink, useLocation } from 'react-router-dom';

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
  showHome?: boolean;
}

// Route-to-breadcrumb mapping for automatic generation
const routeLabels: Record<string, string> = {
  '': 'Home',
  'map': 'Map',
  'source-references': 'Source References',
  'site-visits': 'Site Visits',
  'my-site-visits': 'My Site Visits',
  'downloads': 'Downloads',
  'upload': 'Upload',
  'add': 'Add Data',
  'validate': 'Validation',
  'admin': 'Administration',
  'about': 'About',
  'contact': 'Contact',
  'resources': 'Resources',
  'bug-report': 'Report Bug',
  'login': 'Sign In',
  'register': 'Register',
  'profile': 'Profile',
  'analytics': 'Analytics',
  'dashboard': 'Dashboard',
  'harvest': 'Data Harvest',
  // Upload types
  'occurrence': 'Occurrence Data',
  'taxa': 'Taxonomic Data',
  'physico-chemical': 'Physico-Chemical',
  'water-temperature': 'Water Temperature',
  'shapefile': 'Shapefile',
  'spatial-layer': 'Spatial Layer',
  // Add types
  'site': 'Location Site',
  'wetland': 'Wetland Site',
  'fish': 'Fish Record',
  'invertebrate': 'Invertebrate Record',
  'algae': 'Algae Record',
  'module': 'Module Record',
  'abiotic': 'Abiotic Data',
  // Validate types
  'sites': 'Sites',
  'records': 'Records',
  // Admin sections
  'layers': 'Visualization Layers',
  'context-layers': 'Context Layers',
  'summary': 'Summary Report',
  'backups': 'Backups',
  // Harvest types
  'gbif': 'GBIF',
  'species': 'Species',
  // Dashboard types
  'sass': 'SASS',
};

const Breadcrumb: React.FC<BreadcrumbProps> = ({ items, showHome = true }) => {
  const location = useLocation();

  // Generate breadcrumb items from current path if not provided
  const breadcrumbItems: BreadcrumbItem[] = React.useMemo(() => {
    if (items) return items;

    const pathSegments = location.pathname.split('/').filter(Boolean);
    const generatedItems: BreadcrumbItem[] = [];

    if (showHome) {
      generatedItems.push({ label: 'Home', path: '/' });
    }

    let currentPath = '';
    for (const segment of pathSegments) {
      currentPath += `/${segment}`;
      const label = routeLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
      generatedItems.push({ label, path: currentPath });
    }

    return generatedItems;
  }, [items, location.pathname, showHome]);

  // Don't render if there's only home or no items
  if (breadcrumbItems.length <= 1) return null;

  return (
    <Box py={2} px={4} bg="gray.50" borderBottomWidth={1} borderColor="gray.200">
      <ChakraBreadcrumb
        separator={<Icon as={ChevronRightIcon} color="gray.400" boxSize={3} />}
        fontSize="sm"
        color="gray.600"
      >
        {breadcrumbItems.map((item, index) => {
          const isLast = index === breadcrumbItems.length - 1;

          return (
            <BreadcrumbItem key={index} isCurrentPage={isLast}>
              {isLast || !item.path ? (
                <BreadcrumbLink
                  fontWeight={isLast ? '600' : '400'}
                  color={isLast ? 'gray.800' : 'gray.600'}
                  cursor={isLast ? 'default' : 'pointer'}
                  _hover={isLast ? {} : { color: 'brand.500' }}
                >
                  {item.label}
                </BreadcrumbLink>
              ) : (
                <BreadcrumbLink
                  as={RouterLink}
                  to={item.path}
                  _hover={{ color: 'brand.500', textDecoration: 'none' }}
                >
                  {item.label}
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>
          );
        })}
      </ChakraBreadcrumb>
    </Box>
  );
};

export default Breadcrumb;
