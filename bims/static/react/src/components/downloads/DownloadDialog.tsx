/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Download Dialog - Request and track data downloads
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useCallback } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Text,
  Select,
  Textarea,
  FormControl,
  FormLabel,
  FormHelperText,
  Progress,
  Badge,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Icon,
  Spinner,
  Link,
  useColorModeValue,
} from '@chakra-ui/react';
import { DownloadIcon, CheckCircleIcon, WarningIcon } from '@chakra-ui/icons';
import { useDownloadRequest, useDownloadPurposes } from '../../hooks/useDownload';
import { useSearchStore } from '../../stores/searchStore';

interface DownloadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  downloadType?: 'csv' | 'checklist';
  taxonGroupId?: number;
  boundaryId?: number;
}

export const DownloadDialog: React.FC<DownloadDialogProps> = ({
  isOpen,
  onClose,
  downloadType = 'csv',
  taxonGroupId,
  boundaryId,
}) => {
  const [selectedPurpose, setSelectedPurpose] = useState<string>('');
  const [notes, setNotes] = useState('');

  const { purposes, isLoading: isLoadingPurposes } = useDownloadPurposes();
  const {
    requestDownload,
    isRequesting,
    error,
    taskId,
    taskStatus,
    isPolling,
  } = useDownloadRequest();
  const { filters } = useSearchStore();

  const bgColor = useColorModeValue('white', 'gray.800');

  // Convert search filters to download filters
  const buildFilters = useCallback(() => {
    const downloadFilters: Record<string, unknown> = {};

    if (filters.taxonGroups?.length) {
      downloadFilters.taxonGroups = filters.taxonGroups;
    }
    if (filters.yearFrom) {
      downloadFilters.startYear = filters.yearFrom;
    }
    if (filters.yearTo) {
      downloadFilters.endYear = filters.yearTo;
    }
    if (filters.iucnCategories?.length) {
      downloadFilters.conservationStatus = filters.iucnCategories;
    }
    if (filters.endemism?.length) {
      downloadFilters.endemism = filters.endemism;
    }
    if (filters.boundaryId) {
      downloadFilters.boundaryId = filters.boundaryId;
    }

    return downloadFilters;
  }, [filters]);

  const handleDownload = async () => {
    if (!selectedPurpose) {
      return;
    }

    await requestDownload({
      type: downloadType,
      filters: downloadType === 'csv' ? buildFilters() : undefined,
      taxonGroupId: downloadType === 'checklist' ? taxonGroupId : undefined,
      boundaryId: downloadType === 'checklist' ? boundaryId : undefined,
    });
  };

  const handleClose = () => {
    setSelectedPurpose('');
    setNotes('');
    onClose();
  };

  const getStatusBadge = () => {
    if (!taskStatus) return null;

    const statusColors: Record<string, string> = {
      PENDING: 'yellow',
      STARTED: 'blue',
      SUCCESS: 'green',
      FAILURE: 'red',
      REVOKED: 'gray',
    };

    return (
      <Badge colorScheme={statusColors[taskStatus.status] || 'gray'}>
        {taskStatus.status}
      </Badge>
    );
  };

  const renderContent = () => {
    // Show success state
    if (taskStatus?.status === 'SUCCESS' && taskStatus.result?.download_url) {
      return (
        <VStack spacing={4} align="stretch">
          <Alert status="success" borderRadius="md">
            <AlertIcon as={CheckCircleIcon} />
            <VStack align="start" spacing={1}>
              <AlertTitle>Download Ready!</AlertTitle>
              <AlertDescription>
                Your download is ready. Click the button below to download your file.
              </AlertDescription>
            </VStack>
          </Alert>
          <Button
            as={Link}
            href={taskStatus.result.download_url}
            target="_blank"
            download
            colorScheme="green"
            leftIcon={<DownloadIcon />}
          >
            Download File
          </Button>
        </VStack>
      );
    }

    // Show processing state
    if (taskId && isPolling) {
      return (
        <VStack spacing={4} align="stretch">
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            <VStack align="start" spacing={1} flex={1}>
              <HStack justify="space-between" width="100%">
                <AlertTitle>Processing Download</AlertTitle>
                {getStatusBadge()}
              </HStack>
              <AlertDescription>
                Your download is being processed. This may take a few moments
                depending on the size of the data.
              </AlertDescription>
            </VStack>
          </Alert>
          <HStack spacing={4}>
            <Spinner size="sm" />
            <Text fontSize="sm" color="gray.500">
              Task ID: {taskId}
            </Text>
          </HStack>
          <Progress size="sm" isIndeterminate colorScheme="blue" />
        </VStack>
      );
    }

    // Show error state
    if (error || taskStatus?.status === 'FAILURE') {
      return (
        <VStack spacing={4} align="stretch">
          <Alert status="error" borderRadius="md">
            <AlertIcon as={WarningIcon} />
            <VStack align="start" spacing={1}>
              <AlertTitle>Download Failed</AlertTitle>
              <AlertDescription>
                {error || taskStatus?.error || 'An unexpected error occurred'}
              </AlertDescription>
            </VStack>
          </Alert>
          <Button variant="outline" onClick={() => handleDownload()}>
            Try Again
          </Button>
        </VStack>
      );
    }

    // Show request form
    return (
      <VStack spacing={4} align="stretch">
        <FormControl isRequired>
          <FormLabel>Purpose</FormLabel>
          <Select
            placeholder="Select download purpose"
            value={selectedPurpose}
            onChange={(e) => setSelectedPurpose(e.target.value)}
            isDisabled={isLoadingPurposes}
          >
            {purposes.map((purpose) => (
              <option key={purpose.id} value={purpose.id}>
                {purpose.name}
              </option>
            ))}
          </Select>
          <FormHelperText>
            Please indicate the purpose of your download
          </FormHelperText>
        </FormControl>

        <FormControl>
          <FormLabel>Additional Notes</FormLabel>
          <Textarea
            placeholder="Any additional information about your download request..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
          />
        </FormControl>

        {/* Filter summary */}
        {downloadType === 'csv' && Object.keys(buildFilters()).length > 0 && (
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            <VStack align="start" spacing={1}>
              <AlertTitle fontSize="sm">Active Filters</AlertTitle>
              <AlertDescription fontSize="xs">
                {Object.entries(buildFilters()).map(([key, value]) => (
                  <Text key={key}>
                    <strong>{key}:</strong> {Array.isArray(value) ? value.join(', ') : String(value)}
                  </Text>
                ))}
              </AlertDescription>
            </VStack>
          </Alert>
        )}
      </VStack>
    );
  };

  const showRequestForm = !taskId && !isPolling && taskStatus?.status !== 'SUCCESS';

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="md">
      <ModalOverlay />
      <ModalContent bg={bgColor}>
        <ModalHeader>
          <HStack spacing={2}>
            <Icon as={DownloadIcon} />
            <Text>
              {downloadType === 'csv' ? 'Download Occurrence Data' : 'Download Checklist'}
            </Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />

        <ModalBody>{renderContent()}</ModalBody>

        <ModalFooter>
          {showRequestForm ? (
            <HStack spacing={3}>
              <Button variant="ghost" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                colorScheme="blue"
                leftIcon={<DownloadIcon />}
                onClick={handleDownload}
                isLoading={isRequesting}
                isDisabled={!selectedPurpose}
              >
                Request Download
              </Button>
            </HStack>
          ) : (
            <Button onClick={handleClose}>
              {taskStatus?.status === 'SUCCESS' ? 'Done' : 'Close'}
            </Button>
          )}
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default DownloadDialog;
