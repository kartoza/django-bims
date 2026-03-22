/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Publish Spatial Layer on Map page.
 * Allows adding cloud native GIS layers as visualization layers on the map.
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
  Select,
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
  Input,
  Tooltip,
  Switch,
  Link,
} from '@chakra-ui/react';
import {
  AddIcon,
  DeleteIcon,
  ExternalLinkIcon,
  ViewIcon,
  ViewOffIcon,
  EditIcon,
  ChevronUpIcon,
  ChevronDownIcon,
} from '@chakra-ui/icons';
import { apiClient } from '../api/client';

interface CloudNativeLayer {
  id: number;
  unique_id: string;
  name: string;
  abstract?: string;
  attributes?: string[];
  default_style?: {
    id: number;
    name: string;
  };
  maputnik_url?: string;
  is_ready?: boolean;
  status?: string;
}

interface PublishedLayer {
  id: number;
  name: string;
  native_layer?: CloudNativeLayer;
  wms_url?: string;
  wms_layer_name?: string;
  order: number;
  visible: boolean;
}

const PublishSpatialLayerPage: React.FC = () => {
  const toast = useToast();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [availableLayers, setAvailableLayers] = useState<CloudNativeLayer[]>([]);
  const [publishedLayers, setPublishedLayers] = useState<PublishedLayer[]>([]);
  const [selectedLayerId, setSelectedLayerId] = useState<string>('');
  const [layerDisplayName, setLayerDisplayName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isPublishing, setIsPublishing] = useState(false);

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

  // Fetch published layers (NonBiodiversityLayer)
  const fetchPublishedLayers = useCallback(async () => {
    try {
      const response = await apiClient.get<{ data: PublishedLayer[] }>(
        'visualization-layers/'
      );
      setPublishedLayers(response.data?.data || []);
    } catch (error) {
      console.error('Failed to fetch published layers:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAvailableLayers();
    fetchPublishedLayers();
  }, [fetchAvailableLayers, fetchPublishedLayers]);

  const handleSelectLayer = (layerId: string) => {
    setSelectedLayerId(layerId);
    const layer = availableLayers.find((l) => l.unique_id === layerId);
    if (layer) {
      setLayerDisplayName(layer.name);
    }
  };

  const handlePublish = async () => {
    if (!selectedLayerId) {
      toast({
        title: 'Select a layer',
        description: 'Please select a layer to publish.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsPublishing(true);

    try {
      await apiClient.post('visualization-layers/', {
        native_layer_uuid: selectedLayerId,
        name: layerDisplayName,
      });

      toast({
        title: 'Layer published',
        description: 'The layer has been added to the map.',
        status: 'success',
        duration: 3000,
      });

      onClose();
      setSelectedLayerId('');
      setLayerDisplayName('');
      fetchPublishedLayers();
    } catch (error: any) {
      toast({
        title: 'Failed to publish',
        description: error.response?.data?.message || 'Failed to publish layer.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsPublishing(false);
    }
  };

  const handleToggleVisibility = async (layer: PublishedLayer) => {
    try {
      await apiClient.patch(`visualization-layers/${layer.id}/`, {
        visible: !layer.visible,
      });
      fetchPublishedLayers();
    } catch (error) {
      toast({
        title: 'Failed to update',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleMoveUp = async (layer: PublishedLayer) => {
    try {
      await apiClient.post(`visualization-layers/${layer.id}/move-up/`);
      fetchPublishedLayers();
    } catch (error) {
      toast({
        title: 'Failed to reorder',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleMoveDown = async (layer: PublishedLayer) => {
    try {
      await apiClient.post(`visualization-layers/${layer.id}/move-down/`);
      fetchPublishedLayers();
    } catch (error) {
      toast({
        title: 'Failed to reorder',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleDelete = async (layer: PublishedLayer) => {
    if (!confirm(`Are you sure you want to remove "${layer.name}" from the map?`)) {
      return;
    }

    try {
      await apiClient.delete(`visualization-layers/${layer.id}/`);
      toast({
        title: 'Layer removed',
        status: 'success',
        duration: 3000,
      });
      fetchPublishedLayers();
    } catch (error) {
      toast({
        title: 'Failed to remove',
        status: 'error',
        duration: 3000,
      });
    }
  };

  // Filter out already published layers
  const unpublishedLayers = availableLayers.filter(
    (al) => !publishedLayers.some((pl) => pl.native_layer?.unique_id === al.unique_id)
  );

  return (
    <Box h="100%" overflowY="auto">
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <HStack>
                <ViewIcon />
                <Heading size="lg">Publish Spatial Layer on Map</Heading>
              </HStack>
              <Text opacity={0.9}>
                Add styled vector tile layers to the map as visualization layers
              </Text>
            </VStack>
            <Button
              colorScheme="whiteAlpha"
              leftIcon={<AddIcon />}
              onClick={onOpen}
              isDisabled={unpublishedLayers.length === 0}
            >
              Add Layer
            </Button>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* Info Alert */}
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            <Box>
              <Text fontWeight="bold">About Visualization Layers</Text>
              <Text fontSize="sm">
                Visualization layers appear in the map legend and can be toggled on/off by users.
                They are displayed on top of the base map but below biodiversity data points.
              </Text>
            </Box>
          </Alert>

          {/* Published Layers Table */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Published Layers</Heading>
            </CardHeader>
            <CardBody>
              {isLoading ? (
                <HStack justify="center" py={8}>
                  <Spinner />
                  <Text>Loading layers...</Text>
                </HStack>
              ) : publishedLayers.length === 0 ? (
                <VStack py={8} spacing={4}>
                  <Text color="gray.500">No layers published yet.</Text>
                  <Button
                    colorScheme="brand"
                    leftIcon={<AddIcon />}
                    onClick={onOpen}
                    isDisabled={unpublishedLayers.length === 0}
                  >
                    Add Your First Layer
                  </Button>
                </VStack>
              ) : (
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Order</Th>
                      <Th>Name</Th>
                      <Th>Type</Th>
                      <Th>Visible</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {publishedLayers
                      .sort((a, b) => a.order - b.order)
                      .map((layer, index) => (
                        <Tr key={layer.id}>
                          <Td>
                            <HStack spacing={1}>
                              <IconButton
                                aria-label="Move up"
                                icon={<ChevronUpIcon />}
                                size="xs"
                                variant="ghost"
                                isDisabled={index === 0}
                                onClick={() => handleMoveUp(layer)}
                              />
                              <IconButton
                                aria-label="Move down"
                                icon={<ChevronDownIcon />}
                                size="xs"
                                variant="ghost"
                                isDisabled={index === publishedLayers.length - 1}
                                onClick={() => handleMoveDown(layer)}
                              />
                            </HStack>
                          </Td>
                          <Td fontWeight="medium">{layer.name}</Td>
                          <Td>
                            {layer.native_layer ? (
                              <Badge colorScheme="purple">Vector Tiles</Badge>
                            ) : layer.wms_url ? (
                              <Badge colorScheme="blue">WMS</Badge>
                            ) : (
                              <Badge>Unknown</Badge>
                            )}
                          </Td>
                          <Td>
                            <Switch
                              isChecked={layer.visible}
                              onChange={() => handleToggleVisibility(layer)}
                              colorScheme="green"
                            />
                          </Td>
                          <Td>
                            <HStack spacing={2}>
                              {layer.native_layer?.maputnik_url && (
                                <Tooltip label="Edit Style in Maputnik">
                                  <IconButton
                                    as={Link}
                                    href={layer.native_layer.maputnik_url}
                                    isExternal
                                    aria-label="Edit style"
                                    icon={<EditIcon />}
                                    size="sm"
                                    variant="ghost"
                                    colorScheme="purple"
                                  />
                                </Tooltip>
                              )}
                              <Tooltip label="Remove from map">
                                <IconButton
                                  aria-label="Delete"
                                  icon={<DeleteIcon />}
                                  size="sm"
                                  variant="ghost"
                                  colorScheme="red"
                                  onClick={() => handleDelete(layer)}
                                />
                              </Tooltip>
                            </HStack>
                          </Td>
                        </Tr>
                      ))}
                  </Tbody>
                </Table>
              )}
            </CardBody>
          </Card>

          {/* Available Layers */}
          {unpublishedLayers.length > 0 && (
            <Card bg={cardBg}>
              <CardHeader>
                <Heading size="md">Available Layers ({unpublishedLayers.length})</Heading>
              </CardHeader>
              <CardBody>
                <Text fontSize="sm" color="gray.600" mb={4}>
                  These layers have been uploaded but not yet published to the map.
                </Text>
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>Name</Th>
                      <Th>Status</Th>
                      <Th>Description</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {unpublishedLayers.map((layer) => (
                      <Tr key={layer.unique_id} opacity={layer.is_ready ? 1 : 0.7}>
                        <Td fontWeight="medium">{layer.name}</Td>
                        <Td>
                          {layer.is_ready ? (
                            <Badge colorScheme="green">Ready</Badge>
                          ) : (
                            <Badge colorScheme="blue">Processing</Badge>
                          )}
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.600" noOfLines={1}>
                            {layer.abstract || '-'}
                          </Text>
                        </Td>
                        <Td>
                          <HStack spacing={2}>
                            {layer.is_ready && layer.maputnik_url && (
                              <Button
                                as={Link}
                                href={layer.maputnik_url}
                                isExternal
                                size="xs"
                                variant="outline"
                                colorScheme="purple"
                                leftIcon={<ExternalLinkIcon />}
                              >
                                Style
                              </Button>
                            )}
                            <Button
                              size="xs"
                              colorScheme="brand"
                              leftIcon={<AddIcon />}
                              onClick={() => {
                                handleSelectLayer(layer.unique_id);
                                onOpen();
                              }}
                              isDisabled={!layer.is_ready}
                            >
                              Publish
                            </Button>
                          </HStack>
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

      {/* Add Layer Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Publish Layer to Map</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Select Layer</FormLabel>
                <Select
                  placeholder="Choose a layer..."
                  value={selectedLayerId}
                  onChange={(e) => handleSelectLayer(e.target.value)}
                >
                  {unpublishedLayers.map((layer) => (
                    <option key={layer.unique_id} value={layer.unique_id}>
                      {layer.name}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Display Name</FormLabel>
                <Input
                  value={layerDisplayName}
                  onChange={(e) => setLayerDisplayName(e.target.value)}
                  placeholder="Name shown in map legend"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
              onClick={handlePublish}
              isLoading={isPublishing}
              isDisabled={!selectedLayerId || !layerDisplayName.trim()}
            >
              Publish to Map
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default PublishSpatialLayerPage;
