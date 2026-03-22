/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Upload and Style Spatial Layer page.
 * Allows uploading shapefiles, processing to vector tiles, and styling in Maputnik.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardBody,
  CardHeader,
  FormControl,
  FormLabel,
  FormHelperText,
  Input,
  Button,
  useToast,
  useColorModeValue,
  Alert,
  AlertIcon,
  Badge,
  Spinner,
  Divider,
  Icon,
  Progress,
  Link,
} from '@chakra-ui/react';
import {
  AddIcon,
  ExternalLinkIcon,
  CheckCircleIcon,
  WarningIcon,
  TimeIcon,
  DeleteIcon,
} from '@chakra-ui/icons';
import { apiClient } from '../api/client';

interface LayerUploadSession {
  id: number;
  layer: {
    id: number;
    unique_id: string;
    name: string;
  };
  status: 'pending' | 'processing' | 'success' | 'failed';
  progress: number;
  created_at: string;
  created_by: string;
  maputnik_url?: string;
  error_message?: string;
  status_display?: string;
}

// Helper to format time elapsed
const formatTimeElapsed = (startTime: string): string => {
  const start = new Date(startTime).getTime();
  const now = Date.now();
  const elapsed = Math.floor((now - start) / 1000);

  if (elapsed < 60) return `${elapsed}s`;
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
  return `${Math.floor(elapsed / 3600)}h ${Math.floor((elapsed % 3600) / 60)}m`;
};

