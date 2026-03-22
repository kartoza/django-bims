/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Add Spatial Filter page.
 * Manage context layers for geocontext lookups on location sites.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect, useCallback } from 'react';
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
  Select,
  Input,
  Button,
  useToast,
  useColorModeValue,
  Alert,
  AlertIcon,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  Spinner,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Tooltip,
  Code,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Progress,
  Collapse,
} from '@chakra-ui/react';
import {
  AddIcon,
  DeleteIcon,
  InfoIcon,
  SettingsIcon,
  RepeatIcon,
  CheckCircleIcon,
  WarningIcon,
  TimeIcon,
} from '@chakra-ui/icons';
import { apiClient } from '../api/client';

interface CloudNativeLayer {
  id: number;
  unique_id: string;
  name: string;
  abstract?: string;
  attributes?: string[];
}

interface ContextLayerGroup {
  id: number;
  name: string;
  key: string; // UUID:attribute_name or geocontext key
  layer_identifier?: string;
  geocontext_group_key?: string;
  native_layer?: CloudNativeLayer;
  site_count?: number;
}

const SpatialFilterPage: React.FC = () => {
  const toast = useToast();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [availableLayers, setAvailableLayers] = useState<CloudNativeLayer[]>([]);
  const [contextGroups, setContextGroups] = useState<ContextLayerGroup[]>([]);
  const [selectedLayerId, setSelectedLayerId] = useState<string>('');
  const [selectedAttribute, setSelectedAttribute] = useState('');
  const [groupName, setGroupName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isHarvesting, setIsHarvesting] = useState(false);
  const [harvestSuccess, setHarvestSuccess] = useState(false);
  const [harvestLogs, setHarvestLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState(false);

  // Get attributes for selected layer
  const selectedLayer = availableLayers.find((l) => l.unique_id === selectedLayerId);
  const layerAttributes = selectedLayer?.attributes || [];

  // Fetch available cloud native layers
  const fetchAvailableLayers = useCallback(async () => {
    try {
      const response = await apiClient.get<{ data: CloudNativeLayer[] }>(
        'cloud-native-layers/'
      );
      setAvailableLayers(response.data?.data || []);
    } catch (error) {
      console.error('Failed to fetch available layers:', error);
    }
  }, []);

  // Fetch context layer groups
  const fetchContextGroups = useCallback(async () => {
    try {
      const response = await apiClient.get<{ data: ContextLayerGroup[] }>(
        'context-layer-groups/'
      );
      setContextGroups(response.data?.data || []);
    } catch (error) {
      console.error('Failed to fetch context groups:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Check harvesting status
  const checkHarvestingStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/is-harvesting-geocontext/');
      if (response.ok) {
        const data = await response.json();
        setIsHarvesting(data.harvesting === true);
        return data.harvesting === true;
      }
    } catch (error) {
      console.error('Failed to check harvesting status:', error);
    }
    return false;
  }, []);

  // Fetch harvest logs
  const fetchHarvestLogs = useCallback(async () => {
    try {
      const response = await fetch('/api/harvesting-geocontext-logs/');
      if (response.ok) {
        const data = await response.json();
        setHarvestLogs(data.log || []);
      }
    } catch (error) {
      console.error('Failed to fetch harvest logs:', error);
    }
  }, []);

  useEffect(() => {
    fetchAvailableLayers();
    fetchContextGroups();
    checkHarvestingStatus();
  }, [fetchAvailableLayers, fetchContextGroups, checkHarvestingStatus]);

  // Poll harvesting status when harvesting is in progress
  useEffect(() => {
    if (!isHarvesting) return;

    const interval = setInterval(async () => {
      const stillHarvesting = await checkHarvestingStatus();
      if (stillHarvesting) {
        fetchHarvestLogs();
      } else {
        // Harvesting finished successfully
        setHarvestSuccess(true);
        toast({
          title: 'Harvesting complete',
          description: 'Geocontext data has been updated for all sites.',
          status: 'success',
          duration: 5000,
        });
        fetchContextGroups(); // Refresh to show updated site counts

        // Reset success state after 5 seconds
        setTimeout(() => setHarvestSuccess(false), 5000);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isHarvesting, checkHarvestingStatus, fetchHarvestLogs, fetchContextGroups, toast]);

  const handleSelectLayer = (layerId: string) => {
    setSelectedLayerId(layerId);
    setSelectedAttribute('');
    const layer = availableLayers.find((l) => l.unique_id === layerId);
    if (layer) {
      setGroupName(layer.name);
    }
  };

  const handleSave = async () => {
    if (!selectedLayerId || !selectedAttribute || !groupName.trim()) {
      toast({
        title: 'Missing fields',
        description: 'Please fill in all required fields.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsSaving(true);

    try {
      // The key format for native layers is UUID:attribute_name
      const key = `${selectedLayerId}:${selectedAttribute}`;

      await apiClient.post('context-layer-groups/', {
        name: groupName,
        key: key,
        layer_identifier: selectedAttribute,
      });

      toast({
        title: 'Spatial filter added',
        description: 'The context layer group has been created.',
        status: 'success',
        duration: 3000,
      });

      onClose();
      setSelectedLayerId('');
      setSelectedAttribute('');
      setGroupName('');
      fetchContextGroups();
    } catch (error: any) {
      toast({
        title: 'Failed to save',
        description: error.response?.data?.message || 'Failed to create context layer group.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (group: ContextLayerGroup) => {
    if (!confirm(`Are you sure you want to delete "${group.name}"? This will remove context data from all associated sites.`)) {
      return;
    }

    try {
      await apiClient.delete(`context-layer-groups/${group.id}/`);
      toast({
        title: 'Deleted',
        status: 'success',
        duration: 3000,
      });
      fetchContextGroups();
    } catch (error) {
      toast({
        title: 'Failed to delete',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleHarvestContext = async (harvestAll = false) => {
    if (isHarvesting) {
      toast({
        title: 'Harvesting in progress',
        description: 'Please wait for the current harvest to complete.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      const response = await fetch('/api/harvest-geocontext/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '',
        },
        body: JSON.stringify({ is_all: harvestAll }),
      });

      if (response.ok) {
        setIsHarvesting(true);
        setShowLogs(true);
        toast({
          title: 'Harvest started',
          description: harvestAll
            ? 'Re-harvesting geocontext data for ALL sites. This may take a while.'
            : 'Harvesting geocontext data for sites without context. This may take a while.',
          status: 'info',
          duration: 5000,
        });
      } else {
        const data = await response.json();
        toast({
          title: 'Failed to start harvest',
          description: data.error || 'Unknown error occurred.',
          status: 'error',
          duration: 5000,
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to start harvest',
        description: 'Network error occurred.',
        status: 'error',
        duration: 3000,
      });
    }
  };

  // Separate native layer groups from external geocontext groups
  const nativeLayerGroups = contextGroups.filter((g) => g.key?.includes(':'));
  const externalGroups = contextGroups.filter((g) => !g.key?.includes(':'));

  return (
    <Box h="100%" overflowY="auto">
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <HStack>
                <SettingsIcon />
                <Heading size="lg">Add Spatial Filter</Heading>
              </HStack>
              <Text opacity={0.9}>
                Configure context layers for geocontext lookups on location sites
              </Text>
            </VStack>
            <HStack spacing={3}>
              <Button
                colorScheme={harvestSuccess ? 'green' : isHarvesting ? 'yellow' : 'blue'}
                leftIcon={
                  harvestSuccess ? <CheckCircleIcon /> :
                  isHarvesting ? <Spinner size="sm" /> :
                  <RepeatIcon />
                }
                onClick={() => handleHarvestContext(false)}
                isDisabled={isHarvesting}
                size="md"
                variant={harvestSuccess ? 'solid' : 'solid'}
                _hover={harvestSuccess ? { bg: 'green.600' } : undefined}
              >
                {harvestSuccess ? 'Harvest Complete!' : isHarvesting ? 'Harvesting...' : 'Harvest Geocontext'}
              </Button>
              <Button
                colorScheme="whiteAlpha"
                leftIcon={<AddIcon />}
                onClick={onOpen}
                isDisabled={availableLayers.length === 0}
              >
                Add Filter
              </Button>
            </HStack>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* Harvesting Progress */}
          <Collapse in={isHarvesting || showLogs} animateOpacity>
            <Card bg={isHarvesting ? 'blue.50' : 'green.50'} borderWidth={2} borderColor={isHarvesting ? 'blue.300' : 'green.300'}>
              <CardHeader py={3}>
                <HStack justify="space-between">
                  <HStack>
                    {isHarvesting ? (
                      <>
                        <Spinner size="sm" color="blue.500" />
                        <Heading size="sm" color="blue.700">Harvesting in Progress</Heading>
                      </>
                    ) : (
                      <>
                        <CheckCircleIcon color="green.500" />
                        <Heading size="sm" color="green.700">Harvest Complete</Heading>
                      </>
                    )}
                  </HStack>
                  {!isHarvesting && (
                    <Button size="xs" variant="ghost" onClick={() => setShowLogs(false)}>
                      Dismiss
                    </Button>
                  )}
                </HStack>
              </CardHeader>
              {harvestLogs.length > 0 && (
                <CardBody pt={0}>
                  <Box
                    maxH="150px"
                    overflowY="auto"
                    bg="gray.800"
                    color="green.300"
                    p={3}
                    borderRadius="md"
                    fontFamily="mono"
                    fontSize="xs"
                  >
                    {harvestLogs.slice(-20).map((line, i) => (
                      <Text key={i} whiteSpace="pre-wrap">{line}</Text>
                    ))}
                  </Box>
                </CardBody>
              )}
            </Card>
          </Collapse>

          {/* Info Alert */}
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            <Box>
              <Text fontWeight="bold">About Spatial Filters (Context Layers)</Text>
              <Text fontSize="sm">
                Context layers are used to enrich location sites with spatial information.
                When a site is created or updated, the system performs a spatial lookup
                against these layers to determine which features contain or intersect the site.
                This data is NOT displayed in the map legend but is used for filtering and reporting.
              </Text>
            </Box>
          </Alert>

          {/* How It Works */}
          <Accordion allowToggle>
            <AccordionItem border="none">
              <AccordionButton bg={cardBg} borderRadius="md">
                <HStack flex="1">
                  <InfoIcon color="brand.500" />
                  <Text fontWeight="medium">How Spatial Filters Work</Text>
                </HStack>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel bg={cardBg} borderRadius="md" mt={1}>
                <VStack align="start" spacing={3} fontSize="sm">
                  <Text>
                    1. <strong>Upload a spatial layer</strong> using "Upload and Style Spatial Layer"
                    (e.g., catchment boundaries, protected areas, administrative regions)
                  </Text>
                  <Text>
                    2. <strong>Add it as a spatial filter</strong> here, selecting which attribute
                    contains the value you want to extract (e.g., "catchment_name", "province")
                  </Text>
                  <Text>
                    3. <strong>Run "Harvest Geocontext"</strong> to populate all existing sites
                    with the context data from this layer
                  </Text>
                  <Text>
                    4. <strong>New sites</strong> will automatically get context data when created
                  </Text>
                  <Text mt={2}>
                    <Badge colorScheme="purple">Example:</Badge> If you have a "River Catchments"
                    layer with a "name" attribute, adding it as a spatial filter will automatically
                    tag each site with the name of the catchment it falls within.
                  </Text>
                </VStack>
              </AccordionPanel>
            </AccordionItem>
          </Accordion>

          {/* Native Layer Context Groups */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Vector Layer Filters</Heading>
            </CardHeader>
            <CardBody>
              {isLoading ? (
                <HStack justify="center" py={8}>
                  <Spinner />
                  <Text>Loading...</Text>
                </HStack>
              ) : nativeLayerGroups.length === 0 ? (
                <VStack py={8} spacing={4}>
                  <Text color="gray.500">No spatial filters configured from vector layers.</Text>
                  <Button
                    colorScheme="brand"
                    leftIcon={<AddIcon />}
                    onClick={onOpen}
                    isDisabled={availableLayers.length === 0}
                  >
                    Add Your First Filter
                  </Button>
                </VStack>
              ) : (
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th width="40px">Status</Th>
                      <Th>Name</Th>
                      <Th>Source Layer</Th>
                      <Th>Attribute</Th>
                      <Th>Sites</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {nativeLayerGroups.map((group) => {
                      const [uuid, attr] = group.key?.split(':') || [];
                      const sourceLayer = availableLayers.find((l) => l.unique_id === uuid);
                      const siteCount = group.site_count || 0;
                      const hasData = siteCount > 0;
                      return (
                        <Tr key={group.id}>
                          <Td>
                            <Tooltip
                              label={
                                isHarvesting
                                  ? 'Harvesting in progress...'
                                  : hasData
                                    ? `Harvested for ${siteCount} sites`
                                    : 'Not harvested yet - run Harvest Geocontext'
                              }
                            >
                              <Box>
                                {isHarvesting ? (
                                  <Spinner size="sm" color="blue.500" />
                                ) : harvestSuccess && hasData ? (
                                  <CheckCircleIcon color="green.500" boxSize={5} />
                                ) : hasData ? (
                                  <CheckCircleIcon color="green.500" boxSize={5} />
                                ) : (
                                  <WarningIcon color="orange.400" boxSize={5} />
                                )}
                              </Box>
                            </Tooltip>
                          </Td>
                          <Td fontWeight="medium">{group.name}</Td>
                          <Td>
                            <Text fontSize="sm">{sourceLayer?.name || uuid}</Text>
                          </Td>
                          <Td>
                            <Code fontSize="sm">{attr || group.layer_identifier}</Code>
                          </Td>
                          <Td>
                            <Badge colorScheme={hasData ? 'green' : 'gray'}>{siteCount}</Badge>
                          </Td>
                          <Td>
                            <Tooltip label="Delete filter">
                              <IconButton
                                aria-label="Delete"
                                icon={<DeleteIcon />}
                                size="sm"
                                variant="ghost"
                                colorScheme="red"
                                onClick={() => handleDelete(group)}
                              />
                            </Tooltip>
                          </Td>
                        </Tr>
                      );
                    })}
                  </Tbody>
                </Table>
              )}
            </CardBody>
          </Card>

          {/* External Geocontext Groups */}
          {externalGroups.length > 0 && (
            <Card bg={cardBg}>
              <CardHeader>
                <Heading size="md">External Geocontext Services</Heading>
              </CardHeader>
              <CardBody>
                <Text fontSize="sm" color="gray.600" mb={4}>
                  These context groups fetch data from external geocontext services.
                </Text>
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>Name</Th>
                      <Th>Key</Th>
                      <Th>Sites</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {externalGroups.map((group) => (
                      <Tr key={group.id}>
                        <Td fontWeight="medium">{group.name}</Td>
                        <Td>
                          <Code fontSize="sm">{group.key}</Code>
                        </Td>
                        <Td>
                          <Badge colorScheme="gray">{group.site_count || 0}</Badge>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          )}

          {/* Available Layers */}
          {availableLayers.length > 0 && (
            <Card bg={cardBg}>
              <CardHeader>
                <Heading size="md">Available Vector Layers ({availableLayers.length})</Heading>
              </CardHeader>
              <CardBody>
                <Text fontSize="sm" color="gray.600" mb={4}>
                  These layers can be used as spatial filters.
                </Text>
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>Name</Th>
                      <Th>Attributes</Th>
                      <Th>Action</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {availableLayers.map((layer) => (
                      <Tr key={layer.unique_id}>
                        <Td fontWeight="medium">{layer.name}</Td>
                        <Td>
                          <Text fontSize="xs" color="gray.600" noOfLines={1}>
                            {layer.attributes?.join(', ') || 'No attributes'}
                          </Text>
                        </Td>
                        <Td>
                          <Button
                            size="xs"
                            colorScheme="brand"
                            leftIcon={<AddIcon />}
                            onClick={() => {
                              handleSelectLayer(layer.unique_id);
                              onOpen();
                            }}
                          >
                            Add as Filter
                          </Button>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          )}
        </VStack>
      </Container>

      {/* Add Filter Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add Spatial Filter</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Source Layer</FormLabel>
                <Select
                  placeholder="Choose a vector layer..."
                  value={selectedLayerId}
                  onChange={(e) => handleSelectLayer(e.target.value)}
                >
                  {availableLayers.map((layer) => (
                    <option key={layer.unique_id} value={layer.unique_id}>
                      {layer.name}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <FormControl isRequired isDisabled={!selectedLayerId}>
                <FormLabel>Attribute to Extract</FormLabel>
                <Select
                  placeholder="Choose an attribute..."
                  value={selectedAttribute}
                  onChange={(e) => setSelectedAttribute(e.target.value)}
                >
                  {layerAttributes.map((attr) => (
                    <option key={attr} value={attr}>
                      {attr}
                    </option>
                  ))}
                </Select>
                <FormHelperText>
                  This attribute's value will be stored for each site that intersects a feature.
                </FormHelperText>
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Filter Name</FormLabel>
                <Input
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  placeholder="e.g., Catchment, Province, Protected Area"
                />
                <FormHelperText>
                  A descriptive name for this context data (shown in reports and filters).
                </FormHelperText>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
              onClick={handleSave}
              isLoading={isSaving}
              isDisabled={!selectedLayerId || !selectedAttribute || !groupName.trim()}
            >
              Add Filter
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default SpatialFilterPage;
