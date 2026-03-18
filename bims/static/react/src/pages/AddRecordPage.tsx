/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Add Record Page - Form for adding biological collection records.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  FormControl,
  FormLabel,
  FormErrorMessage,
  FormHelperText,
  Input,
  Select,
  Textarea,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Card,
  CardBody,
  CardHeader,
  SimpleGrid,
  Divider,
  useToast,
  Spinner,
  Center,
  Alert,
  AlertIcon,
  useColorModeValue,
  InputGroup,
  InputLeftElement,
  List,
  ListItem,
  Badge,
  IconButton,
} from '@chakra-ui/react';
import { SearchIcon, CloseIcon, AddIcon } from '@chakra-ui/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';
import { apiClient } from '../api/client';

interface TaxonGroup {
  id: number;
  name: string;
  category?: string;
}

interface Site {
  id: number;
  siteCode: string;
  name: string;
}

interface Taxon {
  id: number;
  canonicalName: string;
  scientificName: string;
  rank: string;
}

interface SourceReference {
  id: number;
  title: string;
  sourceType: string;
}

interface FormData {
  siteId: number | null;
  taxonomyId: number | null;
  collectionDate: string;
  collector: string;
  abundanceNumber: number | null;
  abundanceType: string;
  samplingMethod: string;
  biotope: string;
  specificBiotope: string;
  sourceReferenceId: number | null;
  notes: string;
  originalSpeciesName: string;
}

