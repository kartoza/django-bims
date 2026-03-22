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
import { Box } from '@chakra-ui/react';

interface MapLayoutProps {
  children: React.ReactNode;
}

const MapLayout: React.FC<MapLayoutProps> = ({ children }) => {
  // Simple layout - map fills entire space
  // Panel functionality can be added later when panel content is implemented
  return (
    <Box
      w="100%"
      h="100%"
      position="relative"
    >
      {children}
    </Box>
  );
};

export default MapLayout;
