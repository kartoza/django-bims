/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Map Print Control - Export map as image or PDF
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useCallback } from 'react';
import {
  Box,
  Button,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Select,
  Input,
  VStack,
  HStack,
  Text,
  Checkbox,
  useDisclosure,
  useToast,
  Progress,
  Image,
} from '@chakra-ui/react';
import { DownloadIcon, ViewIcon } from '@chakra-ui/icons';
import { useMapStore } from '../../stores/mapStore';

interface PrintOptions {
  format: 'png' | 'jpeg' | 'pdf';
  quality: 'low' | 'medium' | 'high';
  size: 'current' | 'a4' | 'a3' | 'letter';
  orientation: 'landscape' | 'portrait';
  includeTitle: boolean;
  includeLegend: boolean;
  includeScaleBar: boolean;
  includeNorthArrow: boolean;
  title: string;
}

interface MapPrintControlProps {
  mapRef: React.RefObject<HTMLDivElement>;
}

const sizePresets = {
  current: { label: 'Current View', width: 0, height: 0 },
  a4: { label: 'A4', width: 210, height: 297 },
  a3: { label: 'A3', width: 297, height: 420 },
  letter: { label: 'Letter', width: 216, height: 279 },
};

const qualitySettings = {
  low: { dpi: 96, scale: 1 },
  medium: { dpi: 150, scale: 1.5 },
  high: { dpi: 300, scale: 2 },
};

