/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Tree controls component for zoom, pan, and view actions.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
import {
  VStack,
  IconButton,
  Tooltip,
  Divider,
  Box,
  Spinner,
} from '@chakra-ui/react';
import {
  AddIcon,
  MinusIcon,
  RepeatIcon,
  ViewIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@chakra-ui/icons';

export interface TreeControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
  onFitToView: () => void;
  onExpandAll?: () => void;
  onCollapseAll?: () => void;
  scale: number;
  isExpandingAll?: boolean;
}

const TreeControls: React.FC<TreeControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onResetView,
  onFitToView,
  onExpandAll,
  onCollapseAll,
  scale,
  isExpandingAll = false,
}) => {
  const scalePercent = Math.round(scale * 100);

  return (
    <VStack
      position="absolute"
      right={4}
      top={4}
      spacing={1}
      bg="white"
      borderRadius="md"
      boxShadow="md"
      p={1}
      zIndex={10}
    >
      <Tooltip label="Zoom in" placement="left">
        <IconButton
          aria-label="Zoom in"
          icon={<AddIcon />}
          size="sm"
          variant="ghost"
          onClick={onZoomIn}
        />
      </Tooltip>

      <Box
        fontSize="xs"
        fontWeight="medium"
        color="gray.600"
        px={2}
        py={1}
        textAlign="center"
        minW="50px"
      >
        {scalePercent}%
      </Box>

      <Tooltip label="Zoom out" placement="left">
        <IconButton
          aria-label="Zoom out"
          icon={<MinusIcon />}
          size="sm"
          variant="ghost"
          onClick={onZoomOut}
        />
      </Tooltip>

      <Divider />

      <Tooltip label="Reset view" placement="left">
        <IconButton
          aria-label="Reset view"
          icon={<RepeatIcon />}
          size="sm"
          variant="ghost"
          onClick={onResetView}
        />
      </Tooltip>

      <Tooltip label="Fit to view" placement="left">
        <IconButton
          aria-label="Fit to view"
          icon={<ViewIcon />}
          size="sm"
          variant="ghost"
          onClick={onFitToView}
        />
      </Tooltip>

      {onExpandAll && onCollapseAll && (
        <>
          <Divider />

          <Tooltip label="Expand all (loads all children)" placement="left">
            <IconButton
              aria-label="Expand all"
              icon={isExpandingAll ? <Spinner size="xs" /> : <ChevronDownIcon boxSize={5} />}
              size="sm"
              variant="ghost"
              onClick={onExpandAll}
              isDisabled={isExpandingAll}
              colorScheme="green"
            />
          </Tooltip>

          <Tooltip label="Collapse all" placement="left">
            <IconButton
              aria-label="Collapse all"
              icon={<ChevronUpIcon boxSize={5} />}
              size="sm"
              variant="ghost"
              onClick={onCollapseAll}
              isDisabled={isExpandingAll}
              colorScheme="orange"
            />
          </Tooltip>
        </>
      )}
    </VStack>
  );
};

export default TreeControls;
