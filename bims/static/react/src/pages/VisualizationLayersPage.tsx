/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Visualization Layers management page.
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
  Input,
  Select,
  Switch,
  Button,
  useToast,
  useColorModeValue,
  IconButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Divider,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SimpleGrid,
  Alert,
  AlertIcon,
  Spinner,
  Progress,
  Link,
} from '@chakra-ui/react';
import {
  AddIcon,
  EditIcon,
  DeleteIcon,
  ViewIcon,
  ViewOffIcon,
  DragHandleIcon,
  ExternalLinkIcon,
  TimeIcon,
  CheckCircleIcon,
  WarningIcon,
  CloseIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink } from 'react-router-dom';
import { useVisualizationLayersStore, VisualizationLayer } from '../stores/visualizationLayersStore';
import { apiClient } from '../api/client';

interface LayerUploadSession {
  id: number;
  layer: {
    id: number;
    unique_id: string;
    name: string;
    is_ready?: boolean;
  };
  status: 'pending' | 'processing' | 'success' | 'failed';
  progress: number;
  created_at: string;
  created_by: string;
  maputnik_url?: string;
  error_message?: string;
  status_display?: string;
  has_style?: boolean;
}

const VisualizationLayersPage: React.FC = () => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  // Use the shared store instead of local state
  const {
    layers,
    updateLayer,
    addLayer: storeAddLayer,
    deleteLayer: storeDeleteLayer,
    toggleEnabled,
    setOpacity: storeSetOpacity,
    reorderLayers,
  } = useVisualizationLayersStore();

  const [editingLayer, setEditingLayer] = useState<VisualizationLayer | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Cloud native layer upload sessions
  const [uploadSessions, setUploadSessions] = useState<LayerUploadSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [deletingSessionIds, setDeletingSessionIds] = useState<Set<number>>(new Set());
  const [isClearingFailed, setIsClearingFailed] = useState(false);

  // Published visualization layers from API
  interface PublishedLayer {
    id: number;
    name: string;
    default_visibility: boolean;
    native_layer?: {
      id: number;
      unique_id: string;
      name: string;
      maputnik_url?: string;
    };
  }
  const [publishedLayers, setPublishedLayers] = useState<PublishedLayer[]>([]);
  const [isLoadingPublished, setIsLoadingPublished] = useState(true);
  const [renamingLayerId, setRenamingLayerId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [isSavingRename, setIsSavingRename] = useState(false);
  const [unpublishingIds, setUnpublishingIds] = useState<Set<number>>(new Set());

  // Fetch upload sessions
  const fetchUploadSessions = useCallback(async () => {
    try {
      const response = await apiClient.get<{ data: LayerUploadSession[] }>(
        'spatial-layers/upload-sessions/'
      );
      setUploadSessions(response.data?.data || []);
    } catch (error) {
      console.error('Failed to fetch upload sessions:', error);
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  // Fetch published visualization layers
  const fetchPublishedLayers = useCallback(async () => {
    try {
      const response = await apiClient.get<{ data: PublishedLayer[] }>(
        'visualization-layers/'
      );
      setPublishedLayers(response.data?.data || []);
    } catch (error) {
      console.error('Failed to fetch published layers:', error);
    } finally {
      setIsLoadingPublished(false);
    }
  }, []);

  // Rename a published layer
  const handleStartRename = (layer: PublishedLayer) => {
    setRenamingLayerId(layer.id);
    setRenameValue(layer.name);
  };

  const handleCancelRename = () => {
    setRenamingLayerId(null);
    setRenameValue('');
  };

  const handleSaveRename = async (layerId: number) => {
    if (!renameValue.trim()) {
      toast({
        title: 'Name required',
        description: 'Layer name cannot be empty.',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setIsSavingRename(true);
    try {
      await apiClient.patch(`visualization-layers/${layerId}/`, {
        name: renameValue.trim(),
      });
      toast({
        title: 'Layer renamed',
        status: 'success',
        duration: 3000,
      });
      setRenamingLayerId(null);
      setRenameValue('');
      await fetchPublishedLayers();
    } catch (error: any) {
      toast({
        title: 'Rename failed',
        description: error.response?.data?.message || 'Failed to rename layer.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSavingRename(false);
    }
  };

  // Unpublish a visualization layer
  const handleUnpublish = async (layerId: number, layerName: string) => {
    if (!confirm(`Are you sure you want to unpublish "${layerName}"? The source layer will remain available for re-publishing.`)) {
      return;
    }

    setUnpublishingIds((prev) => new Set(prev).add(layerId));
    try {
      await apiClient.delete(`visualization-layers/${layerId}/`);
      toast({
        title: 'Layer unpublished',
        description: `"${layerName}" has been removed from the map.`,
        status: 'success',
        duration: 3000,
      });
      await fetchPublishedLayers();
    } catch (error: any) {
      toast({
        title: 'Unpublish failed',
        description: error.response?.data?.message || 'Failed to unpublish layer.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setUnpublishingIds((prev) => {
        const next = new Set(prev);
        next.delete(layerId);
        return next;
      });
    }
  };

  // Check if there are processing sessions
  const hasProcessingSessions = uploadSessions.some(
    (s) => s.status === 'pending' || s.status === 'processing'
  );

  // Check if there are failed sessions
  const hasFailedSessions = uploadSessions.some((s) => s.status === 'failed');

  // Delete a single upload session
  const handleDeleteSession = async (sessionId: number, layerName: string) => {
    if (!confirm(`Are you sure you want to delete "${layerName}"? This cannot be undone.`)) {
      return;
    }

    setDeletingSessionIds((prev) => new Set(prev).add(sessionId));

    try {
      await apiClient.delete(`spatial-layers/${sessionId}/`);
      toast({
        title: 'Session deleted',
        description: `"${layerName}" has been removed.`,
        status: 'success',
        duration: 3000,
      });
      await fetchUploadSessions();
    } catch (error: any) {
      toast({
        title: 'Delete failed',
        description: error.response?.data?.message || 'Failed to delete session.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setDeletingSessionIds((prev) => {
        const next = new Set(prev);
        next.delete(sessionId);
        return next;
      });
    }
  };

  // Clear all failed upload sessions
  const handleClearAllFailed = async () => {
    const failedCount = uploadSessions.filter((s) => s.status === 'failed').length;
    if (!confirm(`Are you sure you want to delete all ${failedCount} failed upload(s)? This cannot be undone.`)) {
      return;
    }

    setIsClearingFailed(true);

    try {
      const response = await apiClient.delete<{ message: string; count: number }>(
        'spatial-layers/clear-failed/'
      );
      toast({
        title: 'Failed sessions cleared',
        description: response.data?.message || 'All failed sessions removed.',
        status: 'success',
        duration: 3000,
      });
      await fetchUploadSessions();
    } catch (error: any) {
      toast({
        title: 'Clear failed',
        description: error.response?.data?.message || 'Failed to clear sessions.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsClearingFailed(false);
    }
  };

  useEffect(() => {
    fetchUploadSessions();
    fetchPublishedLayers();
    // Poll more frequently when processing
    const pollInterval = hasProcessingSessions ? 2000 : 10000;
    const interval = setInterval(fetchUploadSessions, pollInterval);
    return () => clearInterval(interval);
  }, [fetchUploadSessions, fetchPublishedLayers, hasProcessingSessions]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge colorScheme="green"><CheckCircleIcon mr={1} />Ready</Badge>;
      case 'processing':
        return <Badge colorScheme="blue"><TimeIcon mr={1} />Processing</Badge>;
      case 'failed':
        return <Badge colorScheme="red"><WarningIcon mr={1} />Failed</Badge>;
      default:
        return <Badge colorScheme="gray"><TimeIcon mr={1} />Pending</Badge>;
    }
  };

  const toggleLayer = (id: string) => {
    toggleEnabled(id);
  };

  const updateOpacity = (id: string, opacity: number) => {
    storeSetOpacity(id, opacity);
  };

  const openEditModal = (layer: VisualizationLayer) => {
    setEditingLayer({ ...layer });
    setIsEditing(true);
    onOpen();
  };

  const openAddModal = () => {
    setEditingLayer({
      id: '',
      name: '',
      type: 'point',
      source: '',
      enabled: true,
      visible: false,
      opacity: 100,
      minZoom: 0,
      maxZoom: 22,
      style: { color: '#3182CE', fillColor: '#3182CE', radius: 6 },
      order: layers.length + 1,
    });
    setIsEditing(false);
    onOpen();
  };

  const saveLayer = () => {
    if (!editingLayer) return;

    if (isEditing) {
      updateLayer(editingLayer.id, editingLayer);
      toast({
        title: 'Layer updated',
        status: 'success',
        duration: 3000,
      });
    } else {
      storeAddLayer({
        ...editingLayer,
        visible: false,
      });
      toast({
        title: 'Layer added',
        status: 'success',
        duration: 3000,
      });
    }
    onClose();
  };

  const deleteLayer = (id: string) => {
    storeDeleteLayer(id);
    toast({
      title: 'Layer deleted',
      status: 'info',
      duration: 3000,
    });
  };

  const getTypeColor = (type: VisualizationLayer['type']) => {
    switch (type) {
      case 'point':
        return 'blue';
      case 'polygon':
        return 'green';
      case 'heatmap':
        return 'red';
      case 'cluster':
        return 'purple';
      default:
        return 'gray';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Custom Vector Layers</Heading>
              <Text opacity={0.9}>
                Upload shapefiles and create custom-styled vector tile layers
              </Text>
            </VStack>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack spacing={6} align="stretch">
          {/* Cloud Native Layer Upload Status */}
          {uploadSessions.length > 0 && (
            <Card bg={cardBg}>
              <CardHeader>
                <HStack justify="space-between">
                  <HStack>
                    {hasProcessingSessions && <Spinner size="sm" />}
                    <Heading size="md">Spatial Layer Status</Heading>
                  </HStack>
                  <HStack spacing={2}>
                    {hasFailedSessions && (
                      <Button
                        size="sm"
                        colorScheme="red"
                        variant="outline"
                        leftIcon={<DeleteIcon />}
                        onClick={handleClearAllFailed}
                        isLoading={isClearingFailed}
                        loadingText="Clearing..."
                      >
                        Clear All Failed
                      </Button>
                    )}
                    <Button
                      as={RouterLink}
                      to="/admin/spatial-upload"
                      size="sm"
                      colorScheme="brand"
                      leftIcon={<AddIcon />}
                    >
                      Upload New Layer
                    </Button>
                  </HStack>
                </HStack>
              </CardHeader>
              <CardBody>
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>Layer Name</Th>
                      <Th>Status</Th>
                      <Th>Style</Th>
                      <Th>Progress</Th>
                      <Th>Uploaded</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {uploadSessions.map((session) => (
                      <Tr
                        key={session.id}
                        bg={
                          session.status === 'processing' || session.status === 'pending'
                            ? 'blue.50'
                            : session.status === 'failed'
                            ? 'red.50'
                            : undefined
                        }
                      >
                        <Td fontWeight="medium">{session.layer.name}</Td>
                        <Td>{getStatusBadge(session.status)}</Td>
                        <Td>
                          {session.status === 'success' && (
                            session.has_style ? (
                              <Badge colorScheme="green">Styled</Badge>
                            ) : (
                              <Badge colorScheme="orange">No Style</Badge>
                            )
                          )}
                        </Td>
                        <Td width="150px">
                          {session.status === 'processing' || session.status === 'pending' ? (
                            <Progress
                              value={session.progress || 0}
                              size="sm"
                              colorScheme="blue"
                              borderRadius="md"
                              isIndeterminate={!session.progress || session.progress === 0}
                              hasStripe
                              isAnimated
                            />
                          ) : session.status === 'success' ? (
                            <Text fontSize="sm" color="green.600">Complete</Text>
                          ) : (
                            <Text fontSize="sm" color="red.600">-</Text>
                          )}
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.600">
                            {new Date(session.created_at).toLocaleDateString()}
                          </Text>
                        </Td>
                        <Td>
                          <HStack spacing={2}>
                            {session.status === 'success' && session.maputnik_url && (
                              <Button
                                as={Link}
                                href={session.maputnik_url}
                                isExternal
                                size="xs"
                                colorScheme={session.has_style ? 'purple' : 'orange'}
                                leftIcon={session.has_style ? <EditIcon /> : <AddIcon />}
                              >
                                {session.has_style ? 'Edit Style' : 'Create Style'}
                              </Button>
                            )}
                            {session.status === 'failed' && session.error_message && (
                              <Text fontSize="xs" color="red.600" maxW="200px" noOfLines={2}>
                                {session.error_message}
                              </Text>
                            )}
                            {(session.status === 'failed' || session.status === 'success') && (
                              <IconButton
                                aria-label="Delete layer"
                                icon={<DeleteIcon />}
                                size="xs"
                                colorScheme="red"
                                variant="ghost"
                                onClick={() => handleDeleteSession(session.id, session.layer.name)}
                                isLoading={deletingSessionIds.has(session.id)}
                              />
                            )}
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          )}

          {/* Empty state for upload sessions */}
          {!isLoadingSessions && uploadSessions.length === 0 && (
            <Alert status="info" borderRadius="md">
              <AlertIcon />
              <HStack justify="space-between" w="100%">
                <Text>
                  No spatial layers uploaded yet. Upload shapefiles to create styled vector tile layers.
                </Text>
                <Button
                  as={RouterLink}
                  to="/admin/spatial-upload"
                  size="sm"
                  colorScheme="brand"
                  leftIcon={<AddIcon />}
                >
                  Upload Layer
                </Button>
              </HStack>
            </Alert>
          )}

          <Divider />

          {/* Published Visualization Layers */}
          {publishedLayers.length > 0 && (
            <Card bg={cardBg}>
              <CardHeader>
                <Heading size="md">Published Map Layers</Heading>
                <Text fontSize="sm" color="gray.500" mt={1}>
                  These layers appear on the map and can be toggled by users.
                </Text>
              </CardHeader>
              <CardBody>
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th>Layer Name</Th>
                      <Th>Source Layer</Th>
                      <Th>Visible</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {publishedLayers.map((layer) => (
                      <Tr key={layer.id}>
                        <Td>
                          {renamingLayerId === layer.id ? (
                            <HStack>
                              <Input
                                size="sm"
                                value={renameValue}
                                onChange={(e) => setRenameValue(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') handleSaveRename(layer.id);
                                  if (e.key === 'Escape') handleCancelRename();
                                }}
                                autoFocus
                              />
                              <IconButton
                                aria-label="Save"
                                icon={<CheckCircleIcon />}
                                size="sm"
                                colorScheme="green"
                                onClick={() => handleSaveRename(layer.id)}
                                isLoading={isSavingRename}
                              />
                              <IconButton
                                aria-label="Cancel"
                                icon={<CloseIcon />}
                                size="sm"
                                variant="ghost"
                                onClick={handleCancelRename}
                              />
                            </HStack>
                          ) : (
                            <Text
                              fontWeight="medium"
                              cursor="pointer"
                              _hover={{ color: 'brand.500' }}
                              onClick={() => handleStartRename(layer)}
                            >
                              {layer.name}
                            </Text>
                          )}
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.600">
                            {layer.native_layer?.name || 'N/A'}
                          </Text>
                        </Td>
                        <Td>
                          <Badge colorScheme={layer.default_visibility ? 'green' : 'gray'}>
                            {layer.default_visibility ? 'On' : 'Off'}
                          </Badge>
                        </Td>
                        <Td>
                          <HStack spacing={2}>
                            <IconButton
                              aria-label="Rename layer"
                              icon={<EditIcon />}
                              size="xs"
                              variant="ghost"
                              onClick={() => handleStartRename(layer)}
                            />
                            <IconButton
                              aria-label="Unpublish layer"
                              icon={<DeleteIcon />}
                              size="xs"
                              colorScheme="red"
                              variant="ghost"
                              onClick={() => handleUnpublish(layer.id, layer.name)}
                              isLoading={unpublishingIds.has(layer.id)}
                            />
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          )}

          {!isLoadingPublished && publishedLayers.length === 0 && (
            <Alert status="info" borderRadius="md">
              <AlertIcon />
              No layers published to the map yet. Upload and style a spatial layer, then publish it to make it available on the map.
            </Alert>
          )}

          <Divider />

        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Site Layers</Heading>
            <Text fontSize="sm" color="gray.500" mt={1}>
              Configure how biodiversity site data is displayed on the map.
            </Text>
          </CardHeader>
          <CardBody>
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th width="40px"></Th>
                  <Th>Name</Th>
                  <Th>Type</Th>
                  <Th>Source</Th>
                  <Th>Opacity</Th>
                  <Th>Zoom Range</Th>
                  <Th>Enabled</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {layers
                  .sort((a, b) => a.order - b.order)
                  .map((layer) => (
                    <Tr key={layer.id} opacity={layer.enabled ? 1 : 0.6}>
                      <Td>
                        <IconButton
                          aria-label="Drag to reorder"
                          icon={<DragHandleIcon />}
                          size="sm"
                          variant="ghost"
                          cursor="grab"
                        />
                      </Td>
                      <Td>
                        <HStack>
                          <Box
                            w={3}
                            h={3}
                            borderRadius="full"
                            bg={layer.style.color}
                          />
                          <Text fontWeight="medium">{layer.name}</Text>
                        </HStack>
                      </Td>
                      <Td>
                        <Badge colorScheme={getTypeColor(layer.type)}>
                          {layer.type}
                        </Badge>
                      </Td>
                      <Td>
                        <Text fontSize="sm" color="gray.500">
                          {layer.source}
                        </Text>
                      </Td>
                      <Td width="150px">
                        <HStack>
                          <Slider
                            value={layer.opacity}
                            onChange={(val) => updateOpacity(layer.id, val)}
                            min={0}
                            max={100}
                            step={10}
                            width="80px"
                          >
                            <SliderTrack>
                              <SliderFilledTrack bg="brand.500" />
                            </SliderTrack>
                            <SliderThumb />
                          </Slider>
                          <Text fontSize="sm" width="40px">
                            {layer.opacity}%
                          </Text>
                        </HStack>
                      </Td>
                      <Td>
                        <Text fontSize="sm">
                          {layer.minZoom} - {layer.maxZoom}
                        </Text>
                      </Td>
                      <Td>
                        <Switch
                          isChecked={layer.enabled}
                          onChange={() => toggleLayer(layer.id)}
                          colorScheme="brand"
                        />
                      </Td>
                      <Td>
                        <HStack spacing={1}>
                          <IconButton
                            aria-label="Edit layer"
                            icon={<EditIcon />}
                            size="sm"
                            variant="ghost"
                            onClick={() => openEditModal(layer)}
                          />
                          <IconButton
                            aria-label="Delete layer"
                            icon={<DeleteIcon />}
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => deleteLayer(layer.id)}
                          />
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
              </Tbody>
            </Table>
          </CardBody>
        </Card>
        </VStack>
      </Container>

      {/* Edit/Add Layer Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {isEditing ? 'Edit Layer' : 'Add New Layer'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {editingLayer && (
              <VStack spacing={4} align="stretch">
                <FormControl isRequired>
                  <FormLabel>Layer Name</FormLabel>
                  <Input
                    value={editingLayer.name}
                    onChange={(e) =>
                      setEditingLayer((prev) =>
                        prev ? { ...prev, name: e.target.value } : null
                      )
                    }
                    placeholder="Enter layer name"
                  />
                </FormControl>

                <SimpleGrid columns={2} spacing={4}>
                  <FormControl isRequired>
                    <FormLabel>Layer Type</FormLabel>
                    <Select
                      value={editingLayer.type}
                      onChange={(e) =>
                        setEditingLayer((prev) =>
                          prev
                            ? {
                                ...prev,
                                type: e.target.value as VisualizationLayer['type'],
                              }
                            : null
                        )
                      }
                    >
                      <option value="point">Point</option>
                      <option value="polygon">Polygon</option>
                      <option value="heatmap">Heatmap</option>
                      <option value="cluster">Cluster</option>
                    </Select>
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel>Data Source</FormLabel>
                    <Select
                      value={editingLayer.source}
                      onChange={(e) =>
                        setEditingLayer((prev) =>
                          prev ? { ...prev, source: e.target.value } : null
                        )
                      }
                    >
                      <option value="sites">Location Sites</option>
                      <option value="fish_records">Fish Records</option>
                      <option value="invertebrate_records">Invertebrate Records</option>
                      <option value="all_records">All Records</option>
                      <option value="catchments">Catchments</option>
                      <option value="boundaries">Boundaries</option>
                    </Select>
                  </FormControl>
                </SimpleGrid>

                <Divider />

                <Heading size="sm">Styling</Heading>

                <SimpleGrid columns={2} spacing={4}>
                  <FormControl>
                    <FormLabel>Primary Color</FormLabel>
                    <Input
                      type="color"
                      value={editingLayer.style.color}
                      onChange={(e) =>
                        setEditingLayer((prev) =>
                          prev
                            ? {
                                ...prev,
                                style: { ...prev.style, color: e.target.value },
                              }
                            : null
                        )
                      }
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Fill Color</FormLabel>
                    <Input
                      type="color"
                      value={editingLayer.style.fillColor || editingLayer.style.color}
                      onChange={(e) =>
                        setEditingLayer((prev) =>
                          prev
                            ? {
                                ...prev,
                                style: { ...prev.style, fillColor: e.target.value },
                              }
                            : null
                        )
                      }
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Min Zoom</FormLabel>
                    <Select
                      value={editingLayer.minZoom}
                      onChange={(e) =>
                        setEditingLayer((prev) =>
                          prev ? { ...prev, minZoom: parseInt(e.target.value) } : null
                        )
                      }
                    >
                      {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((z) => (
                        <option key={z} value={z}>
                          {z}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl>
                    <FormLabel>Max Zoom</FormLabel>
                    <Select
                      value={editingLayer.maxZoom}
                      onChange={(e) =>
                        setEditingLayer((prev) =>
                          prev ? { ...prev, maxZoom: parseInt(e.target.value) } : null
                        )
                      }
                    >
                      {[10, 12, 14, 16, 18, 20, 22].map((z) => (
                        <option key={z} value={z}>
                          {z}
                        </option>
                      ))}
                    </Select>
                  </FormControl>
                </SimpleGrid>

                <FormControl>
                  <FormLabel>Opacity: {editingLayer.opacity}%</FormLabel>
                  <Slider
                    value={editingLayer.opacity}
                    onChange={(val) =>
                      setEditingLayer((prev) =>
                        prev ? { ...prev, opacity: val } : null
                      )
                    }
                    min={0}
                    max={100}
                    step={5}
                  >
                    <SliderTrack>
                      <SliderFilledTrack bg="brand.500" />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                </FormControl>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="brand" onClick={saveLayer}>
              {isEditing ? 'Save Changes' : 'Add Layer'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default VisualizationLayersPage;