const AddRecordPage: React.FC = () => {
  const { type } = useParams<{ type?: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const { user, isAuthenticated } = useAuth();

  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [taxonGroups, setTaxonGroups] = useState<TaxonGroup[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Site search
  const [siteQuery, setSiteQuery] = useState('');
  const [siteResults, setSiteResults] = useState<Site[]>([]);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);
  const [isSearchingSites, setIsSearchingSites] = useState(false);

  // Taxon search
  const [taxonQuery, setTaxonQuery] = useState('');
  const [taxonResults, setTaxonResults] = useState<Taxon[]>([]);
  const [selectedTaxon, setSelectedTaxon] = useState<Taxon | null>(null);
  const [isSearchingTaxa, setIsSearchingTaxa] = useState(false);

  // Source reference search
  const [refQuery, setRefQuery] = useState('');
  const [refResults, setRefResults] = useState<SourceReference[]>([]);
  const [selectedRef, setSelectedRef] = useState<SourceReference | null>(null);
  const [isSearchingRefs, setIsSearchingRefs] = useState(false);

  // Form data
  const [formData, setFormData] = useState<FormData>({
    siteId: null,
    taxonomyId: null,
    collectionDate: new Date().toISOString().split('T')[0],
    collector: user?.username || '',
    abundanceNumber: null,
    abundanceType: '',
    samplingMethod: '',
    biotope: '',
    specificBiotope: '',
    sourceReferenceId: null,
    notes: '',
    originalSpeciesName: '',
  });

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  // Get record type title
  const getTypeTitle = () => {
    switch (type) {
      case 'fish':
        return 'Fish Record';
      case 'invertebrate':
        return 'Invertebrate Record';
      case 'algae':
        return 'Algae Record';
      case 'module':
        return 'Module Record';
      case 'abiotic':
        return 'Abiotic Data';
      default:
        return 'Biological Record';
    }
  };

  // Fetch taxon groups
  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const response = await apiClient.get('taxon-groups/');
        const groups = response.data?.data || [];
        setTaxonGroups(groups);

        // Auto-select group based on type
        const typeGroupMap: Record<string, string> = {
          fish: 'Fish',
          invertebrate: 'Invertebrates',
          algae: 'Algae',
        };
        if (type && typeGroupMap[type]) {
          const matchingGroup = groups.find(
            (g: TaxonGroup) =>
              g.name.toLowerCase().includes(typeGroupMap[type].toLowerCase())
          );
          if (matchingGroup) {
            setSelectedGroupId(matchingGroup.id);
          }
        }
      } catch (error) {
        console.error('Failed to fetch taxon groups:', error);
      }
    };
    fetchGroups();
  }, [type]);

  // Search sites
  useEffect(() => {
    if (siteQuery.length < 2) {
      setSiteResults([]);
      return;
    }

    const searchSites = async () => {
      setIsSearchingSites(true);
      try {
        const response = await apiClient.get('sites/', {
          params: { search: siteQuery, page_size: 10 },
        });
        const sites = (response.data?.data || []).map((site: any) => ({
          id: site.id,
          siteCode: site.site_code,
          name: site.name,
        }));
        setSiteResults(sites);
      } catch (error) {
        console.error('Failed to search sites:', error);
      } finally {
        setIsSearchingSites(false);
      }
    };

    const timeout = setTimeout(searchSites, 300);
    return () => clearTimeout(timeout);
  }, [siteQuery]);

  // Search taxa
  useEffect(() => {
    if (taxonQuery.length < 2) {
      setTaxonResults([]);
      return;
    }

    const searchTaxa = async () => {
      setIsSearchingTaxa(true);
      try {
        const params: Record<string, any> = {
          search: taxonQuery,
          page_size: 10,
        };
        if (selectedGroupId) {
          params.taxon_group = selectedGroupId;
        }

        const response = await apiClient.get('taxa/', { params });
        const taxa = (response.data?.data || []).map((taxon: any) => ({
          id: taxon.id,
          canonicalName: taxon.canonical_name,
          scientificName: taxon.scientific_name,
          rank: taxon.rank,
        }));
        setTaxonResults(taxa);
      } catch (error) {
        console.error('Failed to search taxa:', error);
      } finally {
        setIsSearchingTaxa(false);
      }
    };

    const timeout = setTimeout(searchTaxa, 300);
    return () => clearTimeout(timeout);
  }, [taxonQuery, selectedGroupId]);

  // Search source references
  useEffect(() => {
    if (refQuery.length < 2) {
      setRefResults([]);
      return;
    }

    const searchRefs = async () => {
      setIsSearchingRefs(true);
      try {
        const response = await apiClient.get('source-references/', {
          params: { search: refQuery, page_size: 10 },
        });
        const refs = (response.data?.data || []).map((ref: any) => ({
          id: ref.id,
          title: ref.title,
          sourceType: ref.source_type,
        }));
        setRefResults(refs);
      } catch (error) {
        console.error('Failed to search references:', error);
      } finally {
        setIsSearchingRefs(false);
      }
    };

    const timeout = setTimeout(searchRefs, 300);
    return () => clearTimeout(timeout);
  }, [refQuery]);

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!selectedSite) {
      newErrors.site = 'Please select a site';
    }
    if (!selectedTaxon && !formData.originalSpeciesName) {
      newErrors.taxon = 'Please select a taxon or enter species name';
    }
    if (!formData.collectionDate) {
      newErrors.collectionDate = 'Collection date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle submit
  const handleSubmit = useCallback(async () => {
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const payload = {
        site: selectedSite?.id,
        taxonomy: selectedTaxon?.id,
        original_species_name: formData.originalSpeciesName || selectedTaxon?.canonicalName,
        collection_date: formData.collectionDate,
        collector: formData.collector,
        abundance_number: formData.abundanceNumber,
        abundance_type: formData.abundanceType,
        sampling_method: formData.samplingMethod,
        biotope: formData.biotope,
        specific_biotope: formData.specificBiotope,
        source_reference: selectedRef?.id,
        notes: formData.notes,
        module_group: selectedGroupId,
      };

      const response = await apiClient.post('records/', payload);

      if (response.data?.data) {
        toast({
          title: 'Success',
          description: 'Record has been created',
          status: 'success',
          duration: 3000,
        });
        navigate('/map');
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to create record',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  }, [selectedSite, selectedTaxon, selectedRef, formData, selectedGroupId, navigate, toast]);

  if (!isAuthenticated) {
    return (
      <Container maxW="container.md" py={10}>
        <Alert status="warning">
          <AlertIcon />
          Please sign in to add records.
        </Alert>
      </Container>
    );
  }

  return (
    <Box bg={bgColor} minH="calc(100vh - 100px)" py={8}>
      <Container maxW="container.lg">
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Add {getTypeTitle()}</Heading>
              <Text color="gray.500">
                Enter details for a new biological collection record
              </Text>
            </VStack>
          </HStack>

          {/* Form */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Location & Species</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={6} align="stretch">
                {/* Taxon Group */}
                <FormControl>
                  <FormLabel>Taxon Group</FormLabel>
                  <Select
                    value={selectedGroupId || ''}
                    onChange={(e) =>
                      setSelectedGroupId(e.target.value ? Number(e.target.value) : null)
                    }
                  >
                    <option value="">Select group...</option>
                    {taxonGroups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name}
                      </option>
                    ))}
                  </Select>
                </FormControl>

                {/* Site Selection */}
                <FormControl isInvalid={!!errors.site}>
                  <FormLabel>Site *</FormLabel>
                  {selectedSite ? (
                    <HStack
                      p={3}
                      bg="blue.50"
                      borderRadius="md"
                      justify="space-between"
                    >
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="medium">{selectedSite.name}</Text>
                        <Text fontSize="sm" color="gray.500">
                          {selectedSite.siteCode}
                        </Text>
                      </VStack>
                      <IconButton
                        aria-label="Clear site"
                        icon={<CloseIcon />}
                        size="sm"
                        variant="ghost"
                        onClick={() => setSelectedSite(null)}
                      />
                    </HStack>
                  ) : (
                    <Box position="relative">
                      <InputGroup>
                        <InputLeftElement>
                          {isSearchingSites ? (
                            <Spinner size="sm" />
                          ) : (
                            <SearchIcon color="gray.400" />
                          )}
                        </InputLeftElement>
                        <Input
                          placeholder="Search for a site..."
                          value={siteQuery}
                          onChange={(e) => setSiteQuery(e.target.value)}
                        />
                      </InputGroup>
                      {siteResults.length > 0 && (
                        <List
                          position="absolute"
                          top="100%"
                          left={0}
                          right={0}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.200"
                          borderRadius="md"
                          boxShadow="md"
                          zIndex={10}
                          maxH="200px"
                          overflow="auto"
                        >
                          {siteResults.map((site) => (
                            <ListItem
                              key={site.id}
                              px={4}
                              py={2}
                              cursor="pointer"
                              _hover={{ bg: 'gray.100' }}
                              onClick={() => {
                                setSelectedSite(site);
                                setSiteQuery('');
                                setSiteResults([]);
                              }}
                            >
                              <Text fontWeight="medium">{site.name}</Text>
                              <Text fontSize="sm" color="gray.500">
                                {site.siteCode}
                              </Text>
                            </ListItem>
                          ))}
                        </List>
                      )}
                    </Box>
                  )}
                  <FormErrorMessage>{errors.site}</FormErrorMessage>
                </FormControl>

                {/* Taxon Selection */}
                <FormControl isInvalid={!!errors.taxon}>
                  <FormLabel>Taxon *</FormLabel>
                  {selectedTaxon ? (
                    <HStack
                      p={3}
                      bg="green.50"
                      borderRadius="md"
                      justify="space-between"
                    >
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="medium" fontStyle="italic">
                          {selectedTaxon.canonicalName}
                        </Text>
                        <Text fontSize="sm" color="gray.500">
                          {selectedTaxon.rank}
                        </Text>
                      </VStack>
                      <IconButton
                        aria-label="Clear taxon"
                        icon={<CloseIcon />}
                        size="sm"
                        variant="ghost"
                        onClick={() => setSelectedTaxon(null)}
                      />
                    </HStack>
                  ) : (
                    <Box position="relative">
                      <InputGroup>
                        <InputLeftElement>
                          {isSearchingTaxa ? (
                            <Spinner size="sm" />
                          ) : (
                            <SearchIcon color="gray.400" />
                          )}
                        </InputLeftElement>
                        <Input
                          placeholder="Search for a species..."
                          value={taxonQuery}
                          onChange={(e) => setTaxonQuery(e.target.value)}
                        />
                      </InputGroup>
                      {taxonResults.length > 0 && (
                        <List
                          position="absolute"
                          top="100%"
                          left={0}
                          right={0}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.200"
                          borderRadius="md"
                          boxShadow="md"
                          zIndex={10}
                          maxH="200px"
                          overflow="auto"
                        >
                          {taxonResults.map((taxon) => (
                            <ListItem
                              key={taxon.id}
                              px={4}
                              py={2}
                              cursor="pointer"
                              _hover={{ bg: 'gray.100' }}
                              onClick={() => {
                                setSelectedTaxon(taxon);
                                setTaxonQuery('');
                                setTaxonResults([]);
                              }}
                            >
                              <Text fontWeight="medium" fontStyle="italic">
                                {taxon.canonicalName}
                              </Text>
                              <Text fontSize="sm" color="gray.500">
                                {taxon.rank}
                              </Text>
                            </ListItem>
                          ))}
                        </List>
                      )}
                    </Box>
                  )}
                  <FormErrorMessage>{errors.taxon}</FormErrorMessage>
                  <FormHelperText>
                    Search for an existing species or enter a new name below
                  </FormHelperText>
                </FormControl>

                {/* Original Species Name */}
                {!selectedTaxon && (
                  <FormControl>
                    <FormLabel>Original Species Name</FormLabel>
                    <Input
                      value={formData.originalSpeciesName}
                      onChange={(e) =>
                        setFormData({ ...formData, originalSpeciesName: e.target.value })
                      }
                      placeholder="Enter species name as recorded"
                    />
                    <FormHelperText>
                      Use this if the species is not in the database
                    </FormHelperText>
                  </FormControl>
                )}
              </VStack>
            </CardBody>
          </Card>

          {/* Collection Details */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Collection Details</Heading>
            </CardHeader>
            <CardBody>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                <FormControl isInvalid={!!errors.collectionDate}>
                  <FormLabel>Collection Date *</FormLabel>
                  <Input
                    type="date"
                    value={formData.collectionDate}
                    onChange={(e) =>
                      setFormData({ ...formData, collectionDate: e.target.value })
                    }
                  />
                  <FormErrorMessage>{errors.collectionDate}</FormErrorMessage>
                </FormControl>

                <FormControl>
                  <FormLabel>Collector</FormLabel>
                  <Input
                    value={formData.collector}
                    onChange={(e) =>
                      setFormData({ ...formData, collector: e.target.value })
                    }
                    placeholder="Name of collector"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Abundance</FormLabel>
                  <NumberInput
                    min={0}
                    value={formData.abundanceNumber || ''}
                    onChange={(_, value) =>
                      setFormData({ ...formData, abundanceNumber: value || null })
                    }
                  >
                    <NumberInputField placeholder="Number observed" />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>

                <FormControl>
                  <FormLabel>Abundance Type</FormLabel>
                  <Select
                    value={formData.abundanceType}
                    onChange={(e) =>
                      setFormData({ ...formData, abundanceType: e.target.value })
                    }
                  >
                    <option value="">Select...</option>
                    <option value="number">Number</option>
                    <option value="percentage">Percentage</option>
                    <option value="density">Density</option>
                    <option value="presence">Presence/Absence</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Sampling Method</FormLabel>
                  <Select
                    value={formData.samplingMethod}
                    onChange={(e) =>
                      setFormData({ ...formData, samplingMethod: e.target.value })
                    }
                  >
                    <option value="">Select...</option>
                    <option value="net">Net</option>
                    <option value="trap">Trap</option>
                    <option value="visual">Visual Survey</option>
                    <option value="electrofishing">Electrofishing</option>
                    <option value="kick_sample">Kick Sample</option>
                    <option value="other">Other</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Biotope</FormLabel>
                  <Select
                    value={formData.biotope}
                    onChange={(e) =>
                      setFormData({ ...formData, biotope: e.target.value })
                    }
                  >
                    <option value="">Select...</option>
                    <option value="stones">Stones</option>
                    <option value="vegetation">Vegetation</option>
                    <option value="gravel_sand_mud">Gravel/Sand/Mud</option>
                    <option value="mixed">Mixed</option>
                  </Select>
                </FormControl>
              </SimpleGrid>
            </CardBody>
          </Card>

          {/* Source Reference */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Source Reference</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>Source Reference</FormLabel>
                  {selectedRef ? (
                    <HStack
                      p={3}
                      bg="purple.50"
                      borderRadius="md"
                      justify="space-between"
                    >
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="medium">{selectedRef.title}</Text>
                        <Badge>{selectedRef.sourceType}</Badge>
                      </VStack>
                      <IconButton
                        aria-label="Clear reference"
                        icon={<CloseIcon />}
                        size="sm"
                        variant="ghost"
                        onClick={() => setSelectedRef(null)}
                      />
                    </HStack>
                  ) : (
                    <Box position="relative">
                      <InputGroup>
                        <InputLeftElement>
                          {isSearchingRefs ? (
                            <Spinner size="sm" />
                          ) : (
                            <SearchIcon color="gray.400" />
                          )}
                        </InputLeftElement>
                        <Input
                          placeholder="Search for a source reference..."
                          value={refQuery}
                          onChange={(e) => setRefQuery(e.target.value)}
                        />
                      </InputGroup>
                      {refResults.length > 0 && (
                        <List
                          position="absolute"
                          top="100%"
                          left={0}
                          right={0}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.200"
                          borderRadius="md"
                          boxShadow="md"
                          zIndex={10}
                          maxH="200px"
                          overflow="auto"
                        >
                          {refResults.map((ref) => (
                            <ListItem
                              key={ref.id}
                              px={4}
                              py={2}
                              cursor="pointer"
                              _hover={{ bg: 'gray.100' }}
                              onClick={() => {
                                setSelectedRef(ref);
                                setRefQuery('');
                                setRefResults([]);
                              }}
                            >
                              <Text fontWeight="medium">{ref.title}</Text>
                              <Badge size="sm">{ref.sourceType}</Badge>
                            </ListItem>
                          ))}
                        </List>
                      )}
                    </Box>
                  )}
                </FormControl>

                <FormControl>
                  <FormLabel>Notes</FormLabel>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) =>
                      setFormData({ ...formData, notes: e.target.value })
                    }
                    placeholder="Additional notes about this record..."
                    rows={3}
                  />
                </FormControl>
              </VStack>
            </CardBody>
          </Card>

          {/* Actions */}
          <HStack justify="flex-end" spacing={4}>
            <Button variant="ghost" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
              leftIcon={<AddIcon />}
              onClick={handleSubmit}
              isLoading={isSubmitting}
            >
              Add Record
            </Button>
          </HStack>
        </VStack>
      </Container>
    </Box>
  );
};

export default AddRecordPage;
