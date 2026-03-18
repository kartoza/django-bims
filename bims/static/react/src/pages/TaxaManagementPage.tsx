/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Taxa Management Page - Admin interface for managing taxonomic data.
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
  Input,
  InputGroup,
  InputLeftElement,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Card,
  CardBody,
  CardHeader,
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
} from '@chakra-ui/react';
import {
  SearchIcon,
  AddIcon,
  EditIcon,
  DeleteIcon,
  ChevronDownIcon,
  CheckIcon,
  CloseIcon,
  DownloadIcon,
  ExternalLinkIcon,
} from '@chakra-ui/icons';
import { useAuth } from '../providers/AuthProvider';
import { apiClient } from '../api/client';

interface TaxonGroup {
  id: number;
  name: string;
  category?: string;
  logo?: string;
  taxonCount?: number;
}

interface Taxon {
  id: number;
  canonicalName: string;
  scientificName: string;
  rank: string;
  taxonomicStatus: string;
  iucnStatus?: string;
  endemism?: string;
  validated: boolean;
  gbifKey?: number;
}

interface TaxonProposal {
  id: number;
  taxon: Taxon;
  proposedBy: string;
  proposedAt: string;
  status: 'pending' | 'approved' | 'rejected';
  notes?: string;
  changeType: 'add' | 'update' | 'merge' | 'delete';
}

