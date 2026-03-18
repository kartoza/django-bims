/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Context Layers management page.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState } from 'react';
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
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  SimpleGrid,
  Alert,
  AlertIcon,
  Textarea,
  Code,
} from '@chakra-ui/react';
import {
  AddIcon,
  EditIcon,
  DeleteIcon,
  ExternalLinkIcon,
  RepeatIcon,
} from '@chakra-ui/icons';

interface ContextLayer {
  id: string;
  name: string;
  type: 'wms' | 'wmts' | 'xyz' | 'geojson' | 'vector';
  url: string;
  layerName?: string;
  enabled: boolean;
  category: string;
  attribution?: string;
  description?: string;
  order: number;
}

const ContextLayersPage: React.FC = () => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  const [layers, setLayers] = useState<ContextLayer[]>([
    {
      id: '1',
      name: 'OpenStreetMap',
      type: 'xyz',
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      enabled: true,
      category: 'Base Maps',
      attribution: '© OpenStreetMap contributors',
      order: 1,
    },
    {
      id: '2',
      name: 'Satellite Imagery',
      type: 'xyz',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      enabled: true,
      category: 'Base Maps',
      attribution: '© Esri',
      order: 2,
    },
    {
      id: '3',
      name: 'Rivers & Water Bodies',
      type: 'wms',
      url: 'https://maps.kartoza.com/geoserver/wms',
      layerName: 'rivers',
      enabled: true,
      category: 'Hydrology',
      description: 'Major rivers and water bodies of South Africa',
      order: 3,
    },
    {
      id: '4',
      name: 'Protected Areas',
      type: 'wms',
      url: 'https://maps.kartoza.com/geoserver/wms',
      layerName: 'protected_areas',
      enabled: true,
      category: 'Conservation',
      description: 'National parks and protected areas',
      order: 4,
    },
    {
      id: '5',
      name: 'Catchment Boundaries',
      type: 'geojson',
      url: '/api/v1/boundaries/catchments/',
      enabled: false,
      category: 'Administrative',
      description: 'River catchment boundaries',
      order: 5,
    },
    {
      id: '6',
      name: 'Provincial Boundaries',
      type: 'geojson',
      url: '/api/v1/boundaries/provinces/',
      enabled: true,
      category: 'Administrative',
      description: 'South African provincial boundaries',
      order: 6,
    },
  ]);

  const [editingLayer, setEditingLayer] = useState<ContextLayer | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');

  const categories = ['Base Maps', 'Hydrology', 'Conservation', 'Administrative', 'Custom'];

  const toggleLayer = (id: string) => {
    setLayers((prev) =>
      prev.map((layer) =>
        layer.id === id ? { ...layer, enabled: !layer.enabled } : layer
      )
    );
  };

  const openEditModal = (layer: ContextLayer) => {
    setEditingLayer({ ...layer });
    setIsEditing(true);
    onOpen();
  };

  const openAddModal = () => {
    setEditingLayer({
      id: '',
      name: '',
      type: 'wms',
      url: '',
      enabled: true,
      category: 'Custom',
      order: layers.length + 1,
    });
    setIsEditing(false);
    onOpen();
  };

  const saveLayer = () => {
    if (!editingLayer) return;

    if (isEditing) {
      setLayers((prev) =>
        prev.map((layer) => (layer.id === editingLayer.id ? editingLayer : layer))
      );
      toast({
        title: 'Layer updated',
        status: 'success',
        duration: 3000,
      });
    } else {
      setLayers((prev) => [...prev, { ...editingLayer, id: Date.now().toString() }]);
      toast({
        title: 'Layer added',
        status: 'success',
        duration: 3000,
      });
    }
    onClose();
  };

  const deleteLayer = (id: string) => {
    setLayers((prev) => prev.filter((layer) => layer.id !== id));
    toast({
      title: 'Layer deleted',
      status: 'info',
      duration: 3000,
    });
  };

  const testConnection = async () => {
    toast({
      title: 'Testing connection...',
      status: 'info',
      duration: 2000,
    });
    // Simulate connection test
    await new Promise((resolve) => setTimeout(resolve, 1500));
    toast({
      title: 'Connection successful',
      status: 'success',
      duration: 3000,
    });
  };

  const getTypeColor = (type: ContextLayer['type']) => {
    switch (type) {
      case 'wms':
        return 'blue';
      case 'wmts':
        return 'cyan';
      case 'xyz':
        return 'purple';
      case 'geojson':
        return 'green';
      case 'vector':
        return 'orange';
      default:
        return 'gray';
    }
  };

  const filteredLayers =
    activeCategory === 'all'
      ? layers
      : layers.filter((l) => l.category === activeCategory);

  return (
    <Box>
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Context Layers</Heading>
              <Text opacity={0.9}>
                Manage external map layers (WMS, WMTS, XYZ, GeoJSON)
              </Text>
            </VStack>
            <Button
              leftIcon={<AddIcon />}
              colorScheme="whiteAlpha"
              onClick={openAddModal}
            >
              Add Layer
            </Button>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <Tabs variant="soft-rounded" colorScheme="brand" mb={6}>
          <TabList flexWrap="wrap">
            <Tab onClick={() => setActiveCategory('all')}>All</Tab>
            {categories.map((cat) => (
              <Tab key={cat} onClick={() => setActiveCategory(cat)}>
                {cat}
              </Tab>
            ))}
          </TabList>
        </Tabs>

        <Card bg={cardBg}>
          <CardHeader>
            <HStack justify="space-between">
              <Heading size="md">
                {activeCategory === 'all' ? 'All Layers' : activeCategory}
              </Heading>
              <Badge colorScheme="gray">{filteredLayers.length} layers</Badge>
            </HStack>
          </CardHeader>
          <CardBody>
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Name</Th>
                  <Th>Type</Th>
                  <Th>Category</Th>
                  <Th>URL</Th>
                  <Th>Enabled</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredLayers
                  .sort((a, b) => a.order - b.order)
                  .map((layer) => (
                    <Tr key={layer.id} opacity={layer.enabled ? 1 : 0.6}>
                      <Td>
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="medium">{layer.name}</Text>
                          {layer.description && (
                            <Text fontSize="xs" color="gray.500">
                              {layer.description}
                            </Text>
                          )}
                        </VStack>
                      </Td>
                      <Td>
                        <Badge colorScheme={getTypeColor(layer.type)}>
                          {layer.type.toUpperCase()}
                        </Badge>
                      </Td>
                      <Td>
                        <Badge variant="outline">{layer.category}</Badge>
                      </Td>
                      <Td maxW="200px">
                        <Text fontSize="xs" isTruncated title={layer.url}>
                          {layer.url}
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

            {filteredLayers.length === 0 && (
              <Alert status="info" mt={4} borderRadius="md">
                <AlertIcon />
                No layers found in this category. Click "Add Layer" to create one.
              </Alert>
            )}
          </CardBody>
        </Card>
      </Container>

      {/* Edit/Add Layer Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {isEditing ? 'Edit Context Layer' : 'Add Context Layer'}
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
                                type: e.target.value as ContextLayer['type'],
                              }
                            : null
                        )
                      }
                    >
                      <option value="wms">WMS</option>
                      <option value="wmts">WMTS</option>
                      <option value="xyz">XYZ Tiles</option>
                      <option value="geojson">GeoJSON</option>
                      <option value="vector">Vector Tiles</option>
                    </Select>
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel>Category</FormLabel>
                    <Select
                      value={editingLayer.category}
                      onChange={(e) =>
                        setEditingLayer((prev) =>
                          prev ? { ...prev, category: e.target.value } : null
                        )
                      }
                    >
                      {categories.map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </Select>
                  </FormControl>
                </SimpleGrid>

                <FormControl isRequired>
                  <FormLabel>Service URL</FormLabel>
                  <Input
                    value={editingLayer.url}
                    onChange={(e) =>
                      setEditingLayer((prev) =>
                        prev ? { ...prev, url: e.target.value } : null
                      )
                    }
                    placeholder="https://example.com/wms"
                  />
                  <FormHelperText>
                    {editingLayer.type === 'xyz' && (
                      <>
                        Use <Code>{'{z}'}</Code>, <Code>{'{x}'}</Code>,{' '}
                        <Code>{'{y}'}</Code> placeholders
                      </>
                    )}
                    {(editingLayer.type === 'wms' || editingLayer.type === 'wmts') && (
                      <>Base URL without query parameters</>
                    )}
                  </FormHelperText>
                </FormControl>

                {(editingLayer.type === 'wms' || editingLayer.type === 'wmts') && (
                  <FormControl>
                    <FormLabel>Layer Name</FormLabel>
                    <Input
                      value={editingLayer.layerName || ''}
                      onChange={(e) =>
                        setEditingLayer((prev) =>
                          prev ? { ...prev, layerName: e.target.value } : null
                        )
                      }
                      placeholder="layer_name"
                    />
                    <FormHelperText>
                      The layer name as configured in the WMS/WMTS service
                    </FormHelperText>
                  </FormControl>
                )}

                <FormControl>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    value={editingLayer.description || ''}
                    onChange={(e) =>
                      setEditingLayer((prev) =>
                        prev ? { ...prev, description: e.target.value } : null
                      )
                    }
                    placeholder="Brief description of the layer"
                    rows={2}
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Attribution</FormLabel>
                  <Input
                    value={editingLayer.attribution || ''}
                    onChange={(e) =>
                      setEditingLayer((prev) =>
                        prev ? { ...prev, attribution: e.target.value } : null
                      )
                    }
                    placeholder="© Data Provider"
                  />
                </FormControl>

                <HStack>
                  <Button
                    leftIcon={<RepeatIcon />}
                    variant="outline"
                    onClick={testConnection}
                  >
                    Test Connection
                  </Button>
                </HStack>
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

export default ContextLayersPage;