export const MapPrintControl: React.FC<MapPrintControlProps> = ({ mapRef }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [options, setOptions] = useState<PrintOptions>({
    format: 'png',
    quality: 'medium',
    size: 'current',
    orientation: 'landscape',
    includeTitle: true,
    includeLegend: true,
    includeScaleBar: true,
    includeNorthArrow: true,
    title: 'BIMS Map Export',
  });

  const handleOptionChange = useCallback(
    (key: keyof PrintOptions, value: unknown) => {
      setOptions((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  const generatePreview = useCallback(async () => {
    if (!mapRef.current) return;

    setExportProgress(10);

    try {
      // Dynamic import for html2canvas
      const html2canvas = (await import('html2canvas')).default;

      setExportProgress(30);

      const canvas = await html2canvas(mapRef.current, {
        useCORS: true,
        allowTaint: true,
        scale: 1,
        logging: false,
      });

      setExportProgress(80);

      const dataUrl = canvas.toDataURL('image/png');
      setPreviewUrl(dataUrl);

      setExportProgress(100);
    } catch (error) {
      console.error('Failed to generate preview:', error);
      toast({
        title: 'Preview failed',
        description: 'Could not generate map preview',
        status: 'error',
        duration: 3000,
      });
    }
  }, [mapRef, toast]);

  const handleExport = useCallback(async () => {
    if (!mapRef.current) return;

    setIsExporting(true);
    setExportProgress(0);

    try {
      // Dynamic import for html2canvas
      const html2canvas = (await import('html2canvas')).default;

      setExportProgress(20);

      const quality = qualitySettings[options.quality];

      const canvas = await html2canvas(mapRef.current, {
        useCORS: true,
        allowTaint: true,
        scale: quality.scale,
        logging: false,
      });

      setExportProgress(60);

      // Create final canvas with title and legend if needed
      let finalCanvas = canvas;

      if (options.includeTitle) {
        const titleHeight = 40;
        const finalCtx = document.createElement('canvas');
        finalCtx.width = canvas.width;
        finalCtx.height = canvas.height + titleHeight;
        const ctx = finalCtx.getContext('2d');

        if (ctx) {
          // Draw white background for title
          ctx.fillStyle = 'white';
          ctx.fillRect(0, 0, finalCtx.width, titleHeight);

          // Draw title
          ctx.fillStyle = 'black';
          ctx.font = `bold ${16 * quality.scale}px Arial`;
          ctx.textAlign = 'center';
          ctx.fillText(options.title, finalCtx.width / 2, titleHeight / 2 + 6);

          // Draw map
          ctx.drawImage(canvas, 0, titleHeight);

          finalCanvas = finalCtx;
        }
      }

      setExportProgress(80);

      // Export based on format
      let dataUrl: string;
      let filename: string;

      if (options.format === 'png') {
        dataUrl = finalCanvas.toDataURL('image/png');
        filename = `bims-map-${Date.now()}.png`;
      } else if (options.format === 'jpeg') {
        dataUrl = finalCanvas.toDataURL('image/jpeg', 0.9);
        filename = `bims-map-${Date.now()}.jpg`;
      } else {
        // PDF export
        const { jsPDF } = await import('jspdf');
        const imgData = finalCanvas.toDataURL('image/jpeg', 0.9);

        const pdf = new jsPDF({
          orientation: options.orientation,
          unit: 'mm',
          format: options.size === 'current' ? 'a4' : options.size,
        });

        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = pdf.internal.pageSize.getHeight();

        const imgWidth = pdfWidth;
        const imgHeight = (finalCanvas.height * pdfWidth) / finalCanvas.width;

        pdf.addImage(imgData, 'JPEG', 0, 0, imgWidth, Math.min(imgHeight, pdfHeight));

        pdf.save(`bims-map-${Date.now()}.pdf`);

        setExportProgress(100);
        setIsExporting(false);

        toast({
          title: 'Export complete',
          description: 'Map exported as PDF',
          status: 'success',
          duration: 3000,
        });

        onClose();
        return;
      }

      // Download image
      const link = document.createElement('a');
      link.download = filename;
      link.href = dataUrl;
      link.click();

      setExportProgress(100);

      toast({
        title: 'Export complete',
        description: `Map exported as ${options.format.toUpperCase()}`,
        status: 'success',
        duration: 3000,
      });

      onClose();
    } catch (error) {
      console.error('Export failed:', error);
      toast({
        title: 'Export failed',
        description: 'Could not export map',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsExporting(false);
    }
  }, [mapRef, options, toast, onClose]);

  return (
    <>
      <IconButton
        aria-label="Export map"
        icon={<DownloadIcon />}
        size="sm"
        variant="solid"
        bg="white"
        shadow="md"
        onClick={onOpen}
      />

      <Modal isOpen={isOpen} onClose={onClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Export Map</ModalHeader>
          <ModalCloseButton />

          <ModalBody>
            <VStack spacing={4} align="stretch">
              {/* Preview */}
              {previewUrl && (
                <Box borderWidth={1} borderRadius="md" overflow="hidden">
                  <Image src={previewUrl} alt="Map preview" maxH="200px" w="100%" objectFit="contain" />
                </Box>
              )}

              <Button
                size="sm"
                leftIcon={<ViewIcon />}
                variant="outline"
                onClick={generatePreview}
              >
                Generate Preview
              </Button>

              <FormControl>
                <FormLabel fontSize="sm">Format</FormLabel>
                <Select
                  size="sm"
                  value={options.format}
                  onChange={(e) => handleOptionChange('format', e.target.value)}
                >
                  <option value="png">PNG (High Quality)</option>
                  <option value="jpeg">JPEG (Smaller File)</option>
                  <option value="pdf">PDF (Print Ready)</option>
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel fontSize="sm">Quality</FormLabel>
                <Select
                  size="sm"
                  value={options.quality}
                  onChange={(e) => handleOptionChange('quality', e.target.value)}
                >
                  <option value="low">Low (96 DPI)</option>
                  <option value="medium">Medium (150 DPI)</option>
                  <option value="high">High (300 DPI)</option>
                </Select>
              </FormControl>

              {options.format === 'pdf' && (
                <>
                  <FormControl>
                    <FormLabel fontSize="sm">Paper Size</FormLabel>
                    <Select
                      size="sm"
                      value={options.size}
                      onChange={(e) => handleOptionChange('size', e.target.value)}
                    >
                      {Object.entries(sizePresets).map(([key, preset]) => (
                        <option key={key} value={key}>
                          {preset.label}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl>
                    <FormLabel fontSize="sm">Orientation</FormLabel>
                    <Select
                      size="sm"
                      value={options.orientation}
                      onChange={(e) => handleOptionChange('orientation', e.target.value)}
                    >
                      <option value="landscape">Landscape</option>
                      <option value="portrait">Portrait</option>
                    </Select>
                  </FormControl>
                </>
              )}

              <FormControl>
                <FormLabel fontSize="sm">Title</FormLabel>
                <Input
                  size="sm"
                  value={options.title}
                  onChange={(e) => handleOptionChange('title', e.target.value)}
                  placeholder="Map title"
                />
              </FormControl>

              <VStack align="stretch" spacing={2}>
                <Checkbox
                  size="sm"
                  isChecked={options.includeTitle}
                  onChange={(e) => handleOptionChange('includeTitle', e.target.checked)}
                >
                  Include title
                </Checkbox>
                <Checkbox
                  size="sm"
                  isChecked={options.includeLegend}
                  onChange={(e) => handleOptionChange('includeLegend', e.target.checked)}
                >
                  Include legend
                </Checkbox>
                <Checkbox
                  size="sm"
                  isChecked={options.includeScaleBar}
                  onChange={(e) => handleOptionChange('includeScaleBar', e.target.checked)}
                >
                  Include scale bar
                </Checkbox>
              </VStack>

              {isExporting && (
                <Box>
                  <Text fontSize="sm" color="gray.500" mb={2}>
                    Exporting... {Math.round(exportProgress)}%
                  </Text>
                  <Progress value={exportProgress} size="sm" colorScheme="blue" />
                </Box>
              )}
            </VStack>
          </ModalBody>

          <ModalFooter>
            <HStack spacing={2}>
              <Button variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button
                colorScheme="blue"
                leftIcon={<DownloadIcon />}
                onClick={handleExport}
                isLoading={isExporting}
                loadingText="Exporting..."
              >
                Export
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default MapPrintControl;
