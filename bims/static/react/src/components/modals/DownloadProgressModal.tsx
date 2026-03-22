/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Download Progress Modal - Shows progress for data export tasks
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  Progress,
  Text,
  VStack,
  HStack,
  Icon,
  Box,
  Badge,
  Link,
  useToast,
  Spinner,
} from '@chakra-ui/react';
import {
  DownloadIcon,
  CheckCircleIcon,
  WarningIcon,
  TimeIcon,
} from '@chakra-ui/icons';
import { apiClient } from '../../api/client';

type TaskStatus = 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'REVOKED';

interface TaskState {
  task_id: string;
  status: TaskStatus;
  ready: boolean;
  progress?: number;
  result?: {
    file_url?: string;
    file_name?: string;
    record_count?: number;
    message?: string;
  };
  error?: string;
}

interface DownloadProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskId: string;
  title?: string;
  pollInterval?: number; // ms
}

const statusConfig: Record<TaskStatus, { color: string; icon: typeof TimeIcon; label: string }> = {
  PENDING: { color: 'gray', icon: TimeIcon, label: 'Queued' },
  STARTED: { color: 'blue', icon: Spinner, label: 'Processing' },
  SUCCESS: { color: 'green', icon: CheckCircleIcon, label: 'Complete' },
  FAILURE: { color: 'red', icon: WarningIcon, label: 'Failed' },
  REVOKED: { color: 'orange', icon: WarningIcon, label: 'Cancelled' },
};

export const DownloadProgressModal: React.FC<DownloadProgressModalProps> = ({
  isOpen,
  onClose,
  taskId,
  title = 'Download Progress',
  pollInterval = 2000,
}) => {
  const [taskState, setTaskState] = useState<TaskState | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const toast = useToast();

  // Poll task status
  useEffect(() => {
    if (!isOpen || !taskId || !isPolling) return;

    const pollStatus = async () => {
      try {
        const response = await apiClient.get<{ data: TaskState }>(
          `task-status/${taskId}/`
        );
        const state = response.data?.data;
        if (state) {
          setTaskState(state);

          // Stop polling if task is complete
          if (state.ready || state.status === 'SUCCESS' || state.status === 'FAILURE' || state.status === 'REVOKED') {
            setIsPolling(false);

            if (state.status === 'SUCCESS') {
              toast({
                title: 'Download ready',
                description: 'Your file is ready for download.',
                status: 'success',
                duration: 5000,
              });
            } else if (state.status === 'FAILURE') {
              toast({
                title: 'Download failed',
                description: state.error || 'An error occurred during processing.',
                status: 'error',
                duration: 5000,
              });
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll task status:', error);
      }
    };

    // Initial poll
    pollStatus();

    // Set up interval
    const intervalId = setInterval(pollStatus, pollInterval);

    return () => clearInterval(intervalId);
  }, [isOpen, taskId, isPolling, pollInterval, toast]);

  const handleDownload = useCallback(() => {
    if (taskState?.result?.file_url) {
      window.open(taskState.result.file_url, '_blank');
    }
  }, [taskState]);

  const handleCancel = useCallback(async () => {
    try {
      await apiClient.post(`task-revoke/${taskId}/`);
      setIsPolling(false);
      toast({
        title: 'Task cancelled',
        status: 'info',
        duration: 3000,
      });
    } catch (error) {
      console.error('Failed to cancel task:', error);
    }
  }, [taskId, toast]);

  const status = taskState?.status || 'PENDING';
  const config = statusConfig[status];
  const progress = taskState?.progress || 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered closeOnOverlayClick={false}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <HStack spacing={2}>
            <Icon as={DownloadIcon} color="brand.500" />
            <Text>{title}</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />

        <ModalBody>
          <VStack spacing={4} align="stretch">
            {/* Status Badge */}
            <HStack justify="center">
              <Badge colorScheme={config.color} fontSize="md" px={3} py={1}>
                <HStack spacing={2}>
                  <Icon as={config.icon} />
                  <Text>{config.label}</Text>
                </HStack>
              </Badge>
            </HStack>

            {/* Progress Bar */}
            {(status === 'STARTED' || status === 'PENDING') && (
              <Box>
                <Progress
                  value={progress}
                  size="lg"
                  colorScheme="blue"
                  hasStripe
                  isAnimated={status === 'STARTED'}
                  borderRadius="md"
                />
                <Text textAlign="center" fontSize="sm" color="gray.500" mt={2}>
                  {progress > 0 ? `${Math.round(progress)}% complete` : 'Preparing...'}
                </Text>
              </Box>
            )}

            {/* Task ID */}
            <Text fontSize="xs" color="gray.400" textAlign="center">
              Task ID: {taskId}
            </Text>

            {/* Success Result */}
            {status === 'SUCCESS' && taskState?.result && (
              <VStack spacing={2} p={4} bg="green.50" borderRadius="md">
                <Icon as={CheckCircleIcon} color="green.500" boxSize={8} />
                <Text fontWeight="medium" color="green.700">
                  Download Ready
                </Text>
                {taskState.result.record_count !== undefined && (
                  <Text fontSize="sm" color="green.600">
                    {taskState.result.record_count.toLocaleString()} records exported
                  </Text>
                )}
                {taskState.result.file_name && (
                  <Text fontSize="sm" color="gray.600">
                    {taskState.result.file_name}
                  </Text>
                )}
              </VStack>
            )}

            {/* Error Message */}
            {status === 'FAILURE' && (
              <VStack spacing={2} p={4} bg="red.50" borderRadius="md">
                <Icon as={WarningIcon} color="red.500" boxSize={8} />
                <Text fontWeight="medium" color="red.700">
                  Export Failed
                </Text>
                <Text fontSize="sm" color="red.600" textAlign="center">
                  {taskState?.error || 'An error occurred during processing.'}
                </Text>
              </VStack>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack spacing={2}>
            {(status === 'PENDING' || status === 'STARTED') && (
              <Button variant="ghost" colorScheme="red" onClick={handleCancel}>
                Cancel
              </Button>
            )}

            {status === 'SUCCESS' && taskState?.result?.file_url && (
              <Button
                colorScheme="green"
                leftIcon={<DownloadIcon />}
                onClick={handleDownload}
              >
                Download File
              </Button>
            )}

            <Button variant="ghost" onClick={onClose}>
              {status === 'SUCCESS' || status === 'FAILURE' ? 'Close' : 'Hide'}
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default DownloadProgressModal;
