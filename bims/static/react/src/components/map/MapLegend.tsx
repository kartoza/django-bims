/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Map Legend component showing all context and visualization layers.
 * Allows toggling layer visibility and adjusting opacity.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Switch,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Badge,
  Divider,
  IconButton,
  CloseButton,
  useColorModeValue,
  Tooltip,
  Flex,
  Spacer,
  Icon,
} from '@chakra-ui/react';
import { ViewIcon, ViewOffIcon } from '@chakra-ui/icons';
import { useMapStore, MapLayer } from '../../stores/mapStore';
import { useContextLayersStore } from '../../stores/contextLayersStore';
import { useUIStore } from '../../stores/uiStore';

// Layer category definitions with icons and colors
interface LayerCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
}

const LAYER_CATEGORIES: LayerCategory[] = [
  {
    id: 'biodiversity',
    name: 'Biodiversity Data',
    description: 'Species and occurrence data',
    icon: '🦋',
    color: 'green.500',
  },
  {
    id: 'context',
    name: 'Context Layers',
    description: 'Administrative and geographic boundaries',
    icon: '🗺️',
    color: 'blue.500',
  },
  {
    id: 'visualization',
    name: 'Visualization',
    description: 'Data analysis and visualization layers',
    icon: '📊',
    color: 'purple.500',
  },
];

// Default layers for biodiversity and visualization categories
// Context layers come from the database via useContextLayers hook
const DEFAULT_LAYERS: MapLayer[] = [
  // Biodiversity data layers
  {
    id: 'sites',
    name: 'Location Sites',
    visible: true,
    opacity: 1,
    type: 'data',
  },
  // Visualization layers
  {
    id: 'heatmap',
    name: 'Occurrence Heatmap',
    visible: false,
    opacity: 0.7,
    type: 'data',
  },
  {
    id: 'clusters',
    name: 'Site Clusters',
    visible: false,
    opacity: 1,
    type: 'data',
  },
];

// Map layer types to categories
const getLayerCategory = (layer: MapLayer): string => {
  if (layer.type === 'base') return 'base';

  // Categorize overlay/data layers
  const id = layer.id.toLowerCase();

  // Biodiversity data layers
  if (['sites', 'occurrences', 'taxa-distribution'].includes(id)) {
    return 'biodiversity';
  }

  // Context layers (boundaries, rivers, protected areas)
  if ([
    'provinces', 'municipalities', 'catchments', 'sub-catchments', 'ecoregions',
    'rivers', 'wetlands', 'dams', 'estuaries',
    'protected-areas', 'critical-biodiversity', 'ramsar-sites'
  ].includes(id)) {
    return 'context';
  }

  // Visualization/analysis layers
  if (['heatmap', 'clusters', 'species-richness', 'endemism-hotspots'].includes(id)) {
    return 'visualization';
  }

  // Default based on type
  return layer.type === 'data' ? 'biodiversity' : 'context';
};

