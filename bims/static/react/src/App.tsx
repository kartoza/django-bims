/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Main application component for BIMS React frontend.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { Suspense, lazy } from 'react';
import { Box, Flex, Spinner, Center, Text, Link, HStack } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { AppProvider } from './providers/AppProvider';
import { MapProvider } from './providers/MapProvider';
import Header from './components/Header';
import MapLayout from './layouts/MapLayout';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy load pages for better performance
const LandingPage = lazy(() => import('./pages/LandingPage'));
const MapPage = lazy(() => import('./pages/MapPage'));
const SourceReferencesPage = lazy(() => import('./pages/SourceReferencesPage'));
const SiteVisitsPage = lazy(() => import('./pages/SiteVisitsPage'));
const DownloadsPage = lazy(() => import('./pages/DownloadsPage'));
const UploadPage = lazy(() => import('./pages/UploadPage'));
const AddSitePage = lazy(() => import('./pages/AddSitePage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const ContactPage = lazy(() => import('./pages/ContactPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const TaxaManagementPage = lazy(() => import('./pages/TaxaManagementPage'));
const ValidationPage = lazy(() => import('./pages/ValidationPage'));
const AddRecordPage = lazy(() => import('./pages/AddRecordPage'));
const ResourcesPage = lazy(() => import('./pages/ResourcesPage'));
const BugReportPage = lazy(() => import('./pages/BugReportPage'));
const DashboardSettingsPage = lazy(() => import('./pages/DashboardSettingsPage'));
const HarvestPage = lazy(() => import('./pages/HarvestPage'));
const SummaryReportPage = lazy(() => import('./pages/SummaryReportPage'));
const VisualizationLayersPage = lazy(() => import('./pages/VisualizationLayersPage'));
const ContextLayersPage = lazy(() => import('./pages/ContextLayersPage'));
const AnalyticsDashboardPage = lazy(() => import('./pages/AnalyticsDashboardPage'));
const SiteDashboardPage = lazy(() => import('./pages/SiteDashboardPage'));
const SASSDashboardPage = lazy(() => import('./pages/SASSDashboardPage'));
const WaterTemperatureDashboardPage = lazy(() => import('./pages/WaterTemperatureDashboardPage'));
const PhysicoChemicalDashboardPage = lazy(() => import('./pages/PhysicoChemicalDashboardPage'));
const BackupsManagementPage = lazy(() => import('./pages/BackupsManagementPage'));

// Placeholder for pages not yet implemented
const PlaceholderPage: React.FC<{ title: string }> = ({ title }) => (
  <Center h="calc(100vh - 140px)" bg="gray.50">
    <Box textAlign="center">
      <Text fontSize="2xl" fontWeight="bold" mb={2}>
        {title}
      </Text>
      <Text color="gray.600">This page is coming soon</Text>
    </Box>
  </Center>
);

// Loading fallback
const LoadingFallback: React.FC = () => (
  <Center h="calc(100vh - 140px)" bg="gray.50">
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
  console.log('[App] Rendering, pathname:', window.location.pathname);
  return (
    <AppProvider>
      <BrowserRouter basename="/new">
        <MapProvider>
          <Flex direction="column" h="100vh">
            {/* Header - always visible */}
            <Header />

            {/* Main content - uses flex=1 to fill space, overflow auto for scrollable pages */}
            <Box flex="1" position="relative" overflow="auto" minH={0} minW={0}>
              <ErrorBoundary>
              <Suspense fallback={<LoadingFallback />}>
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

                  {/* Data pages */}
                  <Route path="/source-references" element={<SourceReferencesPage />} />
                  <Route path="/source-references/:id" element={<SourceReferencesPage />} />
                  <Route path="/site-visits" element={<SiteVisitsPage />} />
                  <Route path="/site-visits/:id" element={<SiteVisitsPage />} />
                  <Route path="/my-site-visits" element={<SiteVisitsPage />} />
                  <Route path="/downloads" element={<DownloadsPage />} />

                  {/* Upload pages */}
                  <Route path="/upload" element={<Navigate to="/upload/occurrence" replace />} />
                  <Route path="/upload/:type" element={<UploadPage />} />

                  {/* Add/Create pages */}
                  <Route path="/add/site" element={<AddSitePage />} />
                  <Route path="/add/wetland" element={<AddSitePage />} />
                  <Route path="/add/fish" element={<AddRecordPage />} />
                  <Route path="/add/invertebrate" element={<AddRecordPage />} />
                  <Route path="/add/algae" element={<AddRecordPage />} />
                  <Route path="/add/module" element={<AddRecordPage />} />
                  <Route path="/add/abiotic" element={<AddRecordPage />} />
                  <Route path="/add/source-reference" element={<SourceReferencesPage />} />

                  {/* Validation pages */}
                  <Route path="/validate/sites" element={<ValidationPage />} />
                  <Route path="/validate/records" element={<ValidationPage />} />
                  <Route path="/validate/taxa" element={<ValidationPage />} />

                  {/* Analytics */}
                  <Route path="/analytics" element={<AnalyticsDashboardPage />} />

                  {/* Dashboard pages */}
                  <Route path="/dashboard/site/:siteId" element={<SiteDashboardPage />} />
                  <Route path="/dashboard/sass/:siteId" element={<SASSDashboardPage />} />
                  <Route path="/dashboard/water-temperature/:siteId" element={<WaterTemperatureDashboardPage />} />
                  <Route path="/dashboard/physico-chemical/:siteId" element={<PhysicoChemicalDashboardPage />} />

                  {/* Admin pages */}
                  <Route path="/admin/taxa" element={<TaxaManagementPage />} />
                  <Route path="/admin/dashboard" element={<DashboardSettingsPage />} />
                  <Route path="/admin/layers" element={<VisualizationLayersPage />} />
                  <Route path="/admin/context-layers" element={<ContextLayersPage />} />
                  <Route path="/admin/summary" element={<SummaryReportPage />} />
                  <Route path="/admin/backups" element={<BackupsManagementPage />} />

                  {/* Harvest pages */}
                  <Route path="/harvest/gbif" element={<HarvestPage />} />
                  <Route path="/harvest/species" element={<HarvestPage />} />

                  {/* About pages */}
                  <Route path="/about" element={<AboutPage />} />
                  <Route path="/contact" element={<ContactPage />} />
                  <Route path="/resources" element={<ResourcesPage />} />
                  <Route path="/bug-report" element={<BugReportPage />} />

                  {/* Authentication pages */}
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />

                  {/* User pages */}
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/profile/:username" element={<ProfilePage />} />

                  {/* Catch-all redirect */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
              </ErrorBoundary>
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
