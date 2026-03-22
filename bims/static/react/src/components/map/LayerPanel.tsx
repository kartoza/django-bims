/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Layer Management Panel - Toggle layers, adjust opacity, reorder
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  IconButton,
  Checkbox,
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
  Tooltip,
  Collapse,
  useColorModeValue,
  Divider,
} from '@chakra-ui/react';
import {
  ViewIcon,
  ViewOffIcon,
  DragHandleIcon,
  SettingsIcon,
  InfoIcon,
} from '@chakra-ui/icons';
import { useMapStore } from '../../stores/mapStore';

interface Layer {
  id: string;
  name: string;
  type: 'basemap' | 'overlay' | 'wms' | 'data';
  visible: boolean;
  opacity: number;
  source?: string;
  description?: string;
  legendUrl?: string;
  minZoom?: number;
  maxZoom?: number;
}

interface LayerGroup {
  id: string;
  name: string;
  layers: Layer[];
  expanded?: boolean;
}

interface LayerPanelProps {
  isOpen: boolean;
  onClose?: () => void;
}

export const LayerPanel: React.FC<LayerPanelProps> = ({
  isOpen,
  onClose,
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const { layers, setLayerVisibility, setLayerOpacity, basemapStyle, setBasemapStyle, layerList } = useMapStore();

  // Get context layers from the layerList (fetched from API via useContextLayers)
  const contextLayers: Layer[] = layerList
    .filter((l) => l.type === 'overlay')
    .map((l) => ({
      id: l.id,
      name: l.name,
      type: 'wms' as const,
      visible: layers[l.id] || false,
      opacity: l.opacity || 0.7,
    }));

  // Group layers by type - only include context layers group if there are layers from DB
  const layerGroups: LayerGroup[] = [
    {
      id: 'basemaps',
      name: 'Base Maps',
      layers: [
        { id: 'streets', name: 'Streets', type: 'basemap', visible: basemapStyle === 'streets', opacity: 1 },
        { id: 'satellite', name: 'Satellite', type: 'basemap', visible: basemapStyle === 'satellite', opacity: 1 },
        { id: 'terrain', name: 'Terrain', type: 'basemap', visible: basemapStyle === 'terrain', opacity: 1 },
        { id: 'light', name: 'Light', type: 'basemap', visible: basemapStyle === 'light', opacity: 1 },
        { id: 'dark', name: 'Dark', type: 'basemap', visible: basemapStyle === 'dark', opacity: 1 },
      ],
      expanded: true,
    },
    {
      id: 'data',
      name: 'Data Layers',
      layers: [
        { id: 'sites', name: 'Site Locations', type: 'data', visible: layers.sites, opacity: 1, description: 'Biodiversity monitoring sites' },
        { id: 'clusters', name: 'Site Clusters', type: 'data', visible: layers.clusters, opacity: 1, description: 'Clustered site markers' },
        { id: 'heatmap', name: 'Record Heatmap', type: 'data', visible: layers.heatmap || false, opacity: 0.7, description: 'Heat map of record density' },
      ],
      expanded: true,
    },
    // Only include Context Layers if there are layers configured in the database
    ...(contextLayers.length > 0 ? [{
      id: 'context',
      name: 'Context Layers',
      layers: contextLayers,
      expanded: true,
    }] : []),
  ];

  const [expandedGroups, setExpandedGroups] = useState<string[]>(['basemaps', 'data']);
  const [showOpacity, setShowOpacity] = useState<string | null>(null);

  const handleBasemapChange = useCallback(
    (layerId: string) => {
      setBasemapStyle(layerId as typeof basemapStyle);
    },
    [setBasemapStyle]
  );

  const handleVisibilityToggle = useCallback(
    (layerId: string, layerType: string) => {
      if (layerType === 'basemap') {
        handleBasemapChange(layerId);
      } else {
        setLayerVisibility(layerId, !layers[layerId as keyof typeof layers]);
      }
    },
    [handleBasemapChange, setLayerVisibility, layers]
  );

  const handleOpacityChange = useCallback(
    (layerId: string, opacity: number) => {
      setLayerOpacity(layerId, opacity);
    },
    [setLayerOpacity]
  );

  if (!isOpen) return null;

  return (
    <Box
      position="absolute"
      right={4}
      top={4}
      width="280px"
      maxH="calc(100% - 80px)"
      bg={bgColor}
      borderRadius="lg"
      boxShadow="lg"
      borderWidth={1}
      borderColor={borderColor}
      overflow="hidden"
      zIndex={1000}
    >
      <HStack
        p={3}
        borderBottomWidth={1}
        borderColor={borderColor}
        justify="space-between"
      >
        <Text fontWeight="bold" fontSize="sm">
          Layers
        </Text>
        <IconButton
          aria-label="Close layers"
          icon={<ViewOffIcon />}
          size="xs"
          variant="ghost"
          onClick={onClose}
        />
      </HStack>

      <Box maxH="400px" overflow="auto">
        <Accordion
          allowMultiple
          defaultIndex={[0, 1]}
        >
          {layerGroups.map((group) => (
            <AccordionItem key={group.id} border="none">
              <AccordionButton py={2} px={3}>
                <Box flex={1} textAlign="left" fontSize="sm" fontWeight="medium">
                  {group.name}
                </Box>
                <Badge colorScheme="gray" fontSize="xs" mr={2}>
                  {group.layers.filter((l) => l.visible).length}/{group.layers.length}
                </Badge>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel py={1} px={2}>
                <VStack spacing={1} align="stretch">
                  {group.layers.map((layer) => (
                    <Box key={layer.id}>
                      <HStack
                        py={1}
                        px={2}
                        borderRadius="md"
                        _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}
                      >
                        {layer.type === 'basemap' ? (
                          <Checkbox
                            size="sm"
                            isChecked={layer.visible}
                            onChange={() => handleVisibilityToggle(layer.id, layer.type)}
                            borderRadius="full"
                          />
                        ) : (
                          <IconButton
                            aria-label={layer.visible ? 'Hide layer' : 'Show layer'}
                            icon={layer.visible ? <ViewIcon /> : <ViewOffIcon />}
                            size="xs"
                            variant="ghost"
                            colorScheme={layer.visible ? 'blue' : 'gray'}
                            onClick={() => handleVisibilityToggle(layer.id, layer.type)}
                          />
                        )}

                        <Text flex={1} fontSize="xs" noOfLines={1}>
                          {layer.name}
                        </Text>

                        {layer.description && (
                          <Tooltip label={layer.description} placement="left">
                            <InfoIcon color="gray.400" boxSize={3} />
                          </Tooltip>
                        )}

                        {layer.type !== 'basemap' && (
                          <IconButton
                            aria-label="Layer settings"
                            icon={<SettingsIcon />}
                            size="xs"
                            variant="ghost"
                            onClick={() =>
                              setShowOpacity(showOpacity === layer.id ? null : layer.id)
                            }
                          />
                        )}
                      </HStack>

                      {/* Opacity slider */}
                      <Collapse in={showOpacity === layer.id}>
                        <Box px={4} py={2}>
                          <HStack spacing={2}>
                            <Text fontSize="xs" color="gray.500" minW="50px">
                              Opacity
                            </Text>
                            <Slider
                              aria-label="Layer opacity"
                              value={layer.opacity}
                              min={0}
                              max={1}
                              step={0.1}
                              onChange={(val) => handleOpacityChange(layer.id, val)}
                              size="sm"
                            >
                              <SliderTrack>
                                <SliderFilledTrack bg="blue.400" />
                              </SliderTrack>
                              <SliderThumb boxSize={3} />
                            </Slider>
                            <Text fontSize="xs" color="gray.500" minW="30px">
                              {Math.round(layer.opacity * 100)}%
                            </Text>
                          </HStack>
                        </Box>
                      </Collapse>
                    </Box>
                  ))}
                </VStack>
              </AccordionPanel>
            </AccordionItem>
          ))}
        </Accordion>
      </Box>
    </Box>
  );
};

export default LayerPanel;