// Legend item symbols for different layer types
const getLayerSymbol = (layerId: string): React.ReactNode => {
  const symbolStyle: React.CSSProperties = {
    width: '16px',
    height: '16px',
    borderRadius: '4px',
    display: 'inline-block',
  };

  switch (layerId) {
    case 'sites':
    case 'unclustered-point':
      return (
        <Box
          w="14px"
          h="14px"
          borderRadius="full"
          bg="#0073e6"
          border="2px solid white"
          boxShadow="sm"
        />
      );
    case 'clusters':
      return (
        <Box
          w="18px"
          h="18px"
          borderRadius="full"
          bg="#51bbd6"
          border="2px solid white"
          boxShadow="sm"
          display="flex"
          alignItems="center"
          justifyContent="center"
          fontSize="8px"
          fontWeight="bold"
          color="gray.700"
        >
          n
        </Box>
      );
    case 'highlighted-point':
      return (
        <Box
          w="14px"
          h="14px"
          borderRadius="full"
          bg="#ff9900"
          border="2px solid white"
          boxShadow="sm"
        />
      );
    case 'rivers':
      return (
        <Box w="20px" h="3px" bg="cyan.500" borderRadius="full" />
      );
    case 'wetlands':
      return (
        <Box
          w="16px"
          h="16px"
          bg="teal.200"
          borderRadius="sm"
          border="1px dashed"
          borderColor="teal.500"
        />
      );
    case 'protected-areas':
      return (
        <Box
          w="16px"
          h="16px"
          bg="green.200"
          borderRadius="sm"
          border="2px solid"
          borderColor="green.600"
          opacity={0.7}
        />
      );
    case 'critical-biodiversity':
      return (
        <Box
          w="16px"
          h="16px"
          bg="red.200"
          borderRadius="sm"
          border="1px solid"
          borderColor="red.500"
          opacity={0.7}
        />
      );
    case 'provinces':
    case 'municipalities':
      return (
        <Box
          w="16px"
          h="16px"
          bg="transparent"
          borderRadius="sm"
          border="2px solid"
          borderColor="gray.500"
        />
      );
    case 'catchments':
    case 'sub-catchments':
      return (
        <Box
          w="16px"
          h="16px"
          bg="blue.100"
          borderRadius="sm"
          border="1px solid"
          borderColor="blue.400"
        />
      );
    case 'heatmap':
      return (
        <Box
          w="16px"
          h="16px"
          borderRadius="sm"
          bgGradient="linear(to-r, blue.300, yellow.300, red.400)"
        />
      );
    case 'species-richness':
      return (
        <Box
          w="16px"
          h="16px"
          borderRadius="sm"
          bgGradient="linear(to-r, yellow.200, green.400, green.700)"
        />
      );
    default:
      return (
        <Box
          w="14px"
          h="14px"
          borderRadius="sm"
          bg="gray.300"
          border="1px solid"
          borderColor="gray.400"
        />
      );
  }
};

interface LayerItemProps {
  layer: MapLayer;
  onToggle: (layerId: string, visible: boolean) => void;
  onOpacityChange: (layerId: string, opacity: number) => void;
}

const LayerItem: React.FC<LayerItemProps> = ({ layer, onToggle, onOpacityChange }) => {
  const [showOpacity, setShowOpacity] = React.useState(false);
  const bgHover = useColorModeValue('gray.50', 'gray.700');

  return (
    <Box
      py={2}
      px={3}
      borderRadius="md"
      _hover={{ bg: bgHover }}
      transition="background 0.15s ease"
    >
      <HStack spacing={3}>
        {/* Layer symbol */}
        <Box flexShrink={0}>{getLayerSymbol(layer.id)}</Box>

        {/* Layer name */}
        <Text flex="1" fontSize="sm" fontWeight={layer.visible ? '500' : '400'}>
          {layer.name}
        </Text>

        {/* Opacity control toggle */}
        <Tooltip label="Adjust opacity" placement="top">
          <IconButton
            aria-label="Opacity"
            icon={layer.visible ? <ViewIcon /> : <ViewOffIcon />}
            size="xs"
            variant="ghost"
            opacity={layer.visible ? 1 : 0.5}
            onClick={() => setShowOpacity(!showOpacity)}
          />
        </Tooltip>

        {/* Visibility toggle */}
        <Switch
          size="sm"
          colorScheme="brand"
          isChecked={layer.visible}
          onChange={(e) => onToggle(layer.id, e.target.checked)}
        />
      </HStack>

      {/* Opacity slider (collapsible) */}
      {showOpacity && layer.visible && (
        <Box pt={2} pl={8}>
          <HStack spacing={2}>
            <Text fontSize="xs" color="gray.500" w="50px">
              Opacity
            </Text>
            <Slider
              aria-label="layer-opacity"
              value={layer.opacity * 100}
              onChange={(val) => onOpacityChange(layer.id, val / 100)}
              min={10}
              max={100}
              step={10}
              flex="1"
            >
              <SliderTrack bg="gray.200">
                <SliderFilledTrack bg="brand.500" />
              </SliderTrack>
              <SliderThumb boxSize={3} />
            </Slider>
            <Text fontSize="xs" color="gray.500" w="35px" textAlign="right">
              {Math.round(layer.opacity * 100)}%
            </Text>
          </HStack>
        </Box>
      )}
    </Box>
  );
};

