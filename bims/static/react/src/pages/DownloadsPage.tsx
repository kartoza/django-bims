/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Download requests management page.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardBody,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Spinner,
  Center,
  IconButton,
  Progress,
  useToast,
  useDisclosure,
  Flex,
  Spacer,
  Link,
} from '@chakra-ui/react';
import {
  DownloadIcon,
  DeleteIcon,
  RepeatIcon,
  CheckCircleIcon,
  TimeIcon,
  WarningIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink } from 'react-router-dom';
import { downloadsApi, tasksApi } from '../api/client';
import TaxaListDownloadModal from '../components/TaxaListDownloadModal';

interface DownloadRequest {
  id: string;
  task_id: string;
  type: 'csv' | 'checklist' | 'shapefile';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  file_url?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  filters?: Record<string, unknown>;
  record_count?: number;
}

const DownloadsPage: React.FC = () => {
  const [downloads, setDownloads] = useState<DownloadRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const toast = useToast();
  const { isOpen: isTaxaModalOpen, onOpen: onTaxaModalOpen, onClose: onTaxaModalClose } = useDisclosure();

  useEffect(() => {
    fetchDownloads();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchDownloads, 5000);
    return () => clearInterval(interval);
  }, [page]);

  const fetchDownloads = async () => {
    try {
      // This would fetch from a downloads list endpoint
      // For now, using mock data structure
      const response = await fetch(`/api/v1/downloads/?page=${page}`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setDownloads(data.data || []);
        setTotalPages(data.meta?.total_pages || 1);
      }
    } catch (error) {
      console.error('Failed to fetch downloads:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (taskId: string) => {
    try {
      await tasksApi.cancel(taskId);
      toast({
        title: 'Download cancelled',
        status: 'info',
        duration: 3000,
      });
      fetchDownloads();
    } catch (error) {
      toast({
        title: 'Failed to cancel download',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="green.500" />;
      case 'processing':
      case 'pending':
        return <TimeIcon color="blue.500" />;
      case 'failed':
        return <WarningIcon color="red.500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    const colorScheme = {
      completed: 'green',
      processing: 'blue',
      pending: 'yellow',
      failed: 'red',
    }[status] || 'gray';

    return <Badge colorScheme={colorScheme}>{status}</Badge>;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box h="100%" overflowY="auto">
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Flex align="center">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Download Requests</Heading>
            <Text color="gray.600">
              Manage your data download requests
            </Text>
          </VStack>
          <Spacer />
          <Button
            leftIcon={<RepeatIcon />}
            onClick={fetchDownloads}
            variant="outline"
            size="sm"
          >
            Refresh
          </Button>
        </Flex>

        {/* Download Options */}
        <Card>
          <CardBody>
            <Heading size="sm" mb={4}>
              Request New Download
            </Heading>
            <HStack spacing={4} flexWrap="wrap">
              <Button
                as={RouterLink}
                to="/map"
                leftIcon={<DownloadIcon />}
                colorScheme="brand"
              >
                Export from Map Search
              </Button>
              <Button
                leftIcon={<DownloadIcon />}
                variant="outline"
                onClick={onTaxaModalOpen}
              >
                Download Taxa Checklist
              </Button>
            </HStack>
          </CardBody>
        </Card>

        {/* Downloads Table */}
        <Card>
          <CardBody p={0}>
            {loading ? (
              <Center py={12}>
                <Spinner size="xl" color="brand.500" />
              </Center>
            ) : downloads.length === 0 ? (
              <Center py={12}>
                <VStack>
                  <DownloadIcon boxSize={12} color="gray.300" />
                  <Text color="gray.500">No download requests yet</Text>
                  <Text color="gray.400" fontSize="sm">
                    Use the map search to export data
                  </Text>
                </VStack>
              </Center>
            ) : (
              <Box overflowX="auto">
                <Table variant="simple">
                  <Thead bg="gray.50">
                    <Tr>
                      <Th>Type</Th>
                      <Th>Status</Th>
                      <Th>Progress</Th>
                      <Th>Records</Th>
                      <Th>Created</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {downloads.map((download) => (
                      <Tr key={download.id} _hover={{ bg: 'gray.50' }}>
                        <Td>
                          <HStack>
                            {getStatusIcon(download.status)}
                            <Text fontWeight="500" textTransform="capitalize">
                              {download.type}
                            </Text>
                          </HStack>
                        </Td>
                        <Td>{getStatusBadge(download.status)}</Td>
                        <Td w="150px">
                          {download.status === 'processing' ? (
                            <Progress
                              value={download.progress}
                              size="sm"
                              colorScheme="brand"
                              hasStripe
                              isAnimated
                            />
                          ) : download.status === 'completed' ? (
                            <Text color="green.500">100%</Text>
                          ) : download.status === 'failed' ? (
                            <Text color="red.500" fontSize="sm" noOfLines={1}>
                              {download.error_message || 'Failed'}
                            </Text>
                          ) : (
                            <Text color="gray.500">Waiting...</Text>
                          )}
                        </Td>
                        <Td>
                          {download.record_count ? (
                            <Badge colorScheme="blue">{download.record_count}</Badge>
                          ) : (
                            '-'
                          )}
                        </Td>
                        <Td>
                          <Text fontSize="sm">{formatDate(download.created_at)}</Text>
                        </Td>
                        <Td>
                          <HStack spacing={1}>
                            {download.status === 'completed' && download.file_url && (
                              <Button
                                as="a"
                                href={download.file_url}
                                download
                                size="sm"
                                colorScheme="green"
                                leftIcon={<DownloadIcon />}
                              >
                                Download
                              </Button>
                            )}
                            {(download.status === 'pending' ||
                              download.status === 'processing') && (
                              <IconButton
                                aria-label="Cancel"
                                icon={<DeleteIcon />}
                                size="sm"
                                variant="ghost"
                                colorScheme="red"
                                onClick={() => handleCancel(download.task_id)}
                              />
                            )}
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            )}
          </CardBody>
        </Card>

        {/* Pagination */}
        {totalPages > 1 && (
          <HStack justify="center" spacing={4}>
            <IconButton
              aria-label="Previous page"
              icon={<ChevronLeftIcon />}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              isDisabled={page === 1}
            />
            <Text>
              Page {page} of {totalPages}
            </Text>
            <IconButton
              aria-label="Next page"
              icon={<ChevronRightIcon />}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              isDisabled={page === totalPages}
            />
          </HStack>
        )}
      </VStack>

      {/* Taxa List Download Modal */}
      <TaxaListDownloadModal
        isOpen={isTaxaModalOpen}
        onClose={onTaxaModalClose}
      />
    </Container>
    </Box>
  );
};

export default DownloadsPage;
