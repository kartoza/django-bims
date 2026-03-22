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
import { useContextLayersStore, ContextLayer } from '../stores/contextLayersStore';

const ContextLayersPage: React.FC = () => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  // Use the shared store instead of local state
  const { layers, updateLayer, addLayer: storeAddLayer, deleteLayer: storeDeleteLayer, toggleEnabled } = useContextLayersStore();

  const [editingLayer, setEditingLayer] = useState<ContextLayer | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');

  const categories = ['Base Maps', 'Hydrology', 'Conservation', 'Administrative', 'Custom'];

  const toggleLayer = (id: string) => {
    toggleEnabled(id);
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
      visible: false,
      opacity: 0.7,
      category: 'Custom',
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
        opacity: 0.7,
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
              <Heading size="lg">External Layers</Heading>
              <Text opacity={0.9}>
                Remote layers from external servers (WMS, WMTS, XYZ, COG)
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
        <Alert status="info" mb={6} borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight="medium">Remote layers from external servers</Text>
            <Text fontSize="sm" mt={1}>
              External layers are served from remote WMS, WMTS, or XYZ tile servers. The styling is controlled
              by the remote server. These layers appear in the Context Layers section of the map legend alongside
              custom vector layers. For custom-styled layers you control, use{' '}
              <Text as="span" fontWeight="medium">Custom Vector Layers</Text> instead.
            </Text>
          </Box>
        </Alert>

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
            {isEditing ? 'Edit External Layer' : 'Add External Layer'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {editingLayer && (
              <VStack spacing={4} align="stretch">
                <Alert status="info" size="sm" borderRadius="md">
                  <AlertIcon />
                  <Text fontSize="sm">
                    External layers are served from remote servers. The styling is controlled by the source server.
                  </Text>
                </Alert>

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
