/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Validation Page - Review and validate pending submissions.
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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Card,
  CardBody,
  Select,
  Spinner,
  Center,
  Alert,
  AlertIcon,
  useToast,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Textarea,
  useColorModeValue,
  Checkbox,
  Flex,
  Spacer,
  Tooltip,
  Link,
} from '@chakra-ui/react';
import {
  CheckIcon,
  CloseIcon,
  ViewIcon,
  ExternalLinkIcon,
  InfoIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';
import { apiClient } from '../api/client';

interface PendingSite {
  id: number;
  siteCode: string;
  name: string;
  riverName?: string;
  ecosystemType?: string;
  submittedBy: string;
  submittedAt: string;
  latitude: number;
  longitude: number;
}

interface PendingRecord {
  id: number;
  taxonName: string;
  siteName: string;
  collectionDate: string;
  collector: string;
  submittedBy: string;
  submittedAt: string;
  abundance?: number;
}

interface PendingSurvey {
  id: number;
  siteName: string;
  siteCode: string;
  date: string;
  collector: string;
  recordCount: number;
  submittedBy: string;
  submittedAt: string;
}

interface PendingTaxon {
  id: number;
  canonicalName: string;
  rank: string;
  proposedBy: string;
  proposedAt: string;
  changeType: 'add' | 'update' | 'merge' | 'delete';
  notes?: string;
}

const ValidationPage: React.FC = () => {
  const toast = useToast();
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  const { isOpen, onOpen, onClose } = useDisclosure();

  // Determine initial tab from URL
  const getInitialTab = () => {
    if (location.pathname.includes('site-visits') || location.pathname.includes('surveys')) return 1;
    if (location.pathname.includes('records')) return 2;
    if (location.pathname.includes('taxa')) return 3;
    return 0;
  };

  const [activeTab, setActiveTab] = useState(getInitialTab());
  const [isLoading, setIsLoading] = useState(true);
  const [pendingSites, setPendingSites] = useState<PendingSite[]>([]);
  const [pendingSurveys, setPendingSurveys] = useState<PendingSurvey[]>([]);
  const [pendingRecords, setPendingRecords] = useState<PendingRecord[]>([]);
  const [pendingTaxa, setPendingTaxa] = useState<PendingTaxon[]>([]);
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [rejectionReason, setRejectionReason] = useState('');
  const [rejectingItemId, setRejectingItemId] = useState<number | null>(null);
  const [rejectingType, setRejectingType] = useState<'site' | 'survey' | 'record' | 'taxon'>('site');

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  const canValidate = user?.isStaff || user?.isSuperuser;

  // Fetch pending items
  useEffect(() => {
    const fetchPending = async () => {
      setIsLoading(true);
      try {
        // Fetch based on active tab
        if (activeTab === 0) {
          const response = await apiClient.get('sites/', {
            params: { validated: false, page_size: 50 },
          });
          const sites = (response.data?.data || []).map((site: any) => ({
            id: site.id,
            siteCode: site.site_code,
            name: site.name,
            riverName: site.river_name,
            ecosystemType: site.ecosystem_type,
            submittedBy: site.owner?.username || 'Unknown',
            submittedAt: site.created_at,
            latitude: site.latitude,
            longitude: site.longitude,
          }));
          setPendingSites(sites);
        } else if (activeTab === 1) {
          const response = await apiClient.get('surveys/', {
            params: { validated: false, page_size: 50 },
          });
          const surveys = (response.data?.data || []).map((survey: any) => ({
            id: survey.id,
            siteName: survey.site?.name || 'Unknown',
            siteCode: survey.site?.site_code || '',
            date: survey.date,
            collector: survey.collector_string || survey.collector_user?.username || 'Unknown',
            recordCount: survey.record_count || 0,
            submittedBy: survey.owner?.username || 'Unknown',
            submittedAt: survey.created_at,
          }));
          setPendingSurveys(surveys);
        } else if (activeTab === 2) {
          const response = await apiClient.get('records/', {
            params: { validated: false, page_size: 50 },
          });
          const records = (response.data?.data || []).map((record: any) => ({
            id: record.id,
            taxonName: record.taxonomy?.canonical_name || record.original_species_name,
            siteName: record.site?.name || 'Unknown',
            collectionDate: record.collection_date,
            collector: record.collector,
            submittedBy: record.owner?.username || 'Unknown',
            submittedAt: record.created_at,
            abundance: record.abundance_number,
          }));
          setPendingRecords(records);
        } else if (activeTab === 3) {
          const response = await apiClient.get('taxon-proposals/', {
            params: { status: 'pending' },
          });
          const taxa = (response.data?.data || []).map((proposal: any) => ({
            id: proposal.id,
            canonicalName: proposal.taxon?.canonical_name || proposal.proposed_name,
            rank: proposal.taxon?.rank || proposal.proposed_rank,
            proposedBy: proposal.proposed_by?.username || 'Unknown',
            proposedAt: proposal.created_at,
            changeType: proposal.change_type,
            notes: proposal.notes,
          }));
          setPendingTaxa(taxa);
        }
      } catch (error) {
        console.error('Failed to fetch pending items:', error);
        toast({
          title: 'Error',
          description: 'Failed to load pending items',
          status: 'error',
          duration: 5000,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchPending();
  }, [activeTab, toast]);

  // Approve site
  const handleApproveSite = useCallback(async (siteId: number) => {
    try {
      await apiClient.post(`sites/${siteId}/validate/`);
      setPendingSites(pendingSites.filter((s) => s.id !== siteId));
      toast({
        title: 'Approved',
        description: 'Site has been validated',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to validate site',
        status: 'error',
        duration: 5000,
      });
    }
  }, [pendingSites, toast]);

  // Approve survey (site visit)
  const handleApproveSurvey = useCallback(async (surveyId: number) => {
    try {
      await apiClient.post(`surveys/${surveyId}/validate/`);
      setPendingSurveys(pendingSurveys.filter((s) => s.id !== surveyId));
      toast({
        title: 'Approved',
        description: 'Site visit has been validated',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to validate site visit',
        status: 'error',
        duration: 5000,
      });
    }
  }, [pendingSurveys, toast]);

  // Approve record
  const handleApproveRecord = useCallback(async (recordId: number) => {
    try {
      await apiClient.post(`records/${recordId}/validate/`);
      setPendingRecords(pendingRecords.filter((r) => r.id !== recordId));
      toast({
        title: 'Approved',
        description: 'Record has been validated',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to validate record',
        status: 'error',
        duration: 5000,
      });
    }
  }, [pendingRecords, toast]);

  // Approve taxon
  const handleApproveTaxon = useCallback(async (proposalId: number) => {
    try {
      await apiClient.post(`taxon-proposals/${proposalId}/approve/`);
      setPendingTaxa(pendingTaxa.filter((t) => t.id !== proposalId));
      toast({
        title: 'Approved',
        description: 'Taxon proposal has been approved',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to approve proposal',
        status: 'error',
        duration: 5000,
      });
    }
  }, [pendingTaxa, toast]);

  // Open rejection modal
  const openRejectModal = (itemId: number, type: 'site' | 'survey' | 'record' | 'taxon') => {
    setRejectingItemId(itemId);
    setRejectingType(type);
    setRejectionReason('');
    onOpen();
  };

  // Handle rejection
  const handleReject = useCallback(async () => {
    if (!rejectingItemId) return;

    try {
      const endpointMap: Record<string, string> = {
        site: `sites/${rejectingItemId}/reject/`,
        survey: `surveys/${rejectingItemId}/reject/`,
        record: `records/${rejectingItemId}/reject/`,
        taxon: `taxon-proposals/${rejectingItemId}/reject/`,
      };
      const endpoint = endpointMap[rejectingType];

      await apiClient.post(endpoint, { reason: rejectionReason });

      if (rejectingType === 'site') {
        setPendingSites(pendingSites.filter((s) => s.id !== rejectingItemId));
      } else if (rejectingType === 'survey') {
        setPendingSurveys(pendingSurveys.filter((s) => s.id !== rejectingItemId));
      } else if (rejectingType === 'record') {
        setPendingRecords(pendingRecords.filter((r) => r.id !== rejectingItemId));
      } else {
        setPendingTaxa(pendingTaxa.filter((t) => t.id !== rejectingItemId));
      }

      onClose();
      toast({
        title: 'Rejected',
        description: 'Item has been rejected',
        status: 'info',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to reject item',
        status: 'error',
        duration: 5000,
      });
    }
  }, [rejectingItemId, rejectingType, rejectionReason, pendingSites, pendingSurveys, pendingRecords, pendingTaxa, onClose, toast]);

  // Bulk approve
  const handleBulkApprove = useCallback(async () => {
    if (selectedItems.length === 0) return;

    try {
      const endpointMap: Record<number, string> = {
        0: 'sites/bulk-validate/',
        1: 'surveys/bulk-validate/',
        2: 'records/bulk-validate/',
        3: 'taxon-proposals/bulk-approve/',
      };
      const endpoint = endpointMap[activeTab];

      // Surveys use survey_ids, others use ids
      const payload = activeTab === 1
        ? { survey_ids: selectedItems }
        : { ids: selectedItems };

      await apiClient.post(endpoint, payload);

      if (activeTab === 0) {
        setPendingSites(pendingSites.filter((s) => !selectedItems.includes(s.id)));
      } else if (activeTab === 1) {
        setPendingSurveys(pendingSurveys.filter((s) => !selectedItems.includes(s.id)));
      } else if (activeTab === 2) {
        setPendingRecords(pendingRecords.filter((r) => !selectedItems.includes(r.id)));
      } else {
        setPendingTaxa(pendingTaxa.filter((t) => !selectedItems.includes(t.id)));
      }

      setSelectedItems([]);
      toast({
        title: 'Success',
        description: `${selectedItems.length} items approved`,
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to approve items',
        status: 'error',
        duration: 5000,
      });
    }
  }, [activeTab, selectedItems, pendingSites, pendingSurveys, pendingRecords, pendingTaxa, toast]);

  if (!isAuthenticated || !canValidate) {
    return (
      <Container maxW="container.md" py={10}>
        <Alert status="warning">
          <AlertIcon />
          You do not have permission to validate submissions.
        </Alert>
      </Container>
    );
  }

  const totalPending = pendingSites.length + pendingSurveys.length + pendingRecords.length + pendingTaxa.length;

  return (
    <Box bg={bgColor} minH="calc(100vh - 100px)" py={8}>
      <Container maxW="container.xl">
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <HStack justify="space-between" flexWrap="wrap">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Validation Queue</Heading>
              <Text color="gray.500">
                Review and approve pending submissions
              </Text>
            </VStack>
            {selectedItems.length > 0 && (
              <HStack>
                <Text fontSize="sm" color="gray.500">
                  {selectedItems.length} selected
                </Text>
                <Button
                  leftIcon={<CheckIcon />}
                  colorScheme="green"
                  onClick={handleBulkApprove}
                >
                  Approve Selected
                </Button>
              </HStack>
            )}
          </HStack>

          {/* Summary Cards */}
          <HStack spacing={4} flexWrap="wrap">
            <Card bg={cardBg} minW="140px">
              <CardBody py={3} px={4}>
                <HStack>
                  <Text color="gray.500" fontSize="sm">
                    Sites
                  </Text>
                  <Spacer />
                  <Badge colorScheme="blue" fontSize="md">
                    {pendingSites.length}
                  </Badge>
                </HStack>
              </CardBody>
            </Card>
            <Card bg={cardBg} minW="140px">
              <CardBody py={3} px={4}>
                <HStack>
                  <Text color="gray.500" fontSize="sm">
                    Site Visits
                  </Text>
                  <Spacer />
                  <Badge colorScheme="orange" fontSize="md">
                    {pendingSurveys.length}
                  </Badge>
                </HStack>
              </CardBody>
            </Card>
            <Card bg={cardBg} minW="140px">
              <CardBody py={3} px={4}>
                <HStack>
                  <Text color="gray.500" fontSize="sm">
                    Records
                  </Text>
                  <Spacer />
                  <Badge colorScheme="green" fontSize="md">
                    {pendingRecords.length}
                  </Badge>
                </HStack>
              </CardBody>
            </Card>
            <Card bg={cardBg} minW="140px">
              <CardBody py={3} px={4}>
                <HStack>
                  <Text color="gray.500" fontSize="sm">
                    Taxa
                  </Text>
                  <Spacer />
                  <Badge colorScheme="purple" fontSize="md">
                    {pendingTaxa.length}
                  </Badge>
                </HStack>
              </CardBody>
            </Card>
          </HStack>

          {/* Tabs */}
          <Tabs
            index={activeTab}
            onChange={(index) => {
              setActiveTab(index);
              setSelectedItems([]);
            }}
          >
            <TabList flexWrap="wrap">
              <Tab>
                Sites
                {pendingSites.length > 0 && (
                  <Badge ml={2} colorScheme="blue">
                    {pendingSites.length}
                  </Badge>
                )}
              </Tab>
              <Tab>
                Site Visits
                {pendingSurveys.length > 0 && (
                  <Badge ml={2} colorScheme="orange">
                    {pendingSurveys.length}
                  </Badge>
                )}
              </Tab>
              <Tab>
                Records
                {pendingRecords.length > 0 && (
                  <Badge ml={2} colorScheme="green">
                    {pendingRecords.length}
                  </Badge>
                )}
              </Tab>
              <Tab>
                Taxa Proposals
                {pendingTaxa.length > 0 && (
                  <Badge ml={2} colorScheme="purple">
                    {pendingTaxa.length}
                  </Badge>
                )}
              </Tab>
            </TabList>

            <TabPanels>
              {/* Sites Tab */}
              <TabPanel px={0}>
                <Card bg={cardBg}>
                  <CardBody>
                    {isLoading ? (
                      <Center py={10}>
                        <Spinner size="xl" color="brand.500" />
                      </Center>
                    ) : pendingSites.length === 0 ? (
                      <Center py={10}>
                        <VStack>
                          <CheckIcon boxSize={8} color="green.500" />
                          <Text color="gray.500">No pending sites</Text>
                        </VStack>
                      </Center>
                    ) : (
                      <Box overflowX="auto">
                        <Table variant="simple" size="sm">
                          <Thead>
                            <Tr>
                              <Th w="40px">
                                <Checkbox
                                  isChecked={
                                    selectedItems.length === pendingSites.length &&
                                    pendingSites.length > 0
                                  }
                                  onChange={(e) =>
                                    setSelectedItems(
                                      e.target.checked
                                        ? pendingSites.map((s) => s.id)
                                        : []
                                    )
                                  }
                                />
                              </Th>
                              <Th>Site Code</Th>
                              <Th>Name</Th>
                              <Th>River</Th>
                              <Th>Submitted By</Th>
                              <Th>Date</Th>
                              <Th>Actions</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {pendingSites.map((site) => (
                              <Tr key={site.id}>
                                <Td>
                                  <Checkbox
                                    isChecked={selectedItems.includes(site.id)}
                                    onChange={(e) =>
                                      setSelectedItems(
                                        e.target.checked
                                          ? [...selectedItems, site.id]
                                          : selectedItems.filter((id) => id !== site.id)
                                      )
                                    }
                                  />
                                </Td>
                                <Td>{site.siteCode}</Td>
                                <Td>{site.name}</Td>
                                <Td>{site.riverName || '-'}</Td>
                                <Td>{site.submittedBy}</Td>
                                <Td>
                                  {new Date(site.submittedAt).toLocaleDateString()}
                                </Td>
                                <Td>
                                  <HStack spacing={1}>
                                    <Tooltip label="View on map">
                                      <IconButton
                                        aria-label="View"
                                        icon={<ViewIcon />}
                                        size="sm"
                                        variant="ghost"
                                        as={RouterLink}
                                        to={`/map/site/${site.id}`}
                                      />
                                    </Tooltip>
                                    <Tooltip label="Approve">
                                      <IconButton
                                        aria-label="Approve"
                                        icon={<CheckIcon />}
                                        size="sm"
                                        colorScheme="green"
                                        onClick={() => handleApproveSite(site.id)}
                                      />
                                    </Tooltip>
                                    <Tooltip label="Reject">
                                      <IconButton
                                        aria-label="Reject"
                                        icon={<CloseIcon />}
                                        size="sm"
                                        colorScheme="red"
                                        onClick={() => openRejectModal(site.id, 'site')}
                                      />
                                    </Tooltip>
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
              </TabPanel>

              {/* Site Visits Tab */}
              <TabPanel px={0}>
                <Card bg={cardBg}>
                  <CardBody>
                    {isLoading ? (
                      <Center py={10}>
                        <Spinner size="xl" color="brand.500" />
                      </Center>
                    ) : pendingSurveys.length === 0 ? (
                      <Center py={10}>
                        <VStack>
                          <CheckIcon boxSize={8} color="green.500" />
                          <Text color="gray.500">No pending site visits</Text>
                        </VStack>
                      </Center>
                    ) : (
                      <Box overflowX="auto">
                        <Table variant="simple" size="sm">
                          <Thead>
                            <Tr>
                              <Th w="40px">
                                <Checkbox
                                  isChecked={
                                    selectedItems.length === pendingSurveys.length &&
                                    pendingSurveys.length > 0
                                  }
                                  onChange={(e) =>
                                    setSelectedItems(
                                      e.target.checked
                                        ? pendingSurveys.map((s) => s.id)
                                        : []
                                    )
                                  }
                                />
                              </Th>
                              <Th>Site</Th>
                              <Th>Date</Th>
                              <Th>Collector</Th>
                              <Th>Records</Th>
                              <Th>Submitted By</Th>
                              <Th>Actions</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {pendingSurveys.map((survey) => (
                              <Tr key={survey.id}>
                                <Td>
                                  <Checkbox
                                    isChecked={selectedItems.includes(survey.id)}
                                    onChange={(e) =>
                                      setSelectedItems(
                                        e.target.checked
                                          ? [...selectedItems, survey.id]
                                          : selectedItems.filter((id) => id !== survey.id)
                                      )
                                    }
                                  />
                                </Td>
                                <Td>
                                  <VStack align="start" spacing={0}>
                                    <Text fontWeight="medium">{survey.siteName}</Text>
                                    <Text fontSize="xs" color="gray.500">
                                      {survey.siteCode}
                                    </Text>
                                  </VStack>
                                </Td>
                                <Td>
                                  {survey.date
                                    ? new Date(survey.date).toLocaleDateString()
                                    : '-'}
                                </Td>
                                <Td>{survey.collector}</Td>
                                <Td>
                                  <Badge colorScheme="blue">{survey.recordCount}</Badge>
                                </Td>
                                <Td>{survey.submittedBy}</Td>
                                <Td>
                                  <HStack spacing={1}>
                                    <Tooltip label="View site on map">
                                      <IconButton
                                        aria-label="View"
                                        icon={<ViewIcon />}
                                        size="sm"
                                        variant="ghost"
                                        as={RouterLink}
                                        to={`/map`}
                                      />
                                    </Tooltip>
                                    <Tooltip label="Approve">
                                      <IconButton
                                        aria-label="Approve"
                                        icon={<CheckIcon />}
                                        size="sm"
                                        colorScheme="green"
                                        onClick={() => handleApproveSurvey(survey.id)}
                                      />
                                    </Tooltip>
                                    <Tooltip label="Reject">
                                      <IconButton
                                        aria-label="Reject"
                                        icon={<CloseIcon />}
                                        size="sm"
                                        colorScheme="red"
                                        onClick={() => openRejectModal(survey.id, 'survey')}
                                      />
                                    </Tooltip>
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
              </TabPanel>

              {/* Records Tab */}
              <TabPanel px={0}>
                <Card bg={cardBg}>
                  <CardBody>
                    {isLoading ? (
                      <Center py={10}>
                        <Spinner size="xl" color="brand.500" />
                      </Center>
                    ) : pendingRecords.length === 0 ? (
                      <Center py={10}>
                        <VStack>
                          <CheckIcon boxSize={8} color="green.500" />
                          <Text color="gray.500">No pending records</Text>
                        </VStack>
                      </Center>
                    ) : (
                      <Box overflowX="auto">
                        <Table variant="simple" size="sm">
                          <Thead>
                            <Tr>
                              <Th w="40px">
                                <Checkbox
                                  isChecked={
                                    selectedItems.length === pendingRecords.length &&
                                    pendingRecords.length > 0
                                  }
                                  onChange={(e) =>
                                    setSelectedItems(
                                      e.target.checked
                                        ? pendingRecords.map((r) => r.id)
                                        : []
                                    )
                                  }
                                />
                              </Th>
                              <Th>Species</Th>
                              <Th>Site</Th>
                              <Th>Date</Th>
                              <Th>Collector</Th>
                              <Th>Submitted By</Th>
                              <Th>Actions</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {pendingRecords.map((record) => (
                              <Tr key={record.id}>
                                <Td>
                                  <Checkbox
                                    isChecked={selectedItems.includes(record.id)}
                                    onChange={(e) =>
                                      setSelectedItems(
                                        e.target.checked
                                          ? [...selectedItems, record.id]
                                          : selectedItems.filter((id) => id !== record.id)
                                      )
                                    }
                                  />
                                </Td>
                                <Td fontStyle="italic">{record.taxonName}</Td>
                                <Td>{record.siteName}</Td>
                                <Td>
                                  {record.collectionDate
                                    ? new Date(record.collectionDate).toLocaleDateString()
                                    : '-'}
                                </Td>
                                <Td>{record.collector || '-'}</Td>
                                <Td>{record.submittedBy}</Td>
                                <Td>
                                  <HStack spacing={1}>
                                    <Tooltip label="Approve">
                                      <IconButton
                                        aria-label="Approve"
                                        icon={<CheckIcon />}
                                        size="sm"
                                        colorScheme="green"
                                        onClick={() => handleApproveRecord(record.id)}
                                      />
                                    </Tooltip>
                                    <Tooltip label="Reject">
                                      <IconButton
                                        aria-label="Reject"
                                        icon={<CloseIcon />}
                                        size="sm"
                                        colorScheme="red"
                                        onClick={() => openRejectModal(record.id, 'record')}
                                      />
                                    </Tooltip>
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
              </TabPanel>

              {/* Taxa Tab */}
              <TabPanel px={0}>
                <Card bg={cardBg}>
                  <CardBody>
                    {isLoading ? (
                      <Center py={10}>
                        <Spinner size="xl" color="brand.500" />
                      </Center>
                    ) : pendingTaxa.length === 0 ? (
                      <Center py={10}>
                        <VStack>
                          <CheckIcon boxSize={8} color="green.500" />
                          <Text color="gray.500">No pending taxa proposals</Text>
                        </VStack>
                      </Center>
                    ) : (
                      <Box overflowX="auto">
                        <Table variant="simple" size="sm">
                          <Thead>
                            <Tr>
                              <Th w="40px">
                                <Checkbox
                                  isChecked={
                                    selectedItems.length === pendingTaxa.length &&
                                    pendingTaxa.length > 0
                                  }
                                  onChange={(e) =>
                                    setSelectedItems(
                                      e.target.checked
                                        ? pendingTaxa.map((t) => t.id)
                                        : []
                                    )
                                  }
                                />
                              </Th>
                              <Th>Name</Th>
                              <Th>Rank</Th>
                              <Th>Change Type</Th>
                              <Th>Proposed By</Th>
                              <Th>Date</Th>
                              <Th>Actions</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {pendingTaxa.map((taxon) => (
                              <Tr key={taxon.id}>
                                <Td>
                                  <Checkbox
                                    isChecked={selectedItems.includes(taxon.id)}
                                    onChange={(e) =>
                                      setSelectedItems(
                                        e.target.checked
                                          ? [...selectedItems, taxon.id]
                                          : selectedItems.filter((id) => id !== taxon.id)
                                      )
                                    }
                                  />
                                </Td>
                                <Td fontStyle="italic">{taxon.canonicalName}</Td>
                                <Td>{taxon.rank}</Td>
                                <Td>
                                  <Badge
                                    colorScheme={
                                      taxon.changeType === 'add'
                                        ? 'green'
                                        : taxon.changeType === 'delete'
                                        ? 'red'
                                        : 'blue'
                                    }
                                  >
                                    {taxon.changeType}
                                  </Badge>
                                </Td>
                                <Td>{taxon.proposedBy}</Td>
                                <Td>
                                  {new Date(taxon.proposedAt).toLocaleDateString()}
                                </Td>
                                <Td>
                                  <HStack spacing={1}>
                                    {taxon.notes && (
                                      <Tooltip label={taxon.notes}>
                                        <IconButton
                                          aria-label="Notes"
                                          icon={<InfoIcon />}
                                          size="sm"
                                          variant="ghost"
                                        />
                                      </Tooltip>
                                    )}
                                    <Tooltip label="Approve">
                                      <IconButton
                                        aria-label="Approve"
                                        icon={<CheckIcon />}
                                        size="sm"
                                        colorScheme="green"
                                        onClick={() => handleApproveTaxon(taxon.id)}
                                      />
                                    </Tooltip>
                                    <Tooltip label="Reject">
                                      <IconButton
                                        aria-label="Reject"
                                        icon={<CloseIcon />}
                                        size="sm"
                                        colorScheme="red"
                                        onClick={() => openRejectModal(taxon.id, 'taxon')}
                                      />
                                    </Tooltip>
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
              </TabPanel>
            </TabPanels>
          </Tabs>
        </VStack>

        {/* Rejection Modal */}
        <Modal isOpen={isOpen} onClose={onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Reject Submission</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <FormControl>
                <FormLabel>Reason for rejection (optional)</FormLabel>
                <Textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Provide feedback for the submitter..."
                  rows={4}
                />
              </FormControl>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onClose}>
                Cancel
              </Button>
              <Button colorScheme="red" onClick={handleReject}>
                Reject
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Container>
    </Box>
  );
};

export default ValidationPage;
