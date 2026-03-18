/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Layout component for map-based views.
 * Uses absolute positioning to ensure map fills available space.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
import {
  Box,
  Flex,
  IconButton,
  useBreakpointValue,
  Drawer,
  DrawerContent,
  DrawerOverlay,
  useDisclosure,
} from '@chakra-ui/react';
import { HamburgerIcon, CloseIcon } from '@chakra-ui/icons';
import { useUIStore } from '../stores/uiStore';

interface MapLayoutProps {
  children: React.ReactNode;
}

const MapLayout: React.FC<MapLayoutProps> = ({ children }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const isMobile = useBreakpointValue({ base: true, lg: false });

  const {
    activePanel,
    panelWidth,
    isPanelCollapsed,
    sidebarPosition,
  } = useUIStore();

  const showPanel = activePanel !== null && !isPanelCollapsed;
  const effectivePanelWidth = showPanel ? panelWidth : 0;

  // Panel content - will be replaced with actual panel components
  const PanelContent = () => (
    <Box
      h="100%"
      bg="white"
      overflowY="auto"
      p={4}
    >
      <Box textAlign="center" color="gray.500" py={10}>
        Panel content will be rendered here based on activePanel
      </Box>
    </Box>
  );

  // Mobile layout - full screen map with drawer
  if (isMobile) {
    return (
      <Box
        position="absolute"
        top={0}
        left={0}
        right={0}
        bottom={0}
      >
        {/* Mobile menu button */}
        <IconButton
          aria-label="Open menu"
          icon={<HamburgerIcon />}
          position="absolute"
          top={4}
          left={4}
          zIndex={20}
          bg="white"
          shadow="md"
          onClick={onOpen}
        />

        {/* Main content (map) - absolute fill */}
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
        >
          {children}
        </Box>

        {/* Mobile drawer */}
        <Drawer
          isOpen={isOpen}
          placement={sidebarPosition}
          onClose={onClose}
          size="sm"
        >
          <DrawerOverlay />
          <DrawerContent>
            <IconButton
              aria-label="Close menu"
              icon={<CloseIcon />}
              position="absolute"
              top={4}
              right={4}
              zIndex={1}
              size="sm"
              onClick={onClose}
            />
            <PanelContent />
          </DrawerContent>
        </Drawer>
      </Box>
    );
  }

  // Desktop layout - absolute positioning for reliable sizing
  return (
    <Box
      position="absolute"
      top={0}
      left={0}
      right={0}
      bottom={0}
    >
      <Flex
        direction={sidebarPosition === 'left' ? 'row' : 'row-reverse'}
        h="100%"
        w="100%"
      >
        {/* Sidebar panel */}
        <Box
          w={showPanel ? `${effectivePanelWidth}px` : '0'}
          minW={showPanel ? `${effectivePanelWidth}px` : '0'}
          h="100%"
          bg="white"
          borderRightWidth={sidebarPosition === 'left' && showPanel ? 1 : 0}
          borderLeftWidth={sidebarPosition === 'right' && showPanel ? 1 : 0}
          borderColor="gray.200"
          transition="width 0.2s ease-in-out"
          overflow="hidden"
          flexShrink={0}
        >
          {showPanel && <PanelContent />}
        </Box>

        {/* Main content (map) */}
        <Box flex="1" h="100%" position="relative" minW={0}>
          {children}
        </Box>
      </Flex>
    </Box>
  );
};

export default MapLayout;
