/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Main application component for BIMS React frontend.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
import { Box, Flex, Spinner, Center, Text, Link, HStack } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { AppProvider } from './providers/AppProvider';
import { MapProvider } from './providers/MapProvider';
import Header from './components/Header';
import MapLayout from './layouts/MapLayout';
import MapPage from './pages/MapPage';
import LandingPage from './pages/LandingPage';

// Placeholder components - will be implemented in later tasks
const DashboardPage: React.FC = () => (
  <Center h="calc(100vh - 100px)">
    <Text>Dashboard Coming Soon</Text>
  </Center>
);

const LoadingFallback: React.FC = () => (
  <Center h="100vh" bg="gray.50">
    <Spinner size="xl" color="brand.500" thickness="4px" />
  </Center>
);

// Footer component with Kartoza branding
const Footer: React.FC = () => (
  <HStack
    as="footer"
    justify="center"
    py={2}
    px={4}
    bg="white"
    borderTopWidth={1}
    borderColor="gray.200"
    fontSize="sm"
    color="gray.600"
  >
    <Text>
      Made with{' '}
      <Text as="span" color="red.500">
        &hearts;
      </Text>{' '}
      by{' '}
      <Link href="https://kartoza.com" isExternal color="brand.500">
        Kartoza
      </Link>
    </Text>
    <Text mx={2}>|</Text>
    <Link
      href="https://github.com/sponsors/kartoza"
      isExternal
      color="brand.500"
    >
      Donate!
    </Link>
    <Text mx={2}>|</Text>
    <Link
      href="https://github.com/kartoza/django-bims"
      isExternal
      color="brand.500"
    >
      GitHub
    </Link>
  </HStack>
);

const App: React.FC = () => {
  return (
    <AppProvider>
      <BrowserRouter basename="/new">
        <MapProvider>
          <Flex direction="column" minH="100vh">
            {/* Header - always visible */}
            <Header />

            {/* Main content */}
            <Box flex="1">
              <React.Suspense fallback={<LoadingFallback />}>
                <Routes>
                  {/* Landing page */}
                  <Route path="/" element={<LandingPage />} />

                  {/* Map view - main interface */}
                  <Route
                    path="/map"
                    element={
                      <MapLayout>
                        <MapPage />
                      </MapLayout>
                    }
                  />
                  <Route
                    path="/map/site/:siteId"
                    element={
                      <MapLayout>
                        <MapPage />
                      </MapLayout>
                    }
                  />
                  <Route
                    path="/map/taxon/:taxonId"
                    element={
                      <MapLayout>
                        <MapPage />
                      </MapLayout>
                    }
                  />

                  {/* Dashboard views */}
                  <Route path="/dashboard" element={<DashboardPage />} />

                  {/* Catch-all redirect */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </React.Suspense>
            </Box>

            {/* Footer - always visible */}
            <Footer />
          </Flex>
        </MapProvider>
      </BrowserRouter>
    </AppProvider>
  );
};

export default App;
