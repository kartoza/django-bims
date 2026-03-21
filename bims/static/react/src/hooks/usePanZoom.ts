/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for handling pan and zoom interactions on an infinite canvas.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useCallback, useRef, useEffect, useState } from 'react';
import { useTreeStore, Transform } from '../stores/treeStore';

export interface PanZoomHandlers {
  onMouseDown: (e: React.MouseEvent) => void;
  onMouseMove: (e: React.MouseEvent) => void;
  onMouseUp: (e: React.MouseEvent) => void;
  onMouseLeave: (e: React.MouseEvent) => void;
  onWheel: (e: React.WheelEvent) => void;
  onTouchStart: (e: React.TouchEvent) => void;
  onTouchMove: (e: React.TouchEvent) => void;
  onTouchEnd: (e: React.TouchEvent) => void;
}

export interface UsePanZoomOptions {
  minScale?: number;
  maxScale?: number;
  zoomSensitivity?: number;
  panButton?: number; // 0 = left, 1 = middle, 2 = right
}

export interface UsePanZoomReturn {
  handlers: PanZoomHandlers;
  transform: Transform;
  isDragging: boolean;
  zoomIn: () => void;
  zoomOut: () => void;
  resetView: () => void;
  fitToView: (treeWidth: number, treeHeight: number) => void;
  containerRef: React.RefObject<HTMLDivElement>;
}

const usePanZoom = (options: UsePanZoomOptions = {}): UsePanZoomReturn => {
  const {
    minScale = 0.1,
    maxScale = 4,
    zoomSensitivity = 0.001,
    panButton = 0,
  } = options;

  const containerRef = useRef<HTMLDivElement>(null);
  const lastMousePos = useRef<{ x: number; y: number } | null>(null);
  const lastTouchDistance = useRef<number | null>(null);
  const lastTouchCenter = useRef<{ x: number; y: number } | null>(null);

  const {
    transform,
    isDragging,
    setTransform,
    pan,
    zoom,
    resetView: storeResetView,
    fitToView: storeFitToView,
    setDragging,
  } = useTreeStore();

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button === panButton) {
        e.preventDefault();
        setDragging(true);
        lastMousePos.current = { x: e.clientX, y: e.clientY };
      }
    },
    [panButton, setDragging]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging || !lastMousePos.current) return;

      const dx = e.clientX - lastMousePos.current.x;
      const dy = e.clientY - lastMousePos.current.y;

      pan(dx, dy);
      lastMousePos.current = { x: e.clientX, y: e.clientY };
    },
    [isDragging, pan]
  );

  const handleMouseUp = useCallback(() => {
    setDragging(false);
    lastMousePos.current = null;
  }, [setDragging]);

  const handleMouseLeave = useCallback(() => {
    if (isDragging) {
      setDragging(false);
      lastMousePos.current = null;
    }
  }, [isDragging, setDragging]);

  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();

      const container = containerRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      // Calculate new scale
      const delta = -e.deltaY * zoomSensitivity;
      const newScale = Math.min(
        maxScale,
        Math.max(minScale, transform.scale * (1 + delta))
      );

      zoom(newScale, mouseX, mouseY);
    },
    [transform.scale, zoom, zoomSensitivity, minScale, maxScale]
  );

  // Touch handlers for mobile support
  const getTouchDistance = (touches: React.TouchList): number => {
    if (touches.length < 2) return 0;
    const dx = touches[0].clientX - touches[1].clientX;
    const dy = touches[0].clientY - touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const getTouchCenter = (
    touches: React.TouchList
  ): { x: number; y: number } => {
    if (touches.length === 1) {
      return { x: touches[0].clientX, y: touches[0].clientY };
    }
    return {
      x: (touches[0].clientX + touches[1].clientX) / 2,
      y: (touches[0].clientY + touches[1].clientY) / 2,
    };
  };

  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (e.touches.length === 1) {
        setDragging(true);
        lastTouchCenter.current = getTouchCenter(e.touches);
      } else if (e.touches.length === 2) {
        lastTouchDistance.current = getTouchDistance(e.touches);
        lastTouchCenter.current = getTouchCenter(e.touches);
      }
    },
    [setDragging]
  );

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      e.preventDefault();

      if (e.touches.length === 1 && isDragging && lastTouchCenter.current) {
        const center = getTouchCenter(e.touches);
        const dx = center.x - lastTouchCenter.current.x;
        const dy = center.y - lastTouchCenter.current.y;
        pan(dx, dy);
        lastTouchCenter.current = center;
      } else if (
        e.touches.length === 2 &&
        lastTouchDistance.current !== null &&
        lastTouchCenter.current
      ) {
        // Pinch to zoom
        const newDistance = getTouchDistance(e.touches);
        const newCenter = getTouchCenter(e.touches);

        const container = containerRef.current;
        if (container) {
          const rect = container.getBoundingClientRect();
          const centerX = newCenter.x - rect.left;
          const centerY = newCenter.y - rect.top;

          const scaleFactor = newDistance / lastTouchDistance.current;
          const newScale = Math.min(
            maxScale,
            Math.max(minScale, transform.scale * scaleFactor)
          );

          zoom(newScale, centerX, centerY);
        }

        // Also pan if center moved
        const dx = newCenter.x - lastTouchCenter.current.x;
        const dy = newCenter.y - lastTouchCenter.current.y;
        pan(dx, dy);

        lastTouchDistance.current = newDistance;
        lastTouchCenter.current = newCenter;
      }
    },
    [isDragging, pan, zoom, transform.scale, minScale, maxScale]
  );

  const handleTouchEnd = useCallback(() => {
    setDragging(false);
    lastTouchDistance.current = null;
    lastTouchCenter.current = null;
  }, [setDragging]);

  const zoomIn = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const newScale = Math.min(maxScale, transform.scale * 1.2);
    zoom(newScale, centerX, centerY);
  }, [transform.scale, zoom, maxScale]);

  const zoomOut = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const newScale = Math.max(minScale, transform.scale / 1.2);
    zoom(newScale, centerX, centerY);
  }, [transform.scale, zoom, minScale]);

  const resetView = useCallback(() => {
    storeResetView();
  }, [storeResetView]);

  const fitToView = useCallback(
    (treeWidth: number, treeHeight: number) => {
      const container = containerRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      storeFitToView(rect.width, rect.height, treeWidth, treeHeight);
    },
    [storeFitToView]
  );

  // Prevent default wheel behavior on container
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const preventDefaultWheel = (e: WheelEvent) => {
      e.preventDefault();
    };

    container.addEventListener('wheel', preventDefaultWheel, { passive: false });

    return () => {
      container.removeEventListener('wheel', preventDefaultWheel);
    };
  }, []);

  const handlers: PanZoomHandlers = {
    onMouseDown: handleMouseDown,
    onMouseMove: handleMouseMove,
    onMouseUp: handleMouseUp,
    onMouseLeave: handleMouseLeave,
    onWheel: handleWheel,
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
  };

  return {
    handlers,
    transform,
    isDragging,
    zoomIn,
    zoomOut,
    resetView,
    fitToView,
    containerRef,
  };
};

export default usePanZoom;