const TaxaManagementPage: React.FC = () => {
  const toast = useToast();
  const { user, isAuthenticated } = useAuth();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [activeTab, setActiveTab] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  const [taxonGroups, setTaxonGroups] = useState<TaxonGroup[]>([]);
  const [taxa, setTaxa] = useState<Taxon[]>([]);
  const [proposals, setProposals] = useState<TaxonProposal[]>([]);
  const [selectedTaxa, setSelectedTaxa] = useState<number[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Modal state
  const [modalMode, setModalMode] = useState<'add' | 'edit' | 'gbif'>('add');
  const [editingTaxon, setEditingTaxon] = useState<Taxon | null>(null);
  const [gbifSearchQuery, setGbifSearchQuery] = useState('');
  const [gbifResults, setGbifResults] = useState<any[]>([]);
  const [isSearchingGbif, setIsSearchingGbif] = useState(false);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  // Check permissions
  const canManageTaxa = user?.isStaff || user?.isSuperuser;

  // Fetch taxon groups
  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const response = await apiClient.get('taxon-groups/');
        setTaxonGroups(response.data?.data || []);
      } catch (error) {
        console.error('Failed to fetch taxon groups:', error);
      }
    };
    fetchGroups();
  }, []);

  // Fetch taxa based on filters
  useEffect(() => {
    const fetchTaxa = async () => {
      setIsLoading(true);
      try {
        const params: Record<string, any> = {
          page,
          page_size: 20,
        };
        if (searchQuery) params.search = searchQuery;
        if (selectedGroup) params.taxon_group = selectedGroup;

        const response = await apiClient.get('taxa/', { params });
        setTaxa(response.data?.data || []);
        setTotalPages(response.data?.meta?.total_pages || 1);
      } catch (error) {
        console.error('Failed to fetch taxa:', error);
        toast({
          title: 'Error',
          description: 'Failed to load taxa',
          status: 'error',
          duration: 5000,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchTaxa();
  }, [searchQuery, selectedGroup, page, toast]);

  // Fetch proposals
  useEffect(() => {
    const fetchProposals = async () => {
      if (activeTab !== 1) return;

      try {
        const response = await apiClient.get('taxon-proposals/', {
          params: { status: 'pending' },
        });
        setProposals(response.data?.data || []);
      } catch (error) {
        console.error('Failed to fetch proposals:', error);
      }
    };

    fetchProposals();
  }, [activeTab]);

  // GBIF Search
  const handleGbifSearch = useCallback(async () => {
    if (!gbifSearchQuery.trim()) return;

    setIsSearchingGbif(true);
    try {
      const response = await apiClient.get('taxa-management/gbif_search/', {
        params: { q: gbifSearchQuery },
      });
      setGbifResults(response.data?.data || []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to search GBIF',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSearchingGbif(false);
    }
  }, [gbifSearchQuery, toast]);

  // Import from GBIF
  const handleGbifImport = useCallback(async (gbifKey: number) => {
    try {
      const response = await apiClient.post('taxa-management/gbif_import/', {
        gbif_key: gbifKey,
        taxon_group: selectedGroup,
      });

      if (response.data?.data) {
        toast({
          title: 'Success',
          description: 'Taxon imported from GBIF',
          status: 'success',
          duration: 3000,
        });
        onClose();
        // Refresh taxa list
        setPage(1);
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to import from GBIF',
        status: 'error',
        duration: 5000,
      });
    }
  }, [selectedGroup, toast, onClose]);

  // Approve proposal
  const handleApproveProposal = useCallback(async (proposalId: number) => {
    try {
      await apiClient.post(`taxon-proposals/${proposalId}/approve/`);
      setProposals(proposals.filter((p) => p.id !== proposalId));
      toast({
        title: 'Approved',
        description: 'Proposal has been approved',
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
  }, [proposals, toast]);

  // Reject proposal
  const handleRejectProposal = useCallback(async (proposalId: number) => {
    try {
      await apiClient.post(`taxon-proposals/${proposalId}/reject/`);
      setProposals(proposals.filter((p) => p.id !== proposalId));
      toast({
        title: 'Rejected',
        description: 'Proposal has been rejected',
        status: 'info',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to reject proposal',
        status: 'error',
        duration: 5000,
      });
    }
  }, [proposals, toast]);

  // Validate taxon
  const handleValidateTaxon = useCallback(async (taxonId: number) => {
    try {
      await apiClient.post(`taxa/${taxonId}/validate/`);
      setTaxa(taxa.map((t) => (t.id === taxonId ? { ...t, validated: true } : t)));
      toast({
        title: 'Validated',
        description: 'Taxon has been validated',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to validate taxon',
        status: 'error',
        duration: 5000,
      });
    }
  }, [taxa, toast]);

  // Bulk actions
  const handleBulkValidate = useCallback(async () => {
    if (selectedTaxa.length === 0) return;

    try {
      await apiClient.post('taxa-management/batch_validate/', {
        taxon_ids: selectedTaxa,
      });
      setTaxa(taxa.map((t) =>
        selectedTaxa.includes(t.id) ? { ...t, validated: true } : t
      ));
      setSelectedTaxa([]);
      toast({
        title: 'Success',
        description: `${selectedTaxa.length} taxa validated`,
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to validate taxa',
        status: 'error',
        duration: 5000,
      });
    }
  }, [selectedTaxa, taxa, toast]);

  const openAddModal = () => {
    setModalMode('gbif');
    setEditingTaxon(null);
    setGbifResults([]);
    setGbifSearchQuery('');
    onOpen();
  };

  if (!isAuthenticated || !canManageTaxa) {
    return (
      <Container maxW="container.md" py={10}>
        <Alert status="warning">
          <AlertIcon />
          You do not have permission to access taxa management.
        </Alert>
      </Container>
    );
  }

  return (
    <Box bg={bgColor} minH="calc(100vh - 100px)" py={8}>
      <Container maxW="container.xl">
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <HStack justify="space-between" flexWrap="wrap">
            <Heading size="lg">Taxa Management</Heading>
            <HStack>
              <Button
                leftIcon={<DownloadIcon />}
                variant="outline"
                onClick={() => window.open('/download-taxa-list/', '_blank')}
              >
                Export
              </Button>
              <Button
                leftIcon={<AddIcon />}
                colorScheme="brand"
                onClick={openAddModal}
              >
                Add Taxon
              </Button>
            </HStack>
          </HStack>

          {/* Tabs */}
          <Tabs index={activeTab} onChange={setActiveTab}>
            <TabList>
              <Tab>All Taxa</Tab>
              <Tab>
                Proposals
                {proposals.length > 0 && (
                  <Badge ml={2} colorScheme="orange">
                    {proposals.length}
                  </Badge>
                )}
              </Tab>
              <Tab>Groups</Tab>
            </TabList>

            <TabPanels>
              {/* All Taxa Tab */}
              <TabPanel px={0}>
                <Card bg={cardBg}>
                  <CardBody>
                    {/* Filters */}
                    <HStack spacing={4} mb={6} flexWrap="wrap">
                      <InputGroup maxW="300px">
                        <InputLeftElement>
                          <SearchIcon color="gray.400" />
                        </InputLeftElement>
                        <Input
                          placeholder="Search taxa..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                        />
                      </InputGroup>
                      <Select
                        placeholder="All Groups"
                        maxW="200px"
                        value={selectedGroup || ''}
                        onChange={(e) =>
                          setSelectedGroup(e.target.value ? Number(e.target.value) : null)
                        }
                      >
                        {taxonGroups.map((group) => (
                          <option key={group.id} value={group.id}>
                            {group.name}
                          </option>
                        ))}
                      </Select>
                      <Spacer />
                      {selectedTaxa.length > 0 && (
                        <HStack>
                          <Text fontSize="sm" color="gray.500">
                            {selectedTaxa.length} selected
                          </Text>
                          <Button
                            size="sm"
                            colorScheme="green"
                            onClick={handleBulkValidate}
                          >
                            Validate Selected
                          </Button>
                        </HStack>
                      )}
                    </HStack>

                    {/* Taxa Table */}
                    {isLoading ? (
                      <Center py={10}>
                        <Spinner size="xl" color="brand.500" />
                      </Center>
                    ) : (
                      <>
                        <Box overflowX="auto">
                          <Table variant="simple" size="sm">
                            <Thead>
                              <Tr>
                                <Th w="40px">
                                  <Checkbox
                                    isChecked={selectedTaxa.length === taxa.length && taxa.length > 0}
                                    onChange={(e) =>
                                      setSelectedTaxa(
                                        e.target.checked ? taxa.map((t) => t.id) : []
                                      )
                                    }
                                  />
                                </Th>
                                <Th>Scientific Name</Th>
                                <Th>Rank</Th>
                                <Th>Status</Th>
                                <Th>IUCN</Th>
                                <Th>Validated</Th>
                                <Th w="100px">Actions</Th>
                              </Tr>
                            </Thead>
                            <Tbody>
                              {taxa.map((taxon) => (
                                <Tr key={taxon.id}>
                                  <Td>
                                    <Checkbox
                                      isChecked={selectedTaxa.includes(taxon.id)}
                                      onChange={(e) =>
                                        setSelectedTaxa(
                                          e.target.checked
                                            ? [...selectedTaxa, taxon.id]
                                            : selectedTaxa.filter((id) => id !== taxon.id)
                                        )
                                      }
                                    />
                                  </Td>
                                  <Td>
                                    <Text fontStyle="italic">
                                      {taxon.canonicalName}
                                    </Text>
                                    {taxon.gbifKey && (
                                      <IconButton
                                        aria-label="View on GBIF"
                                        icon={<ExternalLinkIcon />}
                                        size="xs"
                                        variant="ghost"
                                        ml={1}
                                        onClick={() =>
                                          window.open(
                                            `https://www.gbif.org/species/${taxon.gbifKey}`,
                                            '_blank'
                                          )
                                        }
                                      />
                                    )}
                                  </Td>
                                  <Td>{taxon.rank}</Td>
                                  <Td>
                                    <Badge
                                      colorScheme={
                                        taxon.taxonomicStatus === 'ACCEPTED'
                                          ? 'green'
                                          : 'yellow'
                                      }
                                    >
                                      {taxon.taxonomicStatus}
                                    </Badge>
                                  </Td>
                                  <Td>
                                    {taxon.iucnStatus && (
                                      <Badge
                                        colorScheme={
                                          taxon.iucnStatus === 'CR'
                                            ? 'red'
                                            : taxon.iucnStatus === 'EN'
                                            ? 'orange'
                                            : taxon.iucnStatus === 'VU'
                                            ? 'yellow'
                                            : 'green'
                                        }
                                      >
                                        {taxon.iucnStatus}
                                      </Badge>
                                    )}
                                  </Td>
                                  <Td>
                                    {taxon.validated ? (
                                      <Badge colorScheme="green">Yes</Badge>
                                    ) : (
                                      <Button
                                        size="xs"
                                        colorScheme="blue"
                                        onClick={() => handleValidateTaxon(taxon.id)}
                                      >
                                        Validate
                                      </Button>
                                    )}
                                  </Td>
                                  <Td>
                                    <Menu>
                                      <MenuButton
                                        as={IconButton}
                                        aria-label="Actions"
                                        icon={<ChevronDownIcon />}
                                        size="sm"
                                        variant="ghost"
                                      />
                                      <MenuList>
                                        <MenuItem icon={<EditIcon />}>
                                          Edit
                                        </MenuItem>
                                        <MenuItem
                                          icon={<DeleteIcon />}
                                          color="red.500"
                                        >
                                          Delete
                                        </MenuItem>
                                      </MenuList>
                                    </Menu>
                                  </Td>
                                </Tr>
                              ))}
                            </Tbody>
                          </Table>
                        </Box>

                        {/* Pagination */}
                        <HStack justify="center" mt={4}>
                          <Button
                            size="sm"
                            isDisabled={page <= 1}
                            onClick={() => setPage(page - 1)}
                          >
                            Previous
                          </Button>
                          <Text>
                            Page {page} of {totalPages}
                          </Text>
                          <Button
                            size="sm"
                            isDisabled={page >= totalPages}
                            onClick={() => setPage(page + 1)}
                          >
                            Next
                          </Button>
                        </HStack>
                      </>
                    )}
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Proposals Tab */}
              <TabPanel px={0}>
                <Card bg={cardBg}>
                  <CardBody>
                    {proposals.length === 0 ? (
                      <Center py={10}>
                        <Text color="gray.500">No pending proposals</Text>
                      </Center>
                    ) : (
                      <Table variant="simple" size="sm">
                        <Thead>
                          <Tr>
                            <Th>Taxon</Th>
                            <Th>Change Type</Th>
                            <Th>Proposed By</Th>
                            <Th>Date</Th>
                            <Th>Actions</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {proposals.map((proposal) => (
                            <Tr key={proposal.id}>
                              <Td fontStyle="italic">
                                {proposal.taxon.canonicalName}
                              </Td>
                              <Td>
                                <Badge
                                  colorScheme={
                                    proposal.changeType === 'add'
                                      ? 'green'
                                      : proposal.changeType === 'delete'
                                      ? 'red'
                                      : 'blue'
                                  }
                                >
                                  {proposal.changeType}
                                </Badge>
                              </Td>
                              <Td>{proposal.proposedBy}</Td>
                              <Td>
                                {new Date(proposal.proposedAt).toLocaleDateString()}
                              </Td>
                              <Td>
                                <HStack>
                                  <IconButton
                                    aria-label="Approve"
                                    icon={<CheckIcon />}
                                    size="sm"
                                    colorScheme="green"
                                    onClick={() => handleApproveProposal(proposal.id)}
                                  />
                                  <IconButton
                                    aria-label="Reject"
                                    icon={<CloseIcon />}
                                    size="sm"
                                    colorScheme="red"
                                    onClick={() => handleRejectProposal(proposal.id)}
                                  />
                                </HStack>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    )}
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Groups Tab */}
              <TabPanel px={0}>
                <Card bg={cardBg}>
                  <CardBody>
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Name</Th>
                          <Th>Category</Th>
                          <Th>Taxa Count</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {taxonGroups.map((group) => (
                          <Tr key={group.id}>
                            <Td>{group.name}</Td>
                            <Td>{group.category || '-'}</Td>
                            <Td>{group.taxonCount?.toLocaleString() || 0}</Td>
                            <Td>
                              <IconButton
                                aria-label="Edit"
                                icon={<EditIcon />}
                                size="sm"
                                variant="ghost"
                              />
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </CardBody>
                </Card>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </VStack>

        {/* Add/Import Modal */}
        <Modal isOpen={isOpen} onClose={onClose} size="xl">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>
              {modalMode === 'gbif' ? 'Import from GBIF' : 'Add Taxon'}
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {modalMode === 'gbif' && (
                <VStack spacing={4} align="stretch">
                  <HStack>
                    <InputGroup>
                      <InputLeftElement>
                        <SearchIcon color="gray.400" />
                      </InputLeftElement>
                      <Input
                        placeholder="Search GBIF for species..."
                        value={gbifSearchQuery}
                        onChange={(e) => setGbifSearchQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleGbifSearch()}
                      />
                    </InputGroup>
                    <Button
                      colorScheme="brand"
                      onClick={handleGbifSearch}
                      isLoading={isSearchingGbif}
                    >
                      Search
                    </Button>
                  </HStack>

                  <Select
                    placeholder="Select target group"
                    value={selectedGroup || ''}
                    onChange={(e) =>
                      setSelectedGroup(e.target.value ? Number(e.target.value) : null)
                    }
                  >
                    {taxonGroups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name}
                      </option>
                    ))}
                  </Select>

                  {isSearchingGbif ? (
                    <Center py={6}>
                      <Spinner />
                    </Center>
                  ) : gbifResults.length > 0 ? (
                    <Box maxH="300px" overflowY="auto">
                      <Table size="sm">
                        <Thead>
                          <Tr>
                            <Th>Name</Th>
                            <Th>Rank</Th>
                            <Th>Status</Th>
                            <Th></Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {gbifResults.map((result) => (
                            <Tr key={result.key}>
                              <Td fontStyle="italic">{result.canonicalName}</Td>
                              <Td>{result.rank}</Td>
                              <Td>
                                <Badge
                                  colorScheme={
                                    result.status === 'ACCEPTED' ? 'green' : 'yellow'
                                  }
                                >
                                  {result.status}
                                </Badge>
                              </Td>
                              <Td>
                                <Button
                                  size="sm"
                                  colorScheme="brand"
                                  onClick={() => handleGbifImport(result.key)}
                                  isDisabled={!selectedGroup}
                                >
                                  Import
                                </Button>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </Box>
                  ) : gbifSearchQuery && !isSearchingGbif ? (
                    <Text color="gray.500" textAlign="center" py={4}>
                      No results found. Try a different search term.
                    </Text>
                  ) : null}
                </VStack>
              )}
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" onClick={onClose}>
                Cancel
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Container>
    </Box>
  );
};

export default TaxaManagementPage;
