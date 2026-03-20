/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Taxa Management Page - Admin interface for managing taxonomic data.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
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
  useColorModeValue,
  FormControl,
  FormLabel,
  Checkbox,
  Spacer,
} from '@chakra-ui/react';
import {
  SearchIcon,
  AddIcon,
  EditIcon,
  DeleteIcon,
  CheckIcon,
  CloseIcon,
  DownloadIcon,
  ExternalLinkIcon,
  ArrowBackIcon,
  ViewIcon,
  HamburgerIcon,
} from '@chakra-ui/icons';
import { useAuth } from '../providers/AuthProvider';
import { apiClient } from '../api/client';
import TaxaListDownloadModal from '../components/TaxaListDownloadModal';

interface TaxonGroup {
  id: number;
  name: string;
  category?: string;
  logo?: string;
  taxonCount?: number;
  is_approved?: boolean;
  proposed_by_username?: string;
  rejection_reason?: string;
}

interface Taxon {
  id: number;
  canonical_name: string;
  scientific_name: string;
  rank: string;
  taxonomic_status: string;
  iucn_status?: { category: string } | null;
  endemism?: { name: string } | null;
  verified: boolean;
  gbif_key?: number;
}

interface TaxonProposal {
  id: number;
  taxon: Taxon;
  proposed_by: string;
  proposed_at: string;
  status: 'pending' | 'approved' | 'rejected';
  notes?: string;
  change_type: 'add' | 'update' | 'merge' | 'delete';
}

interface TaxonTreeNode {
  id: number;
  name: string;
  rank: string;
  children: TaxonTreeNode[];
  expanded?: boolean;
}

// Tree Node Component for recursive rendering
const TreeNode: React.FC<{
  node: TaxonTreeNode;
  level: number;
  onToggle: (id: number) => void;
  onSelect: (id: number) => void;
  expandedNodes: Set<number>;
}> = ({ node, level, onToggle, onSelect, expandedNodes }) => {
  const isExpanded = expandedNodes.has(node.id);
  const hasChildren = node.children && node.children.length > 0;
  const indent = level * 20;

  const rankColors: Record<string, string> = {
    KINGDOM: 'purple',
    PHYLUM: 'blue',
    CLASS: 'cyan',
    ORDER: 'teal',
    FAMILY: 'green',
    GENUS: 'yellow',
    SPECIES: 'orange',
    SUBSPECIES: 'red',
  };

  return (
    <Box>
      <HStack
        py={1}
        px={2}
        pl={`${indent + 8}px`}
        _hover={{ bg: 'gray.50' }}
        cursor="pointer"
        borderLeftWidth={level > 0 ? 2 : 0}
        borderLeftColor="gray.200"
        ml={level > 0 ? 2 : 0}
      >
        {hasChildren ? (
          <IconButton
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
            icon={<Text fontSize="xs">{isExpanded ? '▼' : '▶'}</Text>}
            size="xs"
            variant="ghost"
            onClick={() => onToggle(node.id)}
          />
        ) : (
          <Box w="24px" />
        )}
        <Badge colorScheme={rankColors[node.rank] || 'gray'} size="sm" fontSize="xs">
          {node.rank?.substring(0, 3)}
        </Badge>
        <Text
          fontStyle={node.rank === 'SPECIES' || node.rank === 'GENUS' ? 'italic' : 'normal'}
          fontSize="sm"
          onClick={() => onSelect(node.id)}
          _hover={{ textDecoration: 'underline' }}
        >
          {node.name}
        </Text>
      </HStack>
      {isExpanded && hasChildren && (
        <Box>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onToggle={onToggle}
              onSelect={onSelect}
              expandedNodes={expandedNodes}
            />
          ))}
        </Box>
      )}
    </Box>
  );
};

