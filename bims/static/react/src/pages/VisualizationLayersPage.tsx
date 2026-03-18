/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Visualization Layers management page.
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
} from '@chakra-ui/react';
import {
  AddIcon,
  EditIcon,
  DeleteIcon,
  ViewIcon,
  ViewOffIcon,
  DragHandleIcon,
} from '@chakra-ui/icons';

interface VisualizationLayer {
  id: string;
  name: string;
  type: 'point' | 'polygon' | 'heatmap' | 'cluster';
  source: string;
  enabled: boolean;
  opacity: number;
  minZoom: number;
  maxZoom: number;
  style: {
    color: string;
    fillColor?: string;
    radius?: number;
  };
  order: number;
}

const VisualizationLayersPage: React.FC = () => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  const [layers, setLayers] = useState<VisualizationLayer[]>([
    {
      id: '1',
      name: 'Location Sites',
      type: 'cluster',
      source: 'sites',
      enabled: true,
      opacity: 100,
      minZoom: 0,
      maxZoom: 22,
      style: { color: '#3182CE', fillColor: '#3182CE', radius: 8 },
      order: 1,
    },
    {
      id: '2',
      name: 'Fish Records',
      type: 'point',
      source: 'fish_records',
      enabled: true,
      opacity: 80,
      minZoom: 5,
      maxZoom: 22,
      style: { color: '#38A169', fillColor: '#38A169', radius: 6 },
      order: 2,
    },
    {
      id: '3',
      name: 'Species Heatmap',
      type: 'heatmap',
      source: 'all_records',
      enabled: false,
      opacity: 60,
      minZoom: 0,
      maxZoom: 10,
      style: { color: '#E53E3E' },
      order: 3,
    },
    {
      id: '4',
      name: 'River Catchments',
      type: 'polygon',
      source: 'catchments',
      enabled: true,
      opacity: 50,
      minZoom: 0,
      maxZoom: 22,
      style: { color: '#0BC5EA', fillColor: '#0BC5EA' },
      order: 4,
    },
  ]);

  const [editingLayer, setEditingLayer] = useState<VisualizationLayer | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const toggleLayer = (id: string) => {
    setLayers((prev) =>
      prev.map((layer) =>
        layer.id === id ? { ...layer, enabled: !layer.enabled } : layer
      )
    );
  };

  const updateOpacity = (id: string, opacity: number) => {
    setLayers((prev) =>
      prev.map((layer) => (layer.id === id ? { ...layer, opacity } : layer))
    );
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
              <Heading size="lg">Visualization Layers</Heading>
              <Text opacity={0.9}>
                Configure map visualization layers and styling
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
          Drag layers to reorder. Layers higher in the list appear on top of the map.
        </Alert>

        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Map Layers</Heading>
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
