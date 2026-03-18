/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Data upload page with multiple upload types.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useRef } from 'react';
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
  Button,
  Input,
  FormControl,
  FormLabel,
  FormHelperText,
  Select,
  Progress,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast,
  Icon,
  Flex,
  Spacer,
  Link,
  Badge,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  List,
  ListItem,
  ListIcon,
  Divider,
} from '@chakra-ui/react';
import {
  DownloadIcon,
  CheckCircleIcon,
  WarningIcon,
  InfoIcon,
  AttachmentIcon,
} from '@chakra-ui/icons';
import { useParams, Link as RouterLink } from 'react-router-dom';

interface UploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  error: string | null;
  success: boolean;
  validationErrors: string[];
  taskId: string | null;
}

const UploadPage: React.FC = () => {
  const { type = 'occurrence' } = useParams<{ type: string }>();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  const [state, setState] = useState<UploadState>({
    file: null,
    uploading: false,
    progress: 0,
    error: null,
    success: false,
    validationErrors: [],
    taskId: null,
  });

  const [taxonGroup, setTaxonGroup] = useState('');

  const uploadTypes = {
    occurrence: {
      title: 'Occurrence Data Upload',
      description: 'Upload biodiversity occurrence records from CSV files',
      templateUrl: '/download-occurrence-template/',
      acceptedFormats: '.csv',
      endpoint: '/api/upload/occurrence/',
    },
    taxa: {
      title: 'Taxonomic Data Upload',
      description: 'Upload taxonomy data including species information',
      templateUrl: '/download-taxa-template/',
      acceptedFormats: '.csv',
      endpoint: '/api/upload/taxa/',
    },
    'physico-chemical': {
      title: 'Physico-Chemical Data Upload',
      description: 'Upload water quality and chemical analysis data',
      templateUrl: '/download-occurrence-template/',
      acceptedFormats: '.csv',
      endpoint: '/api/upload/physico-chemical/',
    },
    'water-temperature': {
      title: 'Water Temperature Upload',
      description: 'Upload water temperature monitoring data',
      templateUrl: '/download-occurrence-template/',
      acceptedFormats: '.csv',
      endpoint: '/api/upload/water-temperature/',
    },
    shapefile: {
      title: 'Shapefile Upload',
      description: 'Upload shapefiles for boundary or spatial data',
      templateUrl: null,
      acceptedFormats: '.zip',
      endpoint: '/api/upload/shapefile/',
    },
    'spatial-layer': {
      title: 'Spatial Layer Upload',
      description: 'Upload and publish spatial visualization layers',
      templateUrl: null,
      acceptedFormats: '.zip,.geojson',
      endpoint: '/api/upload/spatial-layer/',
    },
  };

  const config = uploadTypes[type as keyof typeof uploadTypes] || uploadTypes.occurrence;

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setState({
        ...state,
        file,
        error: null,
        success: false,
        validationErrors: [],
      });
    }
  };

  const handleUpload = async () => {
    if (!state.file) {
      toast({
        title: 'No file selected',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setState({ ...state, uploading: true, progress: 0, error: null });

    const formData = new FormData();
    formData.append('file', state.file);
    if (taxonGroup) {
      formData.append('taxon_group', taxonGroup);
    }

    try {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setState((prev) => ({ ...prev, progress }));
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const response = JSON.parse(xhr.responseText);
          setState((prev) => ({
            ...prev,
            uploading: false,
            success: true,
            taskId: response.task_id,
          }));
          toast({
            title: 'Upload successful',
            description: 'Your file is being processed',
            status: 'success',
            duration: 5000,
          });
        } else {
          const response = JSON.parse(xhr.responseText);
          setState((prev) => ({
            ...prev,
            uploading: false,
            error: response.error || 'Upload failed',
            validationErrors: response.validation_errors || [],
          }));
        }
      });

      xhr.addEventListener('error', () => {
        setState((prev) => ({
          ...prev,
          uploading: false,
          error: 'Network error occurred',
        }));
      });

      xhr.open('POST', config.endpoint);
      xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
      xhr.send(formData);
    } catch (error) {
      setState((prev) => ({
        ...prev,
        uploading: false,
        error: 'Upload failed',
      }));
    }
  };

  const getCsrfToken = (): string => {
    const cookie = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  };

  const resetUpload = () => {
    setState({
      file: null,
      uploading: false,
      progress: 0,
      error: null,
      success: false,
      validationErrors: [],
      taskId: null,
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Container maxW="container.lg" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            {config.title}
          </Heading>
          <Text color="gray.600">{config.description}</Text>
        </Box>

        {/* Upload Type Tabs */}
        <Tabs variant="enclosed" colorScheme="brand">
          <TabList flexWrap="wrap">
            <Tab as={RouterLink} to="/upload/occurrence">
              Occurrence
            </Tab>
            <Tab as={RouterLink} to="/upload/taxa">
              Taxonomy
            </Tab>
            <Tab as={RouterLink} to="/upload/physico-chemical">
              Physico-Chemical
            </Tab>
            <Tab as={RouterLink} to="/upload/water-temperature">
              Water Temp
            </Tab>
            <Tab as={RouterLink} to="/upload/shapefile">
              Shapefile
            </Tab>
            <Tab as={RouterLink} to="/upload/spatial-layer">
              Spatial Layer
            </Tab>
          </TabList>
        </Tabs>

        <Flex gap={8} direction={{ base: 'column', lg: 'row' }}>
          {/* Upload Form */}
          <Card flex="2">
            <CardHeader>
              <Heading size="md">Upload File</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={6} align="stretch">
                {/* Taxon Group Selection (for occurrence data) */}
                {type === 'occurrence' && (
                  <FormControl>
                    <FormLabel>Taxon Group</FormLabel>
                    <Select
                      placeholder="Select taxon group"
                      value={taxonGroup}
                      onChange={(e) => setTaxonGroup(e.target.value)}
                    >
                      <option value="fish">Fish</option>
                      <option value="invertebrates">Invertebrates</option>
                      <option value="algae">Algae</option>
                      <option value="amphibians">Amphibians</option>
                      <option value="odonata">Odonata</option>
                    </Select>
                    <FormHelperText>
                      Select the taxonomic group for your data
                    </FormHelperText>
                  </FormControl>
                )}

                {/* File Input */}
                <FormControl>
                  <FormLabel>Select File</FormLabel>
                  <Input
                    ref={fileInputRef}
                    type="file"
                    accept={config.acceptedFormats}
                    onChange={handleFileSelect}
                    p={1}
                    height="auto"
                  />
                  <FormHelperText>
                    Accepted formats: {config.acceptedFormats}
                  </FormHelperText>
                </FormControl>

                {/* Selected File Info */}
                {state.file && (
                  <HStack p={3} bg="gray.50" rounded="md">
                    <Icon as={AttachmentIcon} color="brand.500" />
                    <Text>{state.file.name}</Text>
                    <Badge colorScheme="blue">
                      {(state.file.size / 1024 / 1024).toFixed(2)} MB
                    </Badge>
                  </HStack>
                )}

                {/* Progress */}
                {state.uploading && (
                  <Box>
                    <Text mb={2}>Uploading... {state.progress}%</Text>
                    <Progress
                      value={state.progress}
                      colorScheme="brand"
                      hasStripe
                      isAnimated
                    />
                  </Box>
                )}

                {/* Error */}
                {state.error && (
                  <Alert status="error" rounded="md">
                    <AlertIcon />
                    <Box>
                      <AlertTitle>Upload Error</AlertTitle>
                      <AlertDescription>{state.error}</AlertDescription>
                    </Box>
                  </Alert>
                )}

                {/* Validation Errors */}
                {state.validationErrors.length > 0 && (
                  <Alert status="warning" rounded="md">
                    <AlertIcon />
                    <Box>
                      <AlertTitle>Validation Issues</AlertTitle>
                      <List spacing={1} mt={2}>
                        {state.validationErrors.map((err, idx) => (
                          <ListItem key={idx} fontSize="sm">
                            <ListIcon as={WarningIcon} color="orange.500" />
                            {err}
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </Alert>
                )}

                {/* Success */}
                {state.success && (
                  <Alert status="success" rounded="md">
                    <AlertIcon />
                    <Box>
                      <AlertTitle>Upload Successful</AlertTitle>
                      <AlertDescription>
                        Your file has been uploaded and is being processed.
                        {state.taskId && (
                          <Link
                            as={RouterLink}
                            to={`/downloads?task=${state.taskId}`}
                            color="green.600"
                            ml={2}
                          >
                            View Status
                          </Link>
                        )}
                      </AlertDescription>
                    </Box>
                  </Alert>
                )}

                {/* Actions */}
                <HStack>
                  <Button
                    colorScheme="brand"
                    onClick={handleUpload}
                    isLoading={state.uploading}
                    isDisabled={!state.file || state.uploading}
                  >
                    Upload File
                  </Button>
                  {(state.file || state.success || state.error) && (
                    <Button variant="outline" onClick={resetUpload}>
                      Reset
                    </Button>
                  )}
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Instructions */}
          <Card flex="1">
            <CardHeader>
              <Heading size="md">Instructions</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Box>
                  <Text fontWeight="600" mb={2}>
                    1. Download Template
                  </Text>
                  {config.templateUrl ? (
                    <Button
                      as="a"
                      href={config.templateUrl}
                      size="sm"
                      leftIcon={<DownloadIcon />}
                      variant="outline"
                    >
                      Download Template
                    </Button>
                  ) : (
                    <Text fontSize="sm" color="gray.500">
                      No template required for this upload type
                    </Text>
                  )}
                </Box>

                <Divider />

                <Box>
                  <Text fontWeight="600" mb={2}>
                    2. Prepare Your Data
                  </Text>
                  <List spacing={1} fontSize="sm">
                    <ListItem>
                      <ListIcon as={CheckCircleIcon} color="green.500" />
                      Fill in required columns
                    </ListItem>
                    <ListItem>
                      <ListIcon as={CheckCircleIcon} color="green.500" />
                      Use correct date formats (YYYY-MM-DD)
                    </ListItem>
                    <ListItem>
                      <ListIcon as={CheckCircleIcon} color="green.500" />
                      Verify coordinates are valid
                    </ListItem>
                    <ListItem>
                      <ListIcon as={CheckCircleIcon} color="green.500" />
                      Check species names exist in database
                    </ListItem>
                  </List>
                </Box>

                <Divider />

                <Box>
                  <Text fontWeight="600" mb={2}>
                    3. Upload & Validate
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    After upload, your data will be validated. Any errors will
                    be shown for correction.
                  </Text>
                </Box>

                <Divider />

                <Alert status="info" rounded="md">
                  <AlertIcon />
                  <Box fontSize="sm">
                    <AlertTitle>Need Help?</AlertTitle>
                    <AlertDescription>
                      <Link as={RouterLink} to="/resources" color="brand.500">
                        View documentation
                      </Link>{' '}
                      or{' '}
                      <Link as={RouterLink} to="/contact" color="brand.500">
                        contact support
                      </Link>
                    </AlertDescription>
                  </Box>
                </Alert>
              </VStack>
            </CardBody>
          </Card>
        </Flex>
      </VStack>
    </Container>
  );
};

export default UploadPage;