const SpatialLayerUploadPage: React.FC = () => {
  const toast = useToast();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');
  const processingRef = React.useRef<HTMLDivElement>(null);

  const [layerName, setLayerName] = useState('');
  const [files, setFiles] = useState<FileList | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadSessions, setUploadSessions] = useState<LayerUploadSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [, setTick] = useState(0); // Force re-render for time elapsed
  const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set());
  const [isClearingFailed, setIsClearingFailed] = useState(false);

  // Chunk size for large file uploads (5MB)
  const CHUNK_SIZE = 5 * 1024 * 1024;

  // Fetch upload sessions
  const fetchUploadSessions = useCallback(async () => {
    try {
      const response = await apiClient.get<{ data: LayerUploadSession[] }>(
        'spatial-layers/upload-sessions/'
      );
      setUploadSessions(response.data?.data || []);
    } catch (error) {
      console.error('Failed to fetch upload sessions:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Check if there are any processing sessions
  const hasProcessingSessions = uploadSessions.some(
    (s) => s.status === 'pending' || s.status === 'processing'
  );

  useEffect(() => {
    fetchUploadSessions();
    // Poll more frequently when there are processing sessions
    const pollInterval = hasProcessingSessions ? 2000 : 10000;
    const interval = setInterval(fetchUploadSessions, pollInterval);
    return () => clearInterval(interval);
  }, [fetchUploadSessions, hasProcessingSessions]);

  // Update time elapsed display every second when processing
  useEffect(() => {
    if (!hasProcessingSessions) return;
    const timer = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(timer);
  }, [hasProcessingSessions]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(e.target.files);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!layerName.trim()) {
      toast({
        title: 'Name required',
        description: 'Please enter a name for the layer.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (!files || files.length === 0) {
      toast({
        title: 'Files required',
        description: 'Please select shapefile files to upload.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus('Preparing files...');

    try {
      // Calculate total size
      let totalSize = 0;
      for (let i = 0; i < files.length; i++) {
        totalSize += files[i].size;
      }

      // For smaller files (< 10MB total), use simple upload
      if (totalSize < 10 * 1024 * 1024) {
        setUploadStatus('Uploading files...');
        const formData = new FormData();
        formData.append('name', layerName);
        for (let i = 0; i < files.length; i++) {
          formData.append('files', files[i]);
        }

        await apiClient.post('spatial-layers/upload/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded / progressEvent.total) * 100)
              : 0;
            setUploadProgress(progress);
          },
        });
      } else {
        // For larger files, use chunked upload
        setUploadStatus('Starting chunked upload...');

        // Generate a unique upload ID
        const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // First, initiate the upload session
        const initResponse = await apiClient.post('spatial-layers/upload/init/', {
          name: layerName,
          upload_id: uploadId,
          total_size: totalSize,
          file_count: files.length,
          file_names: Array.from(files).map(f => f.name),
        });

        if (!initResponse.data?.session_id) {
          throw new Error('Failed to initialize upload session');
        }

        const sessionId = initResponse.data.session_id;
        let uploadedBytes = 0;

        // Upload each file in chunks
        for (let fileIndex = 0; fileIndex < files.length; fileIndex++) {
          const file = files[fileIndex];
          const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

          setUploadStatus(`Uploading ${file.name} (${fileIndex + 1}/${files.length})...`);

          for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
            const start = chunkIndex * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const chunk = file.slice(start, end);

            const chunkFormData = new FormData();
            chunkFormData.append('session_id', sessionId);
            chunkFormData.append('file_name', file.name);
            chunkFormData.append('chunk_index', chunkIndex.toString());
            chunkFormData.append('total_chunks', totalChunks.toString());
            chunkFormData.append('chunk', chunk);

            await apiClient.post('spatial-layers/upload/chunk/', chunkFormData, {
              headers: {
                'Content-Type': 'multipart/form-data',
              },
            });

            uploadedBytes += (end - start);
            const progress = Math.round((uploadedBytes / totalSize) * 100);
            setUploadProgress(progress);
          }
        }

        // Finalize the upload
        setUploadStatus('Finalizing upload...');
        await apiClient.post('spatial-layers/upload/finalize/', {
          session_id: sessionId,
        });
      }

      toast({
        title: 'Upload started',
        description: 'Your layer is being processed. Monitor progress below.',
        status: 'success',
        duration: 5000,
      });

      setLayerName('');
      setFiles(null);
      setUploadProgress(0);
      setUploadStatus('');
      // Reset file input
      const fileInput = document.getElementById('spatial-layer-files') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      // Refresh sessions immediately
      await fetchUploadSessions();

      // Scroll to processing section
      setTimeout(() => {
        processingRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (error: any) {
      toast({
        title: 'Upload failed',
        description: error.response?.data?.message || 'Failed to upload layer.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      setUploadStatus('');
    }
  };

  const handleDeleteSession = async (sessionId: number, layerName: string) => {
    if (!confirm(`Are you sure you want to delete "${layerName}"? This cannot be undone.`)) {
      return;
    }

    setDeletingIds((prev) => new Set(prev).add(sessionId));

    try {
      await apiClient.delete(`spatial-layers/${sessionId}/`);
      toast({
        title: 'Session deleted',
        description: `"${layerName}" has been removed.`,
        status: 'success',
        duration: 3000,
      });
      await fetchUploadSessions();
    } catch (error: any) {
      toast({
        title: 'Delete failed',
        description: error.response?.data?.message || 'Failed to delete session.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setDeletingIds((prev) => {
        const next = new Set(prev);
        next.delete(sessionId);
        return next;
      });
    }
  };

  const handleClearAllFailed = async () => {
    const failedCount = uploadSessions.filter((s) => s.status === 'failed').length;
    if (!confirm(`Are you sure you want to delete all ${failedCount} failed upload(s)? This cannot be undone.`)) {
      return;
    }

    setIsClearingFailed(true);

    try {
      const response = await apiClient.delete<{ message: string; count: number }>(
        'spatial-layers/clear-failed/'
      );
      toast({
        title: 'Failed sessions cleared',
        description: response.data?.message || 'All failed sessions removed.',
        status: 'success',
        duration: 3000,
      });
      await fetchUploadSessions();
    } catch (error: any) {
      toast({
        title: 'Clear failed',
        description: error.response?.data?.message || 'Failed to clear sessions.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsClearingFailed(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge colorScheme="green" leftIcon={<CheckCircleIcon />}>Success</Badge>;
      case 'processing':
        return <Badge colorScheme="blue" leftIcon={<TimeIcon />}>Processing</Badge>;
      case 'failed':
        return <Badge colorScheme="red" leftIcon={<WarningIcon />}>Failed</Badge>;
      default:
        return <Badge colorScheme="gray">Pending</Badge>;
    }
  };

  const processingSessions = uploadSessions.filter(
    (s) => s.status === 'pending' || s.status === 'processing'
  );
  const completedSessions = uploadSessions.filter(
    (s) => s.status === 'success' || s.status === 'failed'
  );

  return (
    <Box h="100%" overflowY="auto">
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <VStack align="start" spacing={1}>
            <HStack>
              <AddIcon />
              <Heading size="lg">Upload and Style Spatial Layer</Heading>
            </HStack>
            <Text opacity={0.9}>
              Upload shapefiles to create vector tile layers, then style them in Maputnik
            </Text>
          </VStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* Requirements Alert */}
          <Alert status="warning" borderRadius="md">
            <AlertIcon />
            <Box>
              <Text fontWeight="bold">Requirements</Text>
              <Text fontSize="sm">
                Ensure the file's coordinate system uses the EPSG:4326 projection.
                Currently, only shapefiles are supported (upload all .shp, .shx, .dbf, .prj files together).
              </Text>
            </Box>
          </Alert>

          {/* Upload Form */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Upload New Layer</Heading>
            </CardHeader>
            <CardBody>
              <form onSubmit={handleSubmit}>
                <VStack spacing={4} align="stretch">
                  <FormControl isRequired>
                    <FormLabel>Layer Name</FormLabel>
                    <Input
                      value={layerName}
                      onChange={(e) => setLayerName(e.target.value)}
                      placeholder="Enter a name for this layer"
                    />
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel>Shapefile Files</FormLabel>
                    <Input
                      id="spatial-layer-files"
                      type="file"
                      multiple
                      accept=".shp,.shx,.dbf,.prj,.cpg,.sbn,.sbx"
                      onChange={handleFileChange}
                      p={1}
                    />
                    <FormHelperText>
                      Select all shapefile components (.shp, .shx, .dbf, .prj, etc.)
                    </FormHelperText>
                  </FormControl>

                  {/* Upload progress */}
                  {isUploading && (
                    <Box>
                      <HStack justify="space-between" mb={2}>
                        <Text fontSize="sm" color="blue.600">
                          {uploadStatus || 'Uploading...'}
                        </Text>
                        <Text fontSize="sm" fontWeight="bold">
                          {uploadProgress}%
                        </Text>
                      </HStack>
                      <Progress
                        value={uploadProgress}
                        size="md"
                        colorScheme="brand"
                        borderRadius="md"
                        hasStripe
                        isAnimated
                      />
                    </Box>
                  )}

                  <Button
                    type="submit"
                    colorScheme="brand"
                    leftIcon={<AddIcon />}
                    isLoading={isUploading}
                    loadingText={uploadStatus || 'Uploading...'}
                    isDisabled={!layerName.trim() || !files || files.length === 0 || isUploading}
                  >
                    Upload Layer
                  </Button>
                </VStack>
              </form>
            </CardBody>
          </Card>

          {/* Processing Sessions */}
          {processingSessions.length > 0 && (
            <Card bg={cardBg} ref={processingRef} borderWidth={2} borderColor="blue.400">
              <CardHeader bg="blue.50">
                <HStack justify="space-between">
                  <HStack>
                    <Spinner size="sm" color="blue.500" />
                    <Heading size="md" color="blue.700">
                      Processing ({processingSessions.length})
                    </Heading>
                  </HStack>
                  <Badge colorScheme="blue" fontSize="sm">
                    Auto-refreshing every 2s
                  </Badge>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  {processingSessions.map((session) => (
                    <Box
                      key={session.id}
                      p={4}
                      borderWidth="1px"
                      borderRadius="md"
                      borderColor="blue.300"
                      bg="blue.50"
                    >
                      <HStack justify="space-between" mb={2}>
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="bold" fontSize="lg">{session.layer.name}</Text>
                          <Text fontSize="sm" color="blue.600">
                            {session.status_display || 'Processing...'}
                          </Text>
                        </VStack>
                        <VStack align="end" spacing={0}>
                          {getStatusBadge(session.status)}
                          <Text fontSize="xs" color="gray.500" mt={1}>
                            {formatTimeElapsed(session.created_at)} elapsed
                          </Text>
                        </VStack>
                      </HStack>
                      <Progress
                        value={session.progress || 0}
                        size="md"
                        colorScheme="blue"
                        borderRadius="md"
                        isIndeterminate={!session.progress || session.progress === 0}
                        mt={2}
                        hasStripe
                        isAnimated
                      />
                      {session.progress > 0 && (
                        <Text fontSize="xs" color="gray.600" mt={1} textAlign="right">
                          {session.progress}% complete
                        </Text>
                      )}
                      <Text fontSize="xs" color="gray.500" mt={2}>
                        Started: {new Date(session.created_at).toLocaleString()}
                      </Text>
                    </Box>
                  ))}
                </VStack>
                <Alert status="info" mt={4} borderRadius="md">
                  <AlertIcon />
                  <Text fontSize="sm">
                    Processing time depends on the size and complexity of your shapefile.
                    Large files may take several minutes. This page will automatically update when complete.
                  </Text>
                </Alert>
              </CardBody>
            </Card>
          )}

          {/* Completed Sessions */}
          {completedSessions.length > 0 && (
            <Card bg={cardBg}>
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">Processed Layers</Heading>
                  {completedSessions.some((s) => s.status === 'failed') && (
                    <Button
                      size="sm"
                      colorScheme="red"
                      variant="outline"
                      leftIcon={<DeleteIcon />}
                      onClick={handleClearAllFailed}
                      isLoading={isClearingFailed}
                      loadingText="Clearing..."
                    >
                      Clear All Failed
                    </Button>
                  )}
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  {completedSessions.map((session) => (
                    <Box
                      key={session.id}
                      p={4}
                      borderWidth="1px"
                      borderRadius="md"
                      borderColor={session.status === 'success' ? 'green.200' : 'red.200'}
                      bg={session.status === 'success' ? 'green.50' : 'red.50'}
                    >
                      <HStack justify="space-between" mb={2}>
                        <Text fontWeight="bold">{session.layer.name}</Text>
                        {getStatusBadge(session.status)}
                      </HStack>
                      <Text fontSize="sm" color="gray.600" mb={2}>
                        Uploaded: {new Date(session.created_at).toLocaleString()}
                      </Text>
                      {session.error_message && (
                        <Alert status="error" size="sm" mb={2}>
                          <AlertIcon />
                          <Text fontSize="sm">{session.error_message}</Text>
                        </Alert>
                      )}
                      <HStack spacing={2}>
                        {session.status === 'success' && session.maputnik_url && (
                          <Button
                            as={Link}
                            href={session.maputnik_url}
                            isExternal
                            colorScheme="purple"
                            size="sm"
                            leftIcon={<ExternalLinkIcon />}
                          >
                            Open Style Editor (Maputnik)
                          </Button>
                        )}
                        {session.status === 'failed' && (
                          <Button
                            colorScheme="red"
                            variant="outline"
                            size="sm"
                            leftIcon={<DeleteIcon />}
                            onClick={() => handleDeleteSession(session.id, session.layer.name)}
                            isLoading={deletingIds.has(session.id)}
                            loadingText="Deleting..."
                          >
                            Delete
                          </Button>
                        )}
                      </HStack>
                    </Box>
                  ))}
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Empty State */}
          {!isLoading && uploadSessions.length === 0 && (
            <Card bg={cardBg}>
              <CardBody>
                <VStack py={8} spacing={4}>
                  <Icon as={AddIcon} boxSize={12} color="gray.400" />
                  <Text color="gray.500" textAlign="center">
                    No layers uploaded yet. Upload a shapefile to get started.
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Next Steps */}
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            <Box>
              <Text fontWeight="bold">Next Steps</Text>
              <Text fontSize="sm">
                After styling your layer in Maputnik, you can publish it to the map using
                "Publish Spatial Layer on Map" or add it as a context layer for geocontext
                lookups using "Add Spatial Filter".
              </Text>
            </Box>
          </Alert>
        </VStack>
      </Container>
    </Box>
  );
};

export default SpatialLayerUploadPage;