const TaxaManagementPage: React.FC = () => {
  const toast = useToast();
  const { user, isAuthenticated } = useAuth();
  const { isOpen: isTaxaDownloadOpen, onOpen: onTaxaDownloadOpen, onClose: onTaxaDownloadClose } = useDisclosure();

  const [activeTab, setActiveTab] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  const [taxonGroups, setTaxonGroups] = useState<TaxonGroup[]>([]);
  const [pendingGroups, setPendingGroups] = useState<TaxonGroup[]>([]);
  const [taxa, setTaxa] = useState<Taxon[]>([]);
  const [proposals, setProposals] = useState<TaxonProposal[]>([]);
  const [selectedTaxa, setSelectedTaxa] = useState<number[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Tree view state
  const [showTreeView, setShowTreeView] = useState(false);
  const [treeData, setTreeData] = useState<TaxonTreeNode[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());
  const [isLoadingTree, setIsLoadingTree] = useState(false);

  // Debounce search query (300ms delay)
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    searchTimeoutRef.current = setTimeout(() => {
      console.log('[TaxaManagement] Debounced search:', searchQuery);
      setDebouncedSearch(searchQuery);
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  // Reset page when search changes
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  // View state: 'list' | 'edit' | 'gbif-import' | 'edit-group'
  const [viewMode, setViewMode] = useState<'list' | 'edit' | 'gbif-import' | 'edit-group'>('list');
  const [editingTaxon, setEditingTaxon] = useState<Taxon | null>(null);
  const [editingGroup, setEditingGroup] = useState<TaxonGroup | null>(null);
  const [gbifSearchQuery, setGbifSearchQuery] = useState('');
  const [gbifResults, setGbifResults] = useState<any[]>([]);
  const [isSearchingGbif, setIsSearchingGbif] = useState(false);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  // Fetch tree data when tree view is enabled
  useEffect(() => {
    const fetchTreeData = async () => {
      if (!showTreeView) return;

      setIsLoadingTree(true);
      try {
        // Get root taxa (those without parents or at kingdom/phylum level)
        const params: Record<string, any> = {
          has_parent: false,
          page_size: 100,
        };
        if (selectedGroup) params.taxon_group = selectedGroup;

        const response = await apiClient.get('taxa/', { params });
        const rootTaxa = response.data?.data || [];

        // Transform to tree nodes
        const treeNodes: TaxonTreeNode[] = rootTaxa.map((taxon: Taxon) => ({
          id: taxon.id,
          name: taxon.canonical_name || taxon.scientific_name,
          rank: taxon.rank,
          children: [],
        }));

        setTreeData(treeNodes);
      } catch (error) {
        console.error('Failed to fetch tree data:', error);
        toast({
          title: 'Error',
          description: 'Failed to load taxonomy tree',
          status: 'error',
          duration: 5000,
        });
      } finally {
        setIsLoadingTree(false);
      }
    };

    fetchTreeData();
  }, [showTreeView, selectedGroup, toast]);

  // Fetch children for a node when expanded
  const fetchChildren = useCallback(async (parentId: number): Promise<TaxonTreeNode[]> => {
    try {
      const response = await apiClient.get(`taxa/${parentId}/tree/`, {
        params: { direction: 'down', depth: 1 },
      });
      const data = response.data?.data;
      if (data?.children) {
        return data.children.map((child: any) => ({
          id: child.id,
          name: child.name,
          rank: child.rank,
          children: child.children || [],
        }));
      }
      return [];
    } catch (error) {
      console.error('Failed to fetch children:', error);
      return [];
    }
  }, []);

  // Toggle node expansion
  const handleTreeToggle = useCallback(async (nodeId: number) => {
    const newExpanded = new Set(expandedNodes);

    if (expandedNodes.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);

      // Fetch children if not already loaded
      const updateTreeWithChildren = async (nodes: TaxonTreeNode[]): Promise<TaxonTreeNode[]> => {
        return Promise.all(nodes.map(async (node) => {
          if (node.id === nodeId && node.children.length === 0) {
            const children = await fetchChildren(nodeId);
            return { ...node, children };
          }
          if (node.children.length > 0) {
            return { ...node, children: await updateTreeWithChildren(node.children) };
          }
          return node;
        }));
      };

      const updatedTree = await updateTreeWithChildren(treeData);
      setTreeData(updatedTree);
    }

    setExpandedNodes(newExpanded);
  }, [expandedNodes, treeData, fetchChildren]);

  // Handle tree node selection
  const handleTreeSelect = useCallback((nodeId: number) => {
    // Find the taxon and open edit view
    const findTaxon = async () => {
      try {
        const response = await apiClient.get(`taxa/${nodeId}/`);
        if (response.data?.data) {
          openEditView(response.data.data);
        }
      } catch (error) {
        console.error('Failed to fetch taxon:', error);
      }
    };
    findTaxon();
  }, []);

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

  // Fetch pending groups (for staff only)
  useEffect(() => {
    const fetchPendingGroups = async () => {
      if (!canManageTaxa) return;

      try {
        const response = await apiClient.get('taxon-groups/pending/');
        setPendingGroups(response.data?.data || []);
      } catch (error) {
        console.error('Failed to fetch pending groups:', error);
      }
    };
    fetchPendingGroups();
  }, [canManageTaxa]);

  // Fetch taxa based on filters (uses debounced search)
  useEffect(() => {
    const fetchTaxa = async () => {
      setIsLoading(true);
      try {
        const params: Record<string, any> = {
          page,
          page_size: 50,
        };
        if (debouncedSearch) params.search = debouncedSearch;
        if (selectedGroup) params.taxon_group = selectedGroup;

        console.log('[TaxaManagement] Fetching taxa with params:', params);
        const response = await apiClient.get('taxa/', { params });
        console.log('[TaxaManagement] API response:', response.data);
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
  }, [debouncedSearch, selectedGroup, page, toast]);

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
    if (!gbifSearchQuery.trim() || gbifSearchQuery.length < 2) return;

    setIsSearchingGbif(true);
    try {
      const response = await apiClient.get('taxa-management/find_gbif/', {
        params: { q: gbifSearchQuery, limit: 20 },
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
      const response = await apiClient.post('taxa-management/add_from_gbif/', {
        gbif_key: gbifKey,
        taxon_group: selectedGroup,
        create_proposal: false,
      });

      if (response.data?.data) {
        toast({
          title: 'Success',
          description: 'Taxon imported from GBIF',
          status: 'success',
          duration: 3000,
        });
        setViewMode('list');
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
  }, [selectedGroup, toast]);

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

  const openGbifImport = () => {
    setViewMode('gbif-import');
    setEditingTaxon(null);
    setGbifResults([]);
    setGbifSearchQuery('');
  };

  const openEditView = (taxon: Taxon) => {
    setViewMode('edit');
    setEditingTaxon({ ...taxon });
  };

  const goBackToList = () => {
    setViewMode('list');
    setEditingTaxon(null);
    setEditingGroup(null);
  };

  const openAddGroup = () => {
    setViewMode('edit-group');
    setEditingGroup({ id: 0, name: '', category: '' });
  };

  const openEditGroup = (group: TaxonGroup) => {
    setViewMode('edit-group');
    setEditingGroup({ ...group });
  };

  const handleSaveGroup = useCallback(async () => {
    if (!editingGroup) return;

    try {
      if (editingGroup.id === 0) {
        // Create new group
        const response = await apiClient.post('taxon-groups/', {
          name: editingGroup.name,
          singular_name: editingGroup.name,
          category: editingGroup.category || 'other',
          display_order: taxonGroups.length + 1,
        });
        setTaxonGroups([...taxonGroups, response.data?.data]);
        toast({
          title: 'Created',
          description: 'Taxon group has been created',
          status: 'success',
          duration: 3000,
        });
      } else {
        // Update existing group
        const response = await apiClient.patch(`taxon-groups/${editingGroup.id}/`, {
          name: editingGroup.name,
          category: editingGroup.category,
        });
        setTaxonGroups(taxonGroups.map((g) =>
          g.id === editingGroup.id ? { ...g, ...response.data?.data } : g
        ));
        toast({
          title: 'Saved',
          description: 'Taxon group has been updated',
          status: 'success',
          duration: 3000,
        });
      }
      setViewMode('list');
      setEditingGroup(null);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to save taxon group',
        status: 'error',
        duration: 5000,
      });
    }
  }, [editingGroup, taxonGroups, toast]);

  const handleDeleteGroup = useCallback(async (groupId: number) => {
    if (!window.confirm('Are you sure you want to delete this taxon group? This will not delete the taxa within it.')) {
      return;
    }

    try {
      await apiClient.delete(`taxon-groups/${groupId}/`);
      setTaxonGroups(taxonGroups.filter((g) => g.id !== groupId));
      setPendingGroups(pendingGroups.filter((g) => g.id !== groupId));
      toast({
        title: 'Deleted',
        description: 'Taxon group has been deleted',
        status: 'success',
        duration: 3000,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to delete taxon group',
        status: 'error',
        duration: 5000,
      });
    }
  }, [taxonGroups, pendingGroups, toast]);

  const handleApproveGroup = useCallback(async (groupId: number) => {
    try {
      const response = await apiClient.post(`taxon-groups/${groupId}/approve/`);
      const approvedGroup = response.data?.data;

      // Move from pending to approved
      setPendingGroups(pendingGroups.filter((g) => g.id !== groupId));
      setTaxonGroups([...taxonGroups, { ...approvedGroup, is_approved: true }]);

      toast({
        title: 'Approved',
        description: 'Taxon group has been approved',
        status: 'success',
        duration: 3000,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to approve taxon group',
        status: 'error',
        duration: 5000,
      });
    }
  }, [taxonGroups, pendingGroups, toast]);

  const handleRejectGroup = useCallback(async (groupId: number) => {
    const reason = window.prompt('Please provide a reason for rejection:');
    if (!reason) return;

    try {
      await apiClient.post(`taxon-groups/${groupId}/reject/`, { reason });
      setPendingGroups(pendingGroups.filter((g) => g.id !== groupId));

      toast({
        title: 'Rejected',
        description: 'Taxon group has been rejected',
        status: 'info',
        duration: 3000,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to reject taxon group',
        status: 'error',
        duration: 5000,
      });
    }
  }, [pendingGroups, toast]);

  const handleDeleteTaxon = useCallback(async (taxonId: number) => {
    if (!window.confirm('Are you sure you want to delete this taxon? This action cannot be undone.')) {
      return;
    }

    try {
      await apiClient.delete(`taxa/${taxonId}/`);
      setTaxa(taxa.filter((t) => t.id !== taxonId));
      toast({
        title: 'Deleted',
        description: 'Taxon has been deleted',
        status: 'success',
        duration: 3000,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to delete taxon',
        status: 'error',
        duration: 5000,
      });
    }
  }, [taxa, toast]);

  const handleSaveTaxon = useCallback(async () => {
    if (!editingTaxon) return;

    try {
      const response = await apiClient.patch(`taxa/${editingTaxon.id}/`, {
        scientific_name: editingTaxon.scientific_name,
        canonical_name: editingTaxon.canonical_name,
        rank: editingTaxon.rank,
        taxonomic_status: editingTaxon.taxonomic_status,
      });

      setTaxa(taxa.map((t) => (t.id === editingTaxon.id ? { ...t, ...response.data?.data } : t)));
      setViewMode('list');
      setEditingTaxon(null);
      toast({
        title: 'Saved',
        description: 'Taxon has been updated',
        status: 'success',
        duration: 3000,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to save taxon',
        status: 'error',
        duration: 5000,
      });
    }
  }, [editingTaxon, taxa, toast]);

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

  // Edit Group View
  if (viewMode === 'edit-group' && editingGroup) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 100px)" py={8}>
        <Container maxW="container.lg">
          <VStack spacing={6} align="stretch">
            <HStack>
              <IconButton
                aria-label="Back to list"
                icon={<ArrowBackIcon />}
                variant="ghost"
                onClick={goBackToList}
              />
              <Heading size="lg">
                {editingGroup.id === 0 ? 'Propose New Taxon Group' : 'Edit Taxon Group'}
              </Heading>
            </HStack>

            {editingGroup.id === 0 && (
              <Alert status="info">
                <AlertIcon />
                New taxon groups require approval before they can be used. Your proposal will be reviewed by an administrator.
              </Alert>
            )}

            <Card bg={cardBg}>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <FormControl isRequired>
                    <FormLabel>Group Name</FormLabel>
                    <Input
                      placeholder="e.g., Freshwater Fish"
                      value={editingGroup.name || ''}
                      onChange={(e) => setEditingGroup({ ...editingGroup, name: e.target.value })}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Category</FormLabel>
                    <Select
                      value={editingGroup.category || ''}
                      onChange={(e) => setEditingGroup({ ...editingGroup, category: e.target.value })}
                    >
                      <option value="">Select category...</option>
                      <option value="fish">Fish</option>
                      <option value="invertebrate">Invertebrate</option>
                      <option value="algae">Algae</option>
                      <option value="plant">Plant</option>
                      <option value="other">Other</option>
                    </Select>
                  </FormControl>

                  <HStack justify="flex-end" pt={4}>
                    <Button variant="ghost" onClick={goBackToList}>
                      Cancel
                    </Button>
                    <Button
                      colorScheme="brand"
                      onClick={handleSaveGroup}
                      isDisabled={!editingGroup.name}
                    >
                      {editingGroup.id === 0 ? 'Submit for Review' : 'Save Changes'}
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </Container>
      </Box>
    );
  }

  // Edit Taxon View
  if (viewMode === 'edit' && editingTaxon) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 100px)" py={8}>
        <Container maxW="container.lg">
          <VStack spacing={6} align="stretch">
            <HStack>
              <IconButton
                aria-label="Back to list"
                icon={<ArrowBackIcon />}
                variant="ghost"
                onClick={goBackToList}
              />
              <Heading size="lg">Edit Taxon</Heading>
            </HStack>

            <Card bg={cardBg}>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <FormControl>
                    <FormLabel>Scientific Name</FormLabel>
                    <Input
                      value={editingTaxon.scientific_name || ''}
                      onChange={(e) => setEditingTaxon({ ...editingTaxon, scientific_name: e.target.value })}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Canonical Name</FormLabel>
                    <Input
                      value={editingTaxon.canonical_name || ''}
                      onChange={(e) => setEditingTaxon({ ...editingTaxon, canonical_name: e.target.value })}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Rank</FormLabel>
                    <Select
                      value={editingTaxon.rank || ''}
                      onChange={(e) => setEditingTaxon({ ...editingTaxon, rank: e.target.value })}
                    >
                      <option value="KINGDOM">Kingdom</option>
                      <option value="PHYLUM">Phylum</option>
                      <option value="CLASS">Class</option>
                      <option value="ORDER">Order</option>
                      <option value="FAMILY">Family</option>
                      <option value="GENUS">Genus</option>
                      <option value="SPECIES">Species</option>
                      <option value="SUBSPECIES">Subspecies</option>
                    </Select>
                  </FormControl>

                  <FormControl>
                    <FormLabel>Taxonomic Status</FormLabel>
                    <Select
                      value={editingTaxon.taxonomic_status || ''}
                      onChange={(e) => setEditingTaxon({ ...editingTaxon, taxonomic_status: e.target.value })}
                    >
                      <option value="ACCEPTED">Accepted</option>
                      <option value="SYNONYM">Synonym</option>
                      <option value="DOUBTFUL">Doubtful</option>
                    </Select>
                  </FormControl>

                  <HStack justify="flex-end" pt={4}>
                    <Button variant="ghost" onClick={goBackToList}>
                      Cancel
                    </Button>
                    <Button colorScheme="brand" onClick={handleSaveTaxon}>
                      Save Changes
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </Container>
      </Box>
    );
  }

  // GBIF Import View
  if (viewMode === 'gbif-import') {
    return (
      <Box bg={bgColor} minH="calc(100vh - 100px)" py={8}>
        <Container maxW="container.lg">
          <VStack spacing={6} align="stretch">
            <HStack>
              <IconButton
                aria-label="Back to list"
                icon={<ArrowBackIcon />}
                variant="ghost"
                onClick={goBackToList}
              />
              <Heading size="lg">Import from GBIF</Heading>
            </HStack>

            <Card bg={cardBg}>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <HStack>
                    <InputGroup flex={1}>
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

                  <FormControl>
                    <FormLabel>Target Group</FormLabel>
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
                  </FormControl>

                  {isSearchingGbif ? (
                    <Center py={10}>
                      <Spinner size="xl" color="brand.500" />
                    </Center>
                  ) : gbifResults.length > 0 ? (
                    <Box overflowX="auto">
                      <Table size="sm">
                        <Thead>
                          <Tr>
                            <Th>Name</Th>
                            <Th>Rank</Th>
                            <Th>Status</Th>
                            <Th w="100px"></Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {gbifResults.map((result) => (
                            <Tr key={result.gbif_key || result.id}>
                              <Td fontStyle="italic">
                                {result.canonical_name || result.scientific_name}
                                {result.source === 'local' && (
                                  <Badge ml={2} colorScheme="blue" size="sm">Local</Badge>
                                )}
                              </Td>
                              <Td>{result.rank}</Td>
                              <Td>
                                <Badge
                                  colorScheme={result.status === 'ACCEPTED' || result.source === 'local' ? 'green' : 'yellow'}
                                >
                                  {result.status || (result.validated ? 'Validated' : 'Pending')}
                                </Badge>
                              </Td>
                              <Td>
                                {result.source === 'local' ? (
                                  <Badge colorScheme="gray">Already exists</Badge>
                                ) : (
                                  <Button
                                    size="sm"
                                    colorScheme="brand"
                                    onClick={() => handleGbifImport(result.gbif_key)}
                                    isDisabled={!selectedGroup}
                                  >
                                    Import
                                  </Button>
                                )}
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </Box>
                  ) : gbifSearchQuery && !isSearchingGbif ? (
                    <Center py={10}>
                      <Text color="gray.500">No results found. Try a different search term.</Text>
                    </Center>
                  ) : (
                    <Center py={10}>
                      <Text color="gray.500">Search GBIF to find and import taxa.</Text>
                    </Center>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </Container>
      </Box>
    );
  }

  // List View (default)
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
                onClick={onTaxaDownloadOpen}
              >
                Export
              </Button>
              <Button
                leftIcon={<AddIcon />}
                colorScheme="brand"
                onClick={openGbifImport}
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
                      <HStack>
                        <IconButton
                          aria-label="Table view"
                          icon={<HamburgerIcon />}
                          size="sm"
                          variant={!showTreeView ? 'solid' : 'outline'}
                          colorScheme={!showTreeView ? 'brand' : 'gray'}
                          onClick={() => setShowTreeView(false)}
                        />
                        <IconButton
                          aria-label="Tree view"
                          icon={<ViewIcon />}
                          size="sm"
                          variant={showTreeView ? 'solid' : 'outline'}
                          colorScheme={showTreeView ? 'brand' : 'gray'}
                          onClick={() => setShowTreeView(true)}
                        />
                      </HStack>
                      {selectedTaxa.length > 0 && !showTreeView && (
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

                    {/* Taxa Display - Table or Tree */}
                    {showTreeView ? (
                      // Tree View
                      isLoadingTree ? (
                        <Center py={10}>
                          <Spinner size="xl" color="brand.500" />
                        </Center>
                      ) : (
                        <Box
                          border="1px"
                          borderColor="gray.200"
                          borderRadius="md"
                          maxH="600px"
                          overflowY="auto"
                          bg="white"
                        >
                          {treeData.length === 0 ? (
                            <Center py={10}>
                              <Text color="gray.500">No taxa found. Select a group to view the taxonomy tree.</Text>
                            </Center>
                          ) : (
                            <Box py={2}>
                              {treeData.map((node) => (
                                <TreeNode
                                  key={node.id}
                                  node={node}
                                  level={0}
                                  onToggle={handleTreeToggle}
                                  onSelect={handleTreeSelect}
                                  expandedNodes={expandedNodes}
                                />
                              ))}
                            </Box>
                          )}
                        </Box>
                      )
                    ) : (
                      // Table View
                      isLoading ? (
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
                                      {taxon.canonical_name}
                                    </Text>
                                    {taxon.gbif_key && (
                                      <IconButton
                                        aria-label="View on GBIF"
                                        icon={<ExternalLinkIcon />}
                                        size="xs"
                                        variant="ghost"
                                        ml={1}
                                        onClick={() =>
                                          window.open(
                                            `https://www.gbif.org/species/${taxon.gbif_key}`,
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
                                        taxon.taxonomic_status === 'ACCEPTED'
                                          ? 'green'
                                          : 'yellow'
                                      }
                                    >
                                      {taxon.taxonomic_status}
                                    </Badge>
                                  </Td>
                                  <Td>
                                    {taxon.iucn_status?.category && (
                                      <Badge
                                        colorScheme={
                                          taxon.iucn_status.category === 'CR'
                                            ? 'red'
                                            : taxon.iucn_status.category === 'EN'
                                            ? 'orange'
                                            : taxon.iucn_status.category === 'VU'
                                            ? 'yellow'
                                            : 'green'
                                        }
                                      >
                                        {taxon.iucn_status.category}
                                      </Badge>
                                    )}
                                  </Td>
                                  <Td>
                                    {taxon.verified ? (
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
                                    <HStack spacing={1}>
                                      <IconButton
                                        aria-label="Edit taxon"
                                        icon={<EditIcon />}
                                        size="sm"
                                        variant="ghost"
                                        colorScheme="blue"
                                        onClick={() => openEditView(taxon)}
                                      />
                                      <IconButton
                                        aria-label="Delete taxon"
                                        icon={<DeleteIcon />}
                                        size="sm"
                                        variant="ghost"
                                        colorScheme="red"
                                        onClick={() => handleDeleteTaxon(taxon.id)}
                                      />
                                    </HStack>
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
                      )
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
                                {proposal.taxon.canonical_name}
                              </Td>
                              <Td>
                                <Badge
                                  colorScheme={
                                    proposal.change_type === 'add'
                                      ? 'green'
                                      : proposal.change_type === 'delete'
                                      ? 'red'
                                      : 'blue'
                                  }
                                >
                                  {proposal.change_type}
                                </Badge>
                              </Td>
                              <Td>{proposal.proposed_by}</Td>
                              <Td>
                                {new Date(proposal.proposed_at).toLocaleDateString()}
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
                <VStack spacing={4} align="stretch">
                  {/* Pending Groups Section (Staff Only) */}
                  {pendingGroups.length > 0 && (
                    <Card bg="orange.50" borderColor="orange.200" borderWidth={1}>
                      <CardBody>
                        <Heading size="sm" mb={4} color="orange.700">
                          Pending Proposals ({pendingGroups.length})
                        </Heading>
                        <Table variant="simple" size="sm">
                          <Thead>
                            <Tr>
                              <Th>Name</Th>
                              <Th>Category</Th>
                              <Th>Proposed By</Th>
                              <Th w="150px">Actions</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {pendingGroups.map((group) => (
                              <Tr key={group.id}>
                                <Td>{group.name}</Td>
                                <Td>
                                  <Badge colorScheme="blue">{group.category || 'other'}</Badge>
                                </Td>
                                <Td>{group.proposed_by_username || 'Unknown'}</Td>
                                <Td>
                                  <HStack spacing={1}>
                                    <IconButton
                                      aria-label="Approve"
                                      icon={<CheckIcon />}
                                      size="sm"
                                      colorScheme="green"
                                      onClick={() => handleApproveGroup(group.id)}
                                    />
                                    <IconButton
                                      aria-label="Reject"
                                      icon={<CloseIcon />}
                                      size="sm"
                                      colorScheme="red"
                                      onClick={() => handleRejectGroup(group.id)}
                                    />
                                    <IconButton
                                      aria-label="Edit"
                                      icon={<EditIcon />}
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => openEditGroup(group)}
                                    />
                                  </HStack>
                                </Td>
                              </Tr>
                            ))}
                          </Tbody>
                        </Table>
                      </CardBody>
                    </Card>
                  )}

                  {/* Approved Groups */}
                  <Card bg={cardBg}>
                    <CardBody>
                      <HStack justify="space-between" mb={4}>
                        <Heading size="sm">Approved Groups</Heading>
                        <Button
                          leftIcon={<AddIcon />}
                          colorScheme="brand"
                          size="sm"
                          onClick={openAddGroup}
                        >
                          Propose New Group
                        </Button>
                      </HStack>
                      <Table variant="simple">
                        <Thead>
                          <Tr>
                            <Th>Name</Th>
                            <Th>Category</Th>
                            <Th>Taxa Count</Th>
                            <Th w="120px">Actions</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {taxonGroups.filter(g => g.is_approved !== false).map((group) => (
                            <Tr key={group.id}>
                              <Td>{group.name}</Td>
                              <Td>
                                <Badge colorScheme="blue">{group.category || 'other'}</Badge>
                              </Td>
                              <Td>{group.taxonCount?.toLocaleString() || 0}</Td>
                              <Td>
                                <HStack spacing={1}>
                                  <IconButton
                                    aria-label="Edit group"
                                    icon={<EditIcon />}
                                    size="sm"
                                    variant="ghost"
                                    colorScheme="blue"
                                    onClick={() => openEditGroup(group)}
                                  />
                                  <IconButton
                                    aria-label="Delete group"
                                    icon={<DeleteIcon />}
                                    size="sm"
                                    variant="ghost"
                                    colorScheme="red"
                                    onClick={() => handleDeleteGroup(group.id)}
                                  />
                                </HStack>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </CardBody>
                  </Card>
                </VStack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </VStack>

        {/* Taxa List Download Modal */}
        <TaxaListDownloadModal
          isOpen={isTaxaDownloadOpen}
          onClose={onTaxaDownloadClose}
          preselectedTaxonGroupId={selectedGroup || undefined}
        />
      </Container>
    </Box>
  );
};

export default TaxaManagementPage;
