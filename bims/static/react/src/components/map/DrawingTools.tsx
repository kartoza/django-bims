/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Drawing Tools - Polygon and lasso drawing for spatial filtering
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  IconButton,
  Button,
  Text,
  Tooltip,
  ButtonGroup,
  Badge,
  useColorModeValue,
  Divider,
} from '@chakra-ui/react';
import {
  EditIcon,
  DeleteIcon,
  CheckIcon,
  CloseIcon,
  RepeatIcon,
} from '@chakra-ui/icons';
import { useSearchStore } from '../../stores/searchStore';

type DrawMode = 'none' | 'polygon' | 'rectangle' | 'circle' | 'freehand';

interface Point {
  x: number;
  y: number;
  lng: number;
  lat: number;
}

interface DrawingToolsProps {
  mapContainer: HTMLElement | null;
  onPolygonComplete?: (coordinates: number[][]) => void;
  onClear?: () => void;
}

// Icons for drawing modes
const PolygonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12,2L4,12L12,22L20,12L12,2M12,5.2L17.5,12L12,18.8L6.5,12L12,5.2Z" />
  </svg>
);

const RectangleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M4,6V19H20V6H4M18,17H6V8H18V17Z" />
  </svg>
);

const CircleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
  </svg>
);

const FreehandIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M9.75,20.85C11.53,20.15 11.14,18.22 10.24,17C9.35,15.75 8.12,14.89 6.88,14.06C6,13.5 5.13,12.87 4.5,12C3.86,11.12 3.5,10.04 3.5,9C3.5,7.07 4.7,5.55 6.58,5.06C8.45,4.56 10.27,5.27 11.12,6.83C11.72,7.96 11.55,9.24 10.81,10.14C10.5,10.53 10.04,10.84 9.5,10.94C8.55,11.11 7.64,10.47 7.5,9.5C7.38,8.72 7.94,8 8.73,8C8.92,8 9.11,8.05 9.29,8.13C9.03,7.76 8.67,7.5 8.22,7.41C7.28,7.24 6.34,7.85 6.18,8.81C6,9.78 6.61,10.73 7.58,10.91C8.25,11.03 8.9,10.91 9.45,10.56C10.66,9.75 11.3,8.25 10.79,6.89C10,4.87 7.74,3.79 5.64,4.4C3.06,5.14 1.62,7.75 2.5,10.38C2.93,11.63 3.88,12.71 5.03,13.43C6.49,14.36 8.21,15 9.26,16.38C10.35,17.83 10.12,20.16 7.53,21C9.13,21.22 10.85,21.26 12.5,20.97L12.5,17.38C12.5,15.5 14.25,14 16.38,14C17.38,14 18.31,14.35 19,14.92L19,8C19,6.9 18.1,6 17,6H14C14,7.1 13.1,8 12,8C10.9,8 10,7.1 10,6H7C5.9,6 5,6.9 5,8V9.89C5.34,9.58 5.73,9.32 6.16,9.15C7.5,8.62 9.04,9.31 9.57,10.65C10.1,11.99 9.41,13.53 8.07,14.06C6.73,14.59 5.19,13.9 4.66,12.56C4.5,12.12 4.45,11.67 4.5,11.22V8C4.5,6.63 5.63,5.5 7,5.5H10.18C10.59,4.36 11.68,3.5 13,3.5C14.32,3.5 15.41,4.36 15.82,5.5H17C18.38,5.5 19.5,6.63 19.5,8V15.18C19.5,15.35 19.5,15.53 19.5,15.69C20.22,16.68 20.5,17.86 20.5,19H21.5V17.38C21.5,15 19.5,13 17.5,13H16.38C15.07,13 14,14.07 14,15.38V22H9.75L9.75,20.85Z" />
  </svg>
);

