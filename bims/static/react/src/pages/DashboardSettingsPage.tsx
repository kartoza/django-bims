/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Dashboard Settings admin page.
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
  FormControl,
  FormLabel,
  FormHelperText,
  Input,
  Textarea,
  Switch,
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
  Divider,
  Badge,
  IconButton,
  InputGroup,
  InputLeftElement,
  Image,
  Alert,
  AlertIcon,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Tooltip,
} from '@chakra-ui/react';
import {
  SettingsIcon,
  EditIcon,
  AddIcon,
  DeleteIcon,
  ViewIcon,
  RepeatIcon,
} from '@chakra-ui/icons';
import { useMapCache } from '../hooks/useMapCache';
import {
  useDashboardSettingsStore,
  AVAILABLE_WIDGET_TYPES,
  DashboardWidget,
} from '../stores/dashboardSettingsStore';

const DashboardSettingsPage: React.FC = () => {
  const toast = useToast();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  // Map cache management
  const {
    stats: cacheStats,
    isLoading: isCacheLoading,
    refreshStats: refreshCacheStats,
    clearLocalCache,
    invalidateServerCache,
  } = useMapCache();

  // Refresh cache stats on mount
  useEffect(() => {
    refreshCacheStats();
  }, [refreshCacheStats]);

  // Use the shared store for settings persistence
  const {
    branding,
    landingPage,
    mapSettings,
    widgets,
    setBranding: updateBranding,
    setLandingPage: updateLandingPage,
    setMapSettings: updateMapSettings,
    addWidget: storeAddWidget,
    removeWidget: storeRemoveWidget,
    toggleWidget: storeToggleWidget,
    moveWidgetUp,
    moveWidgetDown,
    resetToDefaults,
  } = useDashboardSettingsStore();

  const [isSaving, setIsSaving] = useState(false);

  // Get widgets that haven't been added yet
  const availableToAdd = AVAILABLE_WIDGET_TYPES.filter(
    (wt) => !widgets.some((w) => w.id === wt.id)
  );

  const allWidgetsAdded = availableToAdd.length === 0;

  // Add a new widget
  const addWidget = (widgetTypeId: string) => {
    const widgetType = AVAILABLE_WIDGET_TYPES.find((wt) => wt.id === widgetTypeId);
    if (!widgetType) return;

    storeAddWidget(widgetTypeId);

    toast({
      title: 'Widget added',
      description: `${widgetType.name} has been added to the dashboard.`,
      status: 'success',
      duration: 2000,
    });
  };

  // Remove a widget
  const removeWidget = (id: string) => {
    storeRemoveWidget(id);
    toast({
      title: 'Widget removed',
      status: 'info',
      duration: 2000,
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Settings are auto-saved to localStorage via Zustand persist
      // This could also sync to an API in the future
      await new Promise((resolve) => setTimeout(resolve, 500));

      toast({
        title: 'Settings saved',
        description: 'Dashboard settings have been saved.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error saving settings',
        description: 'There was an error saving the settings. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const toggleWidget = (id: string) => {
    storeToggleWidget(id);
  };

  return (
    <Box h="100%" overflowY="auto">
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <HStack>
                <SettingsIcon />
                <Heading size="lg">Dashboard Settings</Heading>
              </HStack>
              <Text opacity={0.9}>Configure site appearance and dashboard widgets</Text>
            </VStack>
            <Button
              colorScheme="whiteAlpha"
              onClick={handleSave}
              isLoading={isSaving}
              loadingText="Saving..."
            >
              Save Changes
            </Button>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <Tabs variant="enclosed" colorScheme="brand">
          <TabList>
            <Tab>Site Branding</Tab>
            <Tab>Landing Page</Tab>
            <Tab>Dashboard Widgets</Tab>
            <Tab>Map Settings</Tab>
          </TabList>

          <TabPanels>
            {/* Site Branding Tab */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">Site Branding</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                      <FormControl>
                        <FormLabel>Site Name</FormLabel>
                        <Input
                          value={branding.siteName}
                          onChange={(e) =>
                            updateBranding({ siteName: e.target.value })
                          }
                        />
                        <FormHelperText>Displayed in header and browser tab</FormHelperText>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Primary Color</FormLabel>
                        <Input
                          type="color"
                          value={branding.primaryColor}
                          onChange={(e) =>
                            updateBranding({ primaryColor: e.target.value })
                          }
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Site Description</FormLabel>
                        <Textarea
                          value={branding.siteDescription}
                          onChange={(e) =>
                            updateBranding({ siteDescription: e.target.value })
                          }
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Logo URL</FormLabel>
                        <Input
                          value={branding.logoUrl}
                          onChange={(e) =>
                            updateBranding({ logoUrl: e.target.value })
                          }
                          placeholder="/static/img/logo.png"
                        />
                        {branding.logoUrl && (
                          <Image
                            src={branding.logoUrl}
                            alt="Site Logo"
                            maxH="60px"
                            mt={2}
                            fallbackSrc="https://via.placeholder.com/150x60?text=Logo"
                          />
                        )}
                      </FormControl>
                    </SimpleGrid>

                    <FormControl>
                      <FormLabel>Banner Image URL</FormLabel>
                      <Input
                        value={branding.bannerImage}
                        onChange={(e) =>
                          updateBranding({ bannerImage: e.target.value })
                        }
                        placeholder="/static/img/landing_page_banner.jpeg"
                      />
                      {branding.bannerImage && (
                        <Image
                          src={branding.bannerImage}
                          alt="Banner"
                          maxH="150px"
                          mt={2}
                          objectFit="cover"
                          width="100%"
                          fallbackSrc="https://via.placeholder.com/1200x300?text=Banner"
                        />
                      )}
                    </FormControl>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Landing Page Tab */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">Landing Page Configuration</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                      <FormControl>
                        <FormLabel>Hero Title</FormLabel>
                        <Input
                          value={landingPage.heroTitle}
                          onChange={(e) =>
                            updateLandingPage({ heroTitle: e.target.value })
                          }
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Hero Subtitle</FormLabel>
                        <Input
                          value={landingPage.heroSubtitle}
                          onChange={(e) =>
                            updateLandingPage({ heroSubtitle: e.target.value })
                          }
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>CTA Button Text</FormLabel>
                        <Input
                          value={landingPage.ctaButtonText}
                          onChange={(e) =>
                            updateLandingPage({ ctaButtonText: e.target.value })
                          }
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>CTA Button URL</FormLabel>
                        <Input
                          value={landingPage.ctaButtonUrl}
                          onChange={(e) =>
                            updateLandingPage({ ctaButtonUrl: e.target.value })
                          }
                        />
                      </FormControl>
                    </SimpleGrid>

                    <Divider />

                    <Heading size="sm">Section Visibility</Heading>
                    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel mb={0}>Show Statistics</FormLabel>
                        <Switch
                          isChecked={landingPage.showStats}
                          onChange={(e) =>
                            updateLandingPage({ showStats: e.target.checked })
                          }
                          colorScheme="brand"
                        />
                      </FormControl>

                      <FormControl display="flex" alignItems="center">
                        <FormLabel mb={0}>Show Partners</FormLabel>
                        <Switch
                          isChecked={landingPage.showPartners}
                          onChange={(e) =>
                            updateLandingPage({ showPartners: e.target.checked })
                          }
                          colorScheme="brand"
                        />
                      </FormControl>

                      <FormControl display="flex" alignItems="center">
                        <FormLabel mb={0}>Show Ecosystems</FormLabel>
                        <Switch
                          isChecked={landingPage.showEcosystems}
                          onChange={(e) =>
                            updateLandingPage({ showEcosystems: e.target.checked })
                          }
                          colorScheme="brand"
                        />
                      </FormControl>
                    </SimpleGrid>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Dashboard Widgets Tab */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <HStack justify="space-between">
                    <Heading size="md">Dashboard Widgets</Heading>
                    <Tooltip
                      label={allWidgetsAdded ? 'All available widgets have been added' : 'Add a new widget to the dashboard'}
                      hasArrow
                    >
                      <Box>
                        <Menu>
                          <MenuButton
                            as={Button}
                            leftIcon={<AddIcon />}
                            size="sm"
                            colorScheme="brand"
                            isDisabled={allWidgetsAdded}
                          >
                            Add Widget
                            {!allWidgetsAdded && (
                              <Badge ml={2} colorScheme="green" borderRadius="full">
                                {availableToAdd.length}
                              </Badge>
                            )}
                          </MenuButton>
                          <MenuList maxH="300px" overflowY="auto">
                            {availableToAdd.map((wt) => (
                              <MenuItem
                                key={wt.id}
                                onClick={() => addWidget(wt.id)}
                              >
                                <VStack align="start" spacing={0}>
                                  <HStack>
                                    <Text fontWeight="medium">{wt.name}</Text>
                                    <Badge size="sm" colorScheme="purple">{wt.type}</Badge>
                                  </HStack>
                                  <Text fontSize="xs" color="gray.500">
                                    {wt.description}
                                  </Text>
                                </VStack>
                              </MenuItem>
                            ))}
                          </MenuList>
                        </Menu>
                      </Box>
                    </Tooltip>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <Alert status="info" borderRadius="md">
                      <AlertIcon />
                      Enable or disable widgets that appear on user dashboards.
                      {widgets.length > 0 && ` ${widgets.length} widget${widgets.length !== 1 ? 's' : ''} configured.`}
                    </Alert>

                    {widgets.length === 0 ? (
                      <Box textAlign="center" py={8} color="gray.500">
                        <Text>No widgets configured.</Text>
                        <Text fontSize="sm">Click "Add Widget" to get started.</Text>
                      </Box>
                    ) : (
                      widgets.map((widget) => (
                        <HStack
                          key={widget.id}
                          p={4}
                          bg={useColorModeValue('gray.50', 'gray.600')}
                          borderRadius="md"
                          justify="space-between"
                          opacity={widget.enabled ? 1 : 0.6}
                        >
                          <HStack spacing={4}>
                            <Text fontWeight="medium">{widget.name}</Text>
                            <Badge colorScheme="purple">{widget.type}</Badge>
                            {!widget.enabled && (
                              <Badge colorScheme="gray">Disabled</Badge>
                            )}
                          </HStack>
                          <HStack>
                            <Tooltip label={widget.enabled ? 'Disable widget' : 'Enable widget'}>
                              <Switch
                                isChecked={widget.enabled}
                                onChange={() => toggleWidget(widget.id)}
                                colorScheme="brand"
                              />
                            </Tooltip>
                            <Tooltip label="Remove widget">
                              <IconButton
                                aria-label="Delete widget"
                                icon={<DeleteIcon />}
                                size="sm"
                                variant="ghost"
                                colorScheme="red"
                                onClick={() => removeWidget(widget.id)}
                              />
                            </Tooltip>
                          </HStack>
                        </HStack>
                      ))
                    )}
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Map Settings Tab */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">Map Configuration</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                      <FormControl>
                        <FormLabel>Default Center Latitude</FormLabel>
                        <Input
                          type="number"
                          step="0.0001"
                          value={mapSettings.defaultLatitude}
                          onChange={(e) =>
                            updateMapSettings({ defaultLatitude: parseFloat(e.target.value) || 0 })
                          }
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Default Center Longitude</FormLabel>
                        <Input
                          type="number"
                          step="0.0001"
                          value={mapSettings.defaultLongitude}
                          onChange={(e) =>
                            updateMapSettings({ defaultLongitude: parseFloat(e.target.value) || 0 })
                          }
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Default Zoom Level</FormLabel>
                        <Select
                          value={mapSettings.defaultZoom}
                          onChange={(e) =>
                            updateMapSettings({ defaultZoom: parseInt(e.target.value, 10) })
                          }
                        >
                          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15].map((z) => (
                            <option key={z} value={z}>
                              {z}
                            </option>
                          ))}
                        </Select>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Default Base Map</FormLabel>
                        <Select
                          value={mapSettings.defaultBaseMap}
                          onChange={(e) =>
                            updateMapSettings({ defaultBaseMap: e.target.value as 'osm' | 'satellite' | 'terrain' | 'dark' })
                          }
                        >
                          <option value="osm">OpenStreetMap</option>
                          <option value="satellite">Satellite</option>
                          <option value="terrain">Terrain</option>
                          <option value="dark">Dark Mode</option>
                        </Select>
                      </FormControl>
                    </SimpleGrid>

                    <Divider />

                    <Heading size="sm">Map Features</Heading>
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel mb={0}>Enable Clustering</FormLabel>
                        <Switch
                          isChecked={mapSettings.enableClustering}
                          onChange={(e) =>
                            updateMapSettings({ enableClustering: e.target.checked })
                          }
                          colorScheme="brand"
                        />
                      </FormControl>

                      <FormControl display="flex" alignItems="center">
                        <FormLabel mb={0}>Show Scale Bar</FormLabel>
                        <Switch
                          isChecked={mapSettings.showScaleBar}
                          onChange={(e) =>
                            updateMapSettings({ showScaleBar: e.target.checked })
                          }
                          colorScheme="brand"
                        />
                      </FormControl>

                      <FormControl display="flex" alignItems="center">
                        <FormLabel mb={0}>Enable Drawing Tools</FormLabel>
                        <Switch
                          isChecked={mapSettings.enableDrawingTools}
                          onChange={(e) =>
                            updateMapSettings({ enableDrawingTools: e.target.checked })
                          }
                          colorScheme="brand"
                        />
                      </FormControl>

                      <FormControl display="flex" alignItems="center">
                        <FormLabel mb={0}>Show Mini Map</FormLabel>
                        <Switch
                          isChecked={mapSettings.showMiniMap}
                          onChange={(e) =>
                            updateMapSettings({ showMiniMap: e.target.checked })
                          }
                          colorScheme="brand"
                        />
                      </FormControl>
                    </SimpleGrid>
                  </VStack>
                </CardBody>
              </Card>

              {/* Map Points Cache Management */}
              <Card bg={cardBg} mt={6}>
                <CardHeader>
                  <HStack justify="space-between">
                    <Heading size="md">Map Points Cache</Heading>
                    <IconButton
                      aria-label="Refresh stats"
                      icon={<RepeatIcon />}
                      size="sm"
                      variant="ghost"
                      onClick={refreshCacheStats}
                      isLoading={isCacheLoading}
                    />
                  </HStack>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <Text fontSize="sm" color="gray.600">
                      Map points are cached on both the server and client to improve performance.
                      Use these controls to manage the cache when data has been updated.
                    </Text>

                    <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
                      <Box p={3} bg="gray.50" borderRadius="md" textAlign="center">
                        <Text fontSize="2xl" fontWeight="bold" color="brand.500">
                          {cacheStats?.entryCount ?? '-'}
                        </Text>
                        <Text fontSize="xs" color="gray.500">Cached Queries</Text>
                      </Box>
                      <Box p={3} bg="gray.50" borderRadius="md" textAlign="center">
                        <Text fontSize="2xl" fontWeight="bold" color="green.500">
                          {cacheStats?.totalPoints?.toLocaleString() ?? '-'}
                        </Text>
                        <Text fontSize="xs" color="gray.500">Cached Points</Text>
                      </Box>
                      <Box p={3} bg="gray.50" borderRadius="md" textAlign="center">
                        <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                          {cacheStats?.serverVersion ?? '-'}
                        </Text>
                        <Text fontSize="xs" color="gray.500">Server Version</Text>
                      </Box>
                      <Box p={3} bg="gray.50" borderRadius="md" textAlign="center">
                        <Text fontSize="2xl" fontWeight="bold" color="orange.500">
                          {cacheStats?.oldestEntry
                            ? `${Math.round((Date.now() - cacheStats.oldestEntry) / 60000)}m`
                            : '-'}
                        </Text>
                        <Text fontSize="xs" color="gray.500">Oldest Entry</Text>
                      </Box>
                    </SimpleGrid>

                    <Divider />

                    <HStack spacing={4}>
                      <Button
                        colorScheme="blue"
                        variant="outline"
                        size="sm"
                        onClick={clearLocalCache}
                        isLoading={isCacheLoading}
                      >
                        Clear Local Cache
                      </Button>
                      <Tooltip label="Invalidates cache for all users. Requires staff permissions.">
                        <Button
                          colorScheme="red"
                          size="sm"
                          onClick={invalidateServerCache}
                          isLoading={isCacheLoading}
                        >
                          Invalidate Server Cache
                        </Button>
                      </Tooltip>
                    </HStack>

                    <Alert status="info" variant="subtle" fontSize="sm">
                      <AlertIcon />
                      <Box>
                        <Text fontWeight="medium">Cache Behavior</Text>
                        <Text>Client cache has a 5-minute TTL. Server cache version changes trigger refetch.</Text>
                      </Box>
                    </Alert>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Container>
    </Box>
  );
};

export default DashboardSettingsPage;
