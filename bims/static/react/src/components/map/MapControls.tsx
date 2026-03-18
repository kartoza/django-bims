/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Map control buttons component.
 */
import React from 'react';
import {
  VStack,
  IconButton,
  Tooltip,
  Divider,
  Box,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  AddIcon,
  MinusIcon,
  RepeatIcon,
  ViewIcon,
  EditIcon,
  Search2Icon,
  SettingsIcon,
} from '@chakra-ui/icons';
import { FiBox, FiGrid } from 'react-icons/fi';
import { useMap } from '../../providers/MapProvider';
import { useMapStore, DrawMode } from '../../stores/mapStore';
import { useUIStore } from '../../stores/uiStore';

interface ControlButtonProps {
  icon: React.ReactElement;
  label: string;
  onClick: () => void;
  isActive?: boolean;
  isDisabled?: boolean;
}

const ControlButton: React.FC<ControlButtonProps> = ({
  icon,
  label,
  onClick,
  isActive = false,
  isDisabled = false,
}) => {
  const bgColor = useColorModeValue('white', 'gray.700');
  const activeBgColor = useColorModeValue('brand.50', 'brand.900');

  return (
    <Tooltip label={label} placement="left" hasArrow>
      <IconButton
        aria-label={label}
        icon={icon}
        onClick={onClick}
        isDisabled={isDisabled}
        size="md"
        variant="ghost"
        bg={isActive ? activeBgColor : bgColor}
        color={isActive ? 'brand.500' : 'gray.600'}
        _hover={{
          bg: isActive ? activeBgColor : 'gray.100',
        }}
        shadow="sm"
        borderRadius="md"
      />
    </Tooltip>
  );
};

const MapControls: React.FC = () => {
  const { zoomIn, zoomOut, resetView, isMapReady } = useMap();
  const { drawMode, setDrawMode } = useMapStore();
  const { openModal, activePanel, setActivePanel, is3DMap, toggle3DMap } = useUIStore();

  const bgColor = useColorModeValue('white', 'gray.700');

  const handleDrawModeChange = (mode: DrawMode) => {
    setDrawMode(drawMode === mode ? 'none' : mode);
  };

  return (
    <>
      {/* Main controls - positioned on the right side */}
      <VStack
        position="absolute"
        top={4}
        right={4}
        spacing={1}
        zIndex={10}
        bg={bgColor}
        p={1}
        borderRadius="lg"
        shadow="md"
      >
        {/* Zoom controls */}
        <ControlButton
          icon={<AddIcon boxSize={3} />}
          label="Zoom in"
          onClick={zoomIn}
          isDisabled={!isMapReady}
        />
        <ControlButton
          icon={<MinusIcon boxSize={3} />}
          label="Zoom out"
          onClick={zoomOut}
          isDisabled={!isMapReady}
        />
        <ControlButton
          icon={<RepeatIcon boxSize={3} />}
          label="Reset view"
          onClick={resetView}
          isDisabled={!isMapReady}
        />

        <Divider borderColor="gray.200" />

        {/* 3D Toggle */}
        <ControlButton
          icon={is3DMap ? <FiGrid size={14} /> : <FiBox size={14} />}
          label={is3DMap ? 'Switch to 2D view' : 'Switch to 3D view'}
          onClick={toggle3DMap}
          isActive={is3DMap}
          isDisabled={!isMapReady}
        />

        <Divider borderColor="gray.200" />

        {/* Drawing tools */}
        <Menu placement="left">
          <Tooltip label="Draw tools" placement="left" hasArrow>
            <MenuButton
              as={IconButton}
              aria-label="Draw tools"
              icon={<EditIcon boxSize={3} />}
              size="md"
              variant="ghost"
              bg={drawMode !== 'none' ? 'brand.50' : bgColor}
              color={drawMode !== 'none' ? 'brand.500' : 'gray.600'}
              _hover={{ bg: 'gray.100' }}
              isDisabled={!isMapReady}
            />
          </Tooltip>
          <MenuList>
            <MenuItem
              onClick={() => handleDrawModeChange('point')}
              bg={drawMode === 'point' ? 'brand.50' : undefined}
            >
              Draw Point
            </MenuItem>
            <MenuItem
              onClick={() => handleDrawModeChange('polygon')}
              bg={drawMode === 'polygon' ? 'brand.50' : undefined}
            >
              Draw Polygon
            </MenuItem>
            <MenuItem
              onClick={() => handleDrawModeChange('line')}
              bg={drawMode === 'line' ? 'brand.50' : undefined}
            >
              Draw Line
            </MenuItem>
            {drawMode !== 'none' && (
              <>
                <Divider />
                <MenuItem onClick={() => setDrawMode('none')}>
                  Cancel Drawing
                </MenuItem>
              </>
            )}
          </MenuList>
        </Menu>
      </VStack>

      {/* Left side controls */}
      <VStack
        position="absolute"
        top={4}
        left={4}
        spacing={1}
        zIndex={10}
        bg={bgColor}
        p={1}
        borderRadius="lg"
        shadow="md"
      >
        {/* Search panel toggle */}
        <ControlButton
          icon={<Search2Icon boxSize={3} />}
          label={activePanel === 'search' ? 'Close search' : 'Open search'}
          onClick={() => setActivePanel(activePanel === 'search' ? null : 'search')}
          isActive={activePanel === 'search'}
        />

        {/* Legend panel toggle */}
        <ControlButton
          icon={<ViewIcon boxSize={3} />}
          label={activePanel === 'legend' ? 'Close legend' : 'Open legend'}
          onClick={() => setActivePanel(activePanel === 'legend' ? null : 'legend')}
          isActive={activePanel === 'legend'}
        />

        <Divider borderColor="gray.200" />

        {/* Settings */}
        <ControlButton
          icon={<SettingsIcon boxSize={3} />}
          label="Map settings"
          onClick={() => openModal('settings')}
        />
      </VStack>
    </>
  );
};

export default MapControls;