export const DrawingTools: React.FC<DrawingToolsProps> = ({
  mapContainer,
  onPolygonComplete,
  onClear,
}) => {
  const [drawMode, setDrawMode] = useState<DrawMode>('none');
  const [points, setPoints] = useState<Point[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const { setFilter, clearFilter } = useSearchStore();

  // Convert screen coordinates to map coordinates (simplified - would need map reference)
  const screenToLatLng = useCallback((x: number, y: number): { lng: number; lat: number } => {
    // This is a placeholder - in real implementation, use mapRef to convert
    // For now, return dummy values
    return { lng: x, lat: y };
  }, []);

  // Handle drawing on canvas
  useEffect(() => {
    if (!mapContainer || drawMode === 'none') return;

    const canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'auto';
    canvas.style.cursor = 'crosshair';
    canvas.style.zIndex = '500';
    canvas.width = mapContainer.clientWidth;
    canvas.height = mapContainer.clientHeight;
    mapContainer.appendChild(canvas);
    canvasRef.current = canvas;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const handleMouseDown = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const { lng, lat } = screenToLatLng(x, y);

      if (drawMode === 'freehand') {
        setIsDrawing(true);
        setPoints([{ x, y, lng, lat }]);
      } else {
        setPoints((prev) => [...prev, { x, y, lng, lat }]);
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDrawing && drawMode !== 'freehand') return;
      if (drawMode !== 'freehand') return;

      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const { lng, lat } = screenToLatLng(x, y);

      setPoints((prev) => [...prev, { x, y, lng, lat }]);
    };

    const handleMouseUp = () => {
      if (drawMode === 'freehand') {
        setIsDrawing(false);
        finishDrawing();
      }
    };

    const handleDblClick = () => {
      if (drawMode === 'polygon' && points.length >= 3) {
        finishDrawing();
      }
    };

    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('dblclick', handleDblClick);

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('dblclick', handleDblClick);
      if (mapContainer.contains(canvas)) {
        mapContainer.removeChild(canvas);
      }
    };
  }, [mapContainer, drawMode, isDrawing, points, screenToLatLng]);

  // Draw the current polygon
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (points.length === 0) return;

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);

    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }

    // Close path for polygon
    if (drawMode === 'polygon' || drawMode === 'freehand') {
      ctx.closePath();
    }

    ctx.strokeStyle = '#3182ce';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = 'rgba(49, 130, 206, 0.2)';
    ctx.fill();

    // Draw vertices
    points.forEach((point) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#3182ce';
      ctx.fill();
      ctx.strokeStyle = 'white';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }, [points, drawMode]);

  const finishDrawing = useCallback(() => {
    if (points.length < 3) return;

    // Convert points to coordinates
    const coordinates = points.map((p) => [p.lng, p.lat]);
    coordinates.push(coordinates[0]); // Close the polygon

    // Create bbox from points
    const lngs = points.map((p) => p.lng);
    const lats = points.map((p) => p.lat);
    const bbox = `${Math.min(...lngs)},${Math.min(...lats)},${Math.max(...lngs)},${Math.max(...lats)}`;

    setFilter('bbox', bbox);
    onPolygonComplete?.(coordinates);

    setDrawMode('none');
    setPoints([]);

    // Remove canvas
    if (canvasRef.current && mapContainer?.contains(canvasRef.current)) {
      mapContainer.removeChild(canvasRef.current);
      canvasRef.current = null;
    }
  }, [points, setFilter, onPolygonComplete, mapContainer]);

  const handleClear = useCallback(() => {
    setDrawMode('none');
    setPoints([]);
    clearFilter('bbox');
    onClear?.();

    if (canvasRef.current && mapContainer?.contains(canvasRef.current)) {
      mapContainer.removeChild(canvasRef.current);
      canvasRef.current = null;
    }
  }, [clearFilter, onClear, mapContainer]);

  const handleCancel = useCallback(() => {
    setDrawMode('none');
    setPoints([]);

    if (canvasRef.current && mapContainer?.contains(canvasRef.current)) {
      mapContainer.removeChild(canvasRef.current);
      canvasRef.current = null;
    }
  }, [mapContainer]);

  return (
    <Box
      bg={bgColor}
      borderRadius="lg"
      boxShadow="md"
      borderWidth={1}
      borderColor={borderColor}
      p={2}
    >
      <VStack spacing={2} align="stretch">
        <HStack justify="space-between">
          <Text fontSize="xs" fontWeight="bold" color="gray.600">
            Draw Filter
          </Text>
          {drawMode !== 'none' && (
            <Badge colorScheme="blue" fontSize="xs">
              {drawMode}
            </Badge>
          )}
        </HStack>

        <ButtonGroup size="sm" variant="outline" isAttached>
          <Tooltip label="Draw polygon">
            <IconButton
              aria-label="Draw polygon"
              icon={<PolygonIcon />}
              colorScheme={drawMode === 'polygon' ? 'blue' : 'gray'}
              onClick={() => setDrawMode('polygon')}
            />
          </Tooltip>
          <Tooltip label="Draw rectangle">
            <IconButton
              aria-label="Draw rectangle"
              icon={<RectangleIcon />}
              colorScheme={drawMode === 'rectangle' ? 'blue' : 'gray'}
              onClick={() => setDrawMode('rectangle')}
            />
          </Tooltip>
          <Tooltip label="Freehand">
            <IconButton
              aria-label="Freehand"
              icon={<FreehandIcon />}
              colorScheme={drawMode === 'freehand' ? 'blue' : 'gray'}
              onClick={() => setDrawMode('freehand')}
            />
          </Tooltip>
        </ButtonGroup>

        {drawMode !== 'none' && (
          <>
            <Divider />
            <Text fontSize="xs" color="gray.500">
              {drawMode === 'polygon'
                ? 'Click to add points. Double-click to finish.'
                : drawMode === 'freehand'
                ? 'Click and drag to draw.'
                : 'Click and drag to draw rectangle.'}
            </Text>
            <HStack spacing={1}>
              <Tooltip label="Finish drawing">
                <IconButton
                  aria-label="Finish"
                  icon={<CheckIcon />}
                  size="xs"
                  colorScheme="green"
                  onClick={finishDrawing}
                  isDisabled={points.length < 3}
                />
              </Tooltip>
              <Tooltip label="Clear points">
                <IconButton
                  aria-label="Clear"
                  icon={<RepeatIcon />}
                  size="xs"
                  onClick={() => setPoints([])}
                />
              </Tooltip>
              <Tooltip label="Cancel">
                <IconButton
                  aria-label="Cancel"
                  icon={<CloseIcon />}
                  size="xs"
                  colorScheme="red"
                  variant="ghost"
                  onClick={handleCancel}
                />
              </Tooltip>
            </HStack>
          </>
        )}

        {points.length > 0 && drawMode === 'none' && (
          <Button
            size="xs"
            leftIcon={<DeleteIcon />}
            colorScheme="red"
            variant="ghost"
            onClick={handleClear}
          >
            Clear Filter Area
          </Button>
        )}
      </VStack>
    </Box>
  );
};

export default DrawingTools;