interface MapLegendProps {
  isOpen: boolean;
  onClose: () => void;
}

const MapLegend: React.FC<MapLegendProps> = ({ isOpen, onClose }) => {
  const { layerList, layers, addLayer, setLayerVisibility, setLayerOpacity } = useMapStore();
  const { layers: contextLayers, toggleVisibility: toggleContextVisibility, setOpacity: setContextOpacity } = useContextLayersStore();

  // All useColorModeValue calls must be at the top, before any conditional returns
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const headerFooterBg = useColorModeValue('gray.50', 'gray.700');
  const hoverBg = useColorModeValue('gray.100', 'gray.700');
  const expandedBg = useColorModeValue('brand.50', 'brand.900');

  // Initialize default layers (adds any missing default layers)
  useEffect(() => {
    const existingIds = new Set(layerList.map(l => l.id));
    DEFAULT_LAYERS.forEach((layer) => {
      if (!existingIds.has(layer.id)) {
        addLayer(layer);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  // Merge layerList with visibility from layers store
  const mergedLayers = React.useMemo(() => {
    return layerList.map((layer) => ({
      ...layer,
      visible: layers[layer.id] ?? layer.visible,
    }));
  }, [layerList, layers]);

  // Convert context layers store to MapLayer format for display
  const contextLayersAsMaplayers: MapLayer[] = React.useMemo(() => {
    return contextLayers
      .filter((cl) => cl.enabled && cl.category !== 'Base Maps') // Only enabled non-basemap layers
      .map((cl) => ({
        id: `context-${cl.id}`,
        name: cl.name,
        visible: cl.visible,
        opacity: cl.opacity,
        type: 'overlay' as const,
      }));
  }, [contextLayers]);

  // Group layers by category
  const layersByCategory = React.useMemo(() => {
    const grouped: Record<string, MapLayer[]> = {};

    LAYER_CATEGORIES.forEach((cat) => {
      grouped[cat.id] = [];
    });

    // Add default/map layers
    mergedLayers.forEach((layer) => {
      const category = getLayerCategory(layer);
      if (grouped[category]) {
        grouped[category].push(layer);
      } else {
        // Fall back to biodiversity for unknown categories
        grouped['biodiversity'].push(layer);
      }
    });

    // Add context layers from the store to the 'context' category
    grouped['context'] = [...grouped['context'], ...contextLayersAsMaplayers];

    return grouped;
  }, [mergedLayers, contextLayersAsMaplayers]);

  // Count visible layers per category
  const visibleCounts = React.useMemo(() => {
    const counts: Record<string, number> = {};
    Object.entries(layersByCategory).forEach(([cat, catLayers]) => {
      counts[cat] = catLayers.filter((l) => l.visible).length;
    });
    return counts;
  }, [layersByCategory]);

  // Total active layers including context layers
  const totalActiveCount = React.useMemo(() => {
    const mapLayersCount = mergedLayers.filter((l) => l.visible).length;
    const contextLayersCount = contextLayersAsMaplayers.filter((l) => l.visible).length;
    return mapLayersCount + contextLayersCount;
  }, [mergedLayers, contextLayersAsMaplayers]);

  // Handler that works for both map store and context store layers
  const handleToggleVisibility = (layerId: string, visible: boolean) => {
    if (layerId.startsWith('context-')) {
      // This is a context layer from the store
      const contextId = layerId.replace('context-', '');
      toggleContextVisibility(contextId);
    } else {
      // This is a map store layer
      setLayerVisibility(layerId, visible);
    }
  };

  // Handler that works for both map store and context store layers
  const handleOpacityChange = (layerId: string, opacity: number) => {
    if (layerId.startsWith('context-')) {
      // This is a context layer from the store
      const contextId = layerId.replace('context-', '');
      setContextOpacity(contextId, opacity);
    } else {
      // This is a map store layer
      setLayerOpacity(layerId, opacity);
    }
  };

  if (!isOpen) return null;

  return (
    <Box
      position="absolute"
      left={4}
      top="60px"
      w="320px"
      maxH="calc(100vh - 120px)"
      bg={bgColor}
      borderRadius="xl"
      boxShadow="lg"
      border="1px solid"
      borderColor={borderColor}
      zIndex={1000}
      overflow="hidden"
      display="flex"
      flexDirection="column"
    >
      {/* Header */}
      <Flex
        px={4}
        py={3}
        borderBottom="1px solid"
        borderColor={borderColor}
        align="center"
        bg={headerFooterBg}
      >
        <Heading size="sm">Map Layers</Heading>
        <Spacer />
        <Badge colorScheme="brand" mr={2}>
          {totalActiveCount} active
        </Badge>
        <CloseButton size="sm" onClick={onClose} />
      </Flex>

      {/* Layer categories accordion */}
      <Box flex="1" overflowY="auto" px={2} py={2}>
        <Accordion allowMultiple defaultIndex={[0, 1, 2]}>
          {LAYER_CATEGORIES.map((category) => {
            const catLayers = layersByCategory[category.id] || [];
            if (catLayers.length === 0) return null;

            return (
              <AccordionItem key={category.id} border="none" mb={1}>
                <AccordionButton
                  px={3}
                  py={2}
                  borderRadius="lg"
                  _hover={{ bg: hoverBg }}
                  _expanded={{ bg: expandedBg }}
                >
                  <HStack flex="1" spacing={2}>
                    <Text fontSize="lg">{category.icon}</Text>
                    <Text fontWeight="600" fontSize="sm">
                      {category.name}
                    </Text>
                    {visibleCounts[category.id] > 0 && (
                      <Badge
                        size="sm"
                        colorScheme="brand"
                        variant="subtle"
                        borderRadius="full"
                      >
                        {visibleCounts[category.id]}
                      </Badge>
                    )}
                  </HStack>
                  <AccordionIcon />
                </AccordionButton>

                <AccordionPanel pb={2} px={1}>
                  <Text fontSize="xs" color="gray.500" mb={2} px={2}>
                    {category.description}
                  </Text>
                  <VStack spacing={0} align="stretch">
                    {catLayers.map((layer) => (
                      <LayerItem
                        key={layer.id}
                        layer={layer}
                        onToggle={handleToggleVisibility}
                        onOpacityChange={handleOpacityChange}
                      />
                    ))}
                  </VStack>
                </AccordionPanel>
              </AccordionItem>
            );
          })}
        </Accordion>
      </Box>

      {/* Footer with quick actions */}
      <Box
        px={4}
        py={2}
        borderTop="1px solid"
        borderColor={borderColor}
        bg={headerFooterBg}
      >
        <HStack spacing={2} justify="center">
          <Tooltip label="Show all layers">
            <IconButton
              aria-label="Show all"
              icon={<ViewIcon />}
              size="sm"
              variant="ghost"
              onClick={() => {
                layerList.forEach((l) => setLayerVisibility(l.id, true));
              }}
            />
          </Tooltip>
          <Tooltip label="Hide all layers">
            <IconButton
              aria-label="Hide all"
              icon={<ViewOffIcon />}
              size="sm"
              variant="ghost"
              onClick={() => {
                // Keep base map visible
                layerList.forEach((l) => {
                  if (l.type !== 'base') {
                    setLayerVisibility(l.id, false);
                  }
                });
              }}
            />
          </Tooltip>
          <Text fontSize="xs" color="gray.500">
            Toggle all layers
          </Text>
        </HStack>
      </Box>
    </Box>
  );
};

export default MapLegend;
