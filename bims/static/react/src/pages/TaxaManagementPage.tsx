/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Taxa Management Page - Admin interface for managing taxonomic data.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Textarea,
  FormHelperText,
  Image,
  Link,
  Divider,
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
  ChevronRightIcon,
  ChevronDownIcon,
  TriangleDownIcon,
} from '@chakra-ui/icons';
import { useAuth } from '../providers/AuthProvider';
import { apiClient } from '../api/client';
import TaxaListDownloadModal from '../components/TaxaListDownloadModal';
import { PhylogeneticTree } from '../components/tree';

interface TaxonGroupStats {
  accepted_validated: number;
  synonym_validated: number;
  accepted_unvalidated: number;
  synonym_unvalidated: number;
  total_unvalidated: number;
}

interface TaxonGroupChild {
  id: number;
  name: string;
}

interface ModuleAttribute {
  id?: number;
  name: string;
  value: string;
}

interface ModuleExpert {
  id: number;
  username: string;
  name: string;
}

interface TaxonGroup {
  id: number;
  name: string;
  category?: string;
  logo_url?: string;
  taxa_count?: number;
  is_approved?: boolean;
  proposed_by_username?: string;
  rejection_reason?: string;
  parent_id?: number | null;
  parent_name?: string;
  children?: TaxonGroupChild[];
  validation_stats?: TaxonGroupStats;
  // Extended fields for editing
  experts?: ModuleExpert[];
  gbif_parent_species_id?: number;
  gbif_parent_species_name?: string;
  taxa_upload_template_url?: string;
  occurrence_upload_template_urls?: string[];
  additional_attributes?: ModuleAttribute[];
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
  author?: string;
  family?: string;
  accepted_taxonomy_name?: string;
  accepted_taxonomy_id?: number;
  biographic_distributions?: string;
  tag_list?: string;
  record_count?: number;
  parent_id?: number;
}

interface TaxonDetail extends Taxon {
  kingdom?: string;
  phylum?: string;
  class_name?: string;
  order?: string;
  subfamily?: string;
  tribe?: string;
  subtribe?: string;
  genus?: string;
  subgenus?: string;
  species_name?: string;
  subspecies?: string;
  species_group_name?: string;
  species_group_id?: number;
  iucn_status_full_name?: string;
  iucn_status_id?: number;
  common_name?: string;
  additional_data?: Record<string, string>;
  // Extended edit fields
  parent?: { id: number; canonical_name: string; rank: string };
  accepted_taxonomy?: { id: number; canonical_name: string; rank: string };
  biographic_distributions_detail?: { name: string; doubtful: boolean }[];
  tags?: string[];
  fada_id?: string;
  created_at_date?: string;
  last_modified?: string;
  user_last_modified?: string;
  origin?: string;
  endemism_name?: string;
}

// Extended interface for editing taxon
interface EditingTaxonState {
  id: number;
  rank: string;
  parent_id?: number | null;
  parent_name?: string;
  taxon_name: string;
  author: string;
  taxonomic_status: string;
  accepted_taxonomy_id?: number | null;
  accepted_taxonomy_name?: string;
  species_group_id?: number | null;
  species_group_name?: string;
  taxonomic_comments?: string;
  taxonomic_references?: string;
  common_name?: string;
  gbif_key?: number | null;
  biographic_distributions?: string[];
  biogeographic_comments?: string;
  biogeographic_references?: string;
  tags?: string[];
  environmental_comments?: string;
  environmental_references?: string;
  iucn_status_id?: number | null;
  conservation_comments?: string;
  conservation_references?: string;
  fada_id?: string;
}

// Module editing state
interface EditingModuleState {
  id: number;
  name: string;
  logo_file?: File | null;
  logo_url?: string;
  logo_preview?: string; // For local file preview
  additional_attributes: ModuleAttribute[];
  expert_ids: number[];
  experts: ModuleExpert[];
  parent_id?: number | null;
  gbif_taxonomy_id?: number | null;
  gbif_taxonomy_name?: string;
  taxa_upload_template_file?: File | null;
  taxa_upload_template_url?: string;
  occurrence_upload_template_files?: File[];
  occurrence_upload_template_urls?: string[];
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

const TaxaManagementPage: React.FC = () => {
  const toast = useToast();
  const { user, isAuthenticated } = useAuth();
  const { isOpen: isTaxaDownloadOpen, onOpen: onTaxaDownloadOpen, onClose: onTaxaDownloadClose } = useDisclosure();
  const { isOpen: isFiltersOpen, onToggle: onFiltersToggle } = useDisclosure();
  const { isOpen: isModuleModalOpen, onOpen: onModuleModalOpen, onClose: onModuleModalClose } = useDisclosure();

  const [activeTab, setActiveTab] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);

  // Expanded row state
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [taxonDetails, setTaxonDetails] = useState<Record<number, TaxonDetail>>({});
  const [loadingDetails, setLoadingDetails] = useState<Set<number>>(new Set());

  // Filter state
  const [rankFilter, setRankFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [validatedFilter, setValidatedFilter] = useState<string>('');

  // Pagination state
  const [pageSize, setPageSize] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
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

  // Module editing state (for Add/Edit Module modal)
  const [editingModule, setEditingModule] = useState<EditingModuleState | null>(null);
  const [isSavingModule, setIsSavingModule] = useState(false);
  const [moduleFormErrors, setModuleFormErrors] = useState<Record<string, string>>({});
  const [moduleFormTouched, setModuleFormTouched] = useState<Record<string, boolean>>({});
  const [expertSearchQuery, setExpertSearchQuery] = useState('');
  const [expertSearchResults, setExpertSearchResults] = useState<ModuleExpert[]>([]);
  const [isSearchingExperts, setIsSearchingExperts] = useState(false);
  const [isCreatingExpert, setIsCreatingExpert] = useState(false);
  const [newExpertData, setNewExpertData] = useState({ firstName: '', lastName: '', email: '' });
  const [gbifTaxaSearchQuery, setGbifTaxaSearchQuery] = useState('');
  const [gbifTaxaSearchResults, setGbifTaxaSearchResults] = useState<any[]>([]);

  // Extended taxon editing state (for full Edit Taxon form)
  const [editingTaxonFull, setEditingTaxonFull] = useState<EditingTaxonState | null>(null);
  const [isSavingTaxon, setIsSavingTaxon] = useState(false);
  const [parentSearchQuery, setParentSearchQuery] = useState('');
  const [parentSearchResults, setParentSearchResults] = useState<any[]>([]);
  const [acceptedTaxonSearchQuery, setAcceptedTaxonSearchQuery] = useState('');
  const [acceptedTaxonSearchResults, setAcceptedTaxonSearchResults] = useState<any[]>([]);
  const [speciesGroupSearchQuery, setSpeciesGroupSearchQuery] = useState('');
  const [speciesGroupSearchResults, setSpeciesGroupSearchResults] = useState<any[]>([]);
  const [biographicSearchResults, setBiographicSearchResults] = useState<string[]>([]);
  const [tagSearchResults, setTagSearchResults] = useState<string[]>([]);
  const [iucnStatusOptions, setIucnStatusOptions] = useState<{ id: number; category: string; label: string }[]>([]);

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

  // Check permissions
  const canManageTaxa = user?.isStaff || user?.isSuperuser;

  // Reusable function to fetch taxon groups
  const fetchTaxonGroups = useCallback(async () => {
    try {
      const response = await apiClient.get('taxon-groups/');
      const groups = response.data?.data || [];
      setTaxonGroups(groups);
      return groups;
    } catch (error) {
      console.error('Failed to fetch taxon groups:', error);
      return [];
    }
  }, []);

  // Fetch taxon groups on mount
  useEffect(() => {
    const fetchInitialGroups = async () => {
      const groups = await fetchTaxonGroups();
      // Auto-select first group if none selected
      if (!selectedGroup && groups.length > 0) {
        const rootGroups = groups.filter((g: TaxonGroup) => !g.parent_id && g.is_approved !== false);
        if (rootGroups.length > 0) {
          setSelectedGroup(rootGroups[0].id);
        }
      }
    };
    fetchInitialGroups();
  }, [fetchTaxonGroups]);

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
          page_size: pageSize,
          include_counts: true,
        };
        if (debouncedSearch) params.search = debouncedSearch;
        if (selectedGroup) params.taxon_group = selectedGroup;
        if (rankFilter) params.rank = rankFilter;
        if (statusFilter) params.taxonomic_status = statusFilter;
        if (validatedFilter) params.validated = validatedFilter === 'true';

        console.log('[TaxaManagement] Fetching taxa with params:', params);
        const response = await apiClient.get('taxa/', { params });
        console.log('[TaxaManagement] API response:', response.data);
        setTaxa(response.data?.data || []);
        setTotalPages(response.data?.meta?.total_pages || 1);
        setTotalCount(response.data?.meta?.count || 0);
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
  }, [debouncedSearch, selectedGroup, page, pageSize, rankFilter, statusFilter, validatedFilter, toast]);

  // Toggle row expansion and fetch details
  const toggleRowExpansion = useCallback(async (taxonId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(taxonId)) {
      newExpanded.delete(taxonId);
      setExpandedRows(newExpanded);
    } else {
      newExpanded.add(taxonId);
      setExpandedRows(newExpanded);

      // Fetch detail if not already loaded
      if (!taxonDetails[taxonId]) {
        setLoadingDetails((prev) => new Set(prev).add(taxonId));
        try {
          const response = await apiClient.get(`taxa/${taxonId}/`);
          if (response.data?.data) {
            setTaxonDetails((prev) => ({
              ...prev,
              [taxonId]: response.data.data,
            }));
          }
        } catch (error) {
          console.error(`Failed to fetch taxon detail ${taxonId}:`, error);
        } finally {
          setLoadingDetails((prev) => {
            const next = new Set(prev);
            next.delete(taxonId);
            return next;
          });
        }
      }
    }
  }, [expandedRows, taxonDetails]);

  // Approve all unvalidated taxa
  const handleApproveAllUnvalidated = useCallback(async () => {
    if (!selectedGroup) {
      toast({
        title: 'No group selected',
        description: 'Please select a taxon group first',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    if (!window.confirm('Approve all unvalidated taxa in this group?')) {
      return;
    }

    try {
      await apiClient.post('taxa-management/batch_validate/', {
        taxon_group: selectedGroup,
      });
      toast({
        title: 'Success',
        description: 'All unvalidated taxa have been approved',
        status: 'success',
        duration: 3000,
      });
      // Refresh the list
      setPage(1);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to approve taxa',
        status: 'error',
        duration: 5000,
      });
    }
  }, [selectedGroup, toast]);

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

  // Handle tree node selection - fetch taxon and open edit view
  const handleTreeNodeSelect = useCallback(async (nodeId: number) => {
    try {
      const response = await apiClient.get(`taxa/${nodeId}/`);
      if (response.data?.data) {
        openEditView(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch taxon:', error);
      toast({
        title: 'Error',
        description: 'Failed to load taxon details',
        status: 'error',
        duration: 3000,
      });
    }
  }, [toast]);

  const goBackToList = () => {
    setViewMode('list');
    setEditingTaxon(null);
    setEditingGroup(null);
  };

  const openAddModule = () => {
    setEditingModule({
      id: 0,
      name: '',
      logo_file: null,
      logo_url: undefined,
      additional_attributes: [],
      expert_ids: [],
      experts: [],
      parent_id: null,
      gbif_taxonomy_id: null,
      gbif_taxonomy_name: '',
      taxa_upload_template_file: null,
      taxa_upload_template_url: undefined,
      occurrence_upload_template_files: [],
      occurrence_upload_template_urls: [],
    });
    onModuleModalOpen();
  };

  const openEditModule = (group: TaxonGroup) => {
    setEditingModule({
      id: group.id,
      name: group.name,
      logo_file: null,
      logo_url: group.logo_url,
      additional_attributes: group.additional_attributes || [],
      expert_ids: group.experts?.map(e => e.id) || [],
      experts: group.experts || [],
      parent_id: group.parent_id || null,
      gbif_taxonomy_id: group.gbif_parent_species_id || null,
      gbif_taxonomy_name: group.gbif_parent_species_name || '',
      taxa_upload_template_file: null,
      taxa_upload_template_url: group.taxa_upload_template_url,
      occurrence_upload_template_files: [],
      occurrence_upload_template_urls: group.occurrence_upload_template_urls || [],
    });
    onModuleModalOpen();
  };

  // Keep old function names for backward compatibility
  const openAddGroup = openAddModule;
  const openEditGroup = openEditModule;

  // Legacy handleSaveGroup kept for backward compatibility
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

  // Validate module form
  const validateModuleForm = useCallback((): boolean => {
    if (!editingModule) return false;

    const errors: Record<string, string> = {};

    // Name is required
    if (!editingModule.name || editingModule.name.trim() === '') {
      errors.name = 'Module name is required';
    } else if (editingModule.name.trim().length < 2) {
      errors.name = 'Module name must be at least 2 characters';
    }

    setModuleFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [editingModule]);

  // New handleSaveModule function for full module editing
  // Uses the original Django API endpoint which expects specific field names
  const handleSaveModule = useCallback(async () => {
    if (!editingModule) return;

    // Mark all fields as touched
    setModuleFormTouched({ name: true });

    // Validate form
    if (!validateModuleForm()) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors in the form before saving',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setIsSavingModule(true);
    try {
      const formData = new FormData();

      // Use the field names expected by the original Django API (/api/update-taxon-group/)
      formData.append('module_name', editingModule.name.trim());

      if (editingModule.logo_file) {
        formData.append('module_logo', editingModule.logo_file);
      }

      if (editingModule.parent_id) {
        formData.append('parent-taxon', editingModule.parent_id.toString());
      }

      if (editingModule.gbif_taxonomy_id) {
        formData.append('gbif-species', editingModule.gbif_taxonomy_id.toString());
      }

      // Add experts using the field name expected by Django
      editingModule.expert_ids.forEach(id => {
        formData.append('taxon-group-experts', id.toString());
      });

      // Add additional attributes (as repeated form fields, not JSON)
      editingModule.additional_attributes.forEach(attr => {
        if (attr.name) {
          formData.append('extra_attribute', attr.name);
        }
      });

      // Add taxa upload template
      if (editingModule.taxa_upload_template_file) {
        formData.append('taxa_upload_template', editingModule.taxa_upload_template_file);
      }

      // Add occurrence upload templates
      if (editingModule.occurrence_upload_template_files) {
        editingModule.occurrence_upload_template_files.forEach(file => {
          formData.append('occurrence_upload_templates', file);
        });
      }

      // If updating existing module, include the ID
      if (editingModule.id !== 0) {
        formData.append('module_id', editingModule.id.toString());
      }

      // Call the original Django API endpoint
      const response = await fetch('/api/update-taxon-group/', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        // Try to get error details from response
        let errorMessage = 'Failed to save module';
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.error) {
            errorMessage = errorData.error;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          } else if (typeof errorData === 'string') {
            errorMessage = errorData;
          }
        } catch {
          // If response is not JSON, try to get text
          try {
            const textError = await response.text();
            if (textError && textError.length < 200) {
              errorMessage = textError;
            }
          } catch {
            // Use default error message
          }
        }

        // Check for specific HTTP status codes
        if (response.status === 403) {
          errorMessage = 'Permission denied. You do not have permission to modify this module.';
        } else if (response.status === 401) {
          errorMessage = 'Authentication required. Please log in and try again.';
        } else if (response.status === 404) {
          errorMessage = 'Module not found. It may have been deleted.';
        } else if (response.status === 400) {
          errorMessage = `Invalid data: ${errorMessage}`;
        } else if (response.status >= 500) {
          errorMessage = 'Server error. Please try again later or contact support.';
        }

        throw new Error(errorMessage);
      }

      toast({
        title: editingModule.id === 0 ? 'Created' : 'Saved',
        description: editingModule.id === 0 ? 'Module has been created' : 'Module has been updated',
        status: 'success',
        duration: 3000,
      });

      // Refresh the taxon groups list
      await fetchTaxonGroups();

      // Clean up the preview URL and reset form state
      if (editingModule.logo_preview) {
        URL.revokeObjectURL(editingModule.logo_preview);
      }
      setEditingModule(null);
      setModuleFormErrors({});
      setModuleFormTouched({});
      onModuleModalClose();
    } catch (error: any) {
      toast({
        title: 'Error Saving Module',
        description: error.message || 'An unexpected error occurred. Please try again.',
        status: 'error',
        duration: 8000,
        isClosable: true,
      });
    } finally {
      setIsSavingModule(false);
    }
  }, [editingModule, toast, onModuleModalClose, fetchTaxonGroups, validateModuleForm]);

  // Close module modal and cleanup preview URL
  const handleCloseModuleModal = useCallback(() => {
    if (editingModule?.logo_preview) {
      URL.revokeObjectURL(editingModule.logo_preview);
    }
    setEditingModule(null);
    setModuleFormErrors({});
    setModuleFormTouched({});
    setIsCreatingExpert(false);
    setNewExpertData({ firstName: '', lastName: '', email: '' });
    onModuleModalClose();
  }, [editingModule, onModuleModalClose]);

  // Create new expert
  const handleCreateExpert = useCallback(async () => {
    if (!newExpertData.firstName.trim() || !newExpertData.email.trim()) {
      toast({
        title: 'Validation Error',
        description: 'First name and email are required to create an expert',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newExpertData.email.trim())) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a valid email address',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      // Use the v1 API endpoint for creating experts
      const response = await apiClient.post('auth/create_expert/', {
        first_name: newExpertData.firstName.trim(),
        last_name: newExpertData.lastName.trim(),
        email: newExpertData.email.trim(),
      });

      const data = response.data?.data;
      if (!data || !data.id) {
        throw new Error('Invalid response from server');
      }

      const newExpert: ModuleExpert = {
        id: data.id,
        username: data.username || newExpertData.email.split('@')[0],
        name: data.name || `${newExpertData.firstName} ${newExpertData.lastName}`.trim(),
      };

      // Add new expert to the module
      if (editingModule) {
        setEditingModule({
          ...editingModule,
          expert_ids: [...editingModule.expert_ids, newExpert.id],
          experts: [...editingModule.experts, newExpert],
        });
      }

      toast({
        title: 'Expert Created',
        description: `${newExpert.name} has been created and added as an expert`,
        status: 'success',
        duration: 3000,
      });

      // Reset form
      setIsCreatingExpert(false);
      setNewExpertData({ firstName: '', lastName: '', email: '' });
    } catch (error: any) {
      // Extract error message from API response
      let errorMessage = 'An unexpected error occurred';
      if (error.response?.data?.errors) {
        const errors = error.response.data.errors;
        if (typeof errors === 'object') {
          // Get first error message
          const firstKey = Object.keys(errors)[0];
          errorMessage = errors[firstKey];
        } else {
          errorMessage = String(errors);
        }
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      toast({
        title: 'Error Creating Expert',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  }, [newExpertData, editingModule, toast]);

  // Search for experts
  const handleExpertSearch = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setExpertSearchResults([]);
      return;
    }

    setIsSearchingExperts(true);
    try {
      const response = await apiClient.get('users/', { params: { search: query, page_size: 10 } });
      setExpertSearchResults(response.data?.data?.map((u: any) => ({
        id: u.id,
        username: u.username,
        name: u.first_name ? `${u.first_name} ${u.last_name}` : u.username,
      })) || []);
    } catch (error) {
      console.error('Failed to search experts:', error);
    } finally {
      setIsSearchingExperts(false);
    }
  }, []);

  // Add attribute to module
  const addModuleAttribute = useCallback(() => {
    if (!editingModule) return;
    setEditingModule({
      ...editingModule,
      additional_attributes: [...editingModule.additional_attributes, { name: '', value: '' }],
    });
  }, [editingModule]);

  // Remove attribute from module
  const removeModuleAttribute = useCallback((index: number) => {
    if (!editingModule) return;
    setEditingModule({
      ...editingModule,
      additional_attributes: editingModule.additional_attributes.filter((_, i) => i !== index),
    });
  }, [editingModule]);

  // Update attribute in module
  const updateModuleAttribute = useCallback((index: number, field: 'name' | 'value', value: string) => {
    if (!editingModule) return;
    const newAttrs = [...editingModule.additional_attributes];
    newAttrs[index] = { ...newAttrs[index], [field]: value };
    setEditingModule({ ...editingModule, additional_attributes: newAttrs });
  }, [editingModule]);

  // Add expert to module
  const addExpertToModule = useCallback((expert: ModuleExpert) => {
    if (!editingModule) return;
    if (editingModule.expert_ids.includes(expert.id)) return;
    setEditingModule({
      ...editingModule,
      expert_ids: [...editingModule.expert_ids, expert.id],
      experts: [...editingModule.experts, expert],
    });
    setExpertSearchQuery('');
    setExpertSearchResults([]);
  }, [editingModule]);

  // Remove expert from module
  const removeExpertFromModule = useCallback((expertId: number) => {
    if (!editingModule) return;
    setEditingModule({
      ...editingModule,
      expert_ids: editingModule.expert_ids.filter(id => id !== expertId),
      experts: editingModule.experts.filter(e => e.id !== expertId),
    });
  }, [editingModule]);

  // Remove occurrence template
  const removeOccurrenceTemplate = useCallback((index: number) => {
    if (!editingModule) return;
    setEditingModule({
      ...editingModule,
      occurrence_upload_template_urls: editingModule.occurrence_upload_template_urls?.filter((_, i) => i !== index) || [],
    });
  }, [editingModule]);

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

  // Edit Taxon View (Full form matching edit_taxon.html)
  if (viewMode === 'edit' && editingTaxon) {
    const taxonDetail = taxonDetails[editingTaxon.id];
    const showAcceptedTaxon = editingTaxon.taxonomic_status?.includes('SYNONYM') || editingTaxon.taxonomic_status === 'DOUBTFUL';

    return (
      <Box bg={bgColor} minH="calc(100vh - 100px)" py={8}>
        <Container maxW="container.lg">
          <VStack spacing={6} align="stretch">
            <HStack justify="space-between">
              <HStack>
                <IconButton
                  aria-label="Back to list"
                  icon={<CloseIcon />}
                  variant="ghost"
                  onClick={goBackToList}
                />
                <Heading size="lg">
                  Edit {editingTaxon.canonical_name || editingTaxon.scientific_name} ({editingTaxon.rank})
                </Heading>
              </HStack>
            </HStack>

            <Card bg={cardBg}>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  {/* Metadata Section */}
                  {taxonDetail?.created_at_date && (
                    <FormControl>
                      <FormLabel>Date added</FormLabel>
                      <Input value={taxonDetail.created_at_date} isReadOnly bg="gray.100" />
                    </FormControl>
                  )}

                  {taxonDetail?.last_modified && (
                    <FormControl>
                      <FormLabel>Last modified</FormLabel>
                      <Input value={taxonDetail.last_modified} isReadOnly bg="gray.100" />
                    </FormControl>
                  )}

                  <FormControl>
                    <FormLabel>Last modified by</FormLabel>
                    <Input value={taxonDetail?.user_last_modified || 'Admin'} isReadOnly bg="gray.100" />
                  </FormControl>

                  <Divider />

                  {/* Core Fields */}
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
                      <option value="SUBFAMILY">Subfamily</option>
                      <option value="TRIBE">Tribe</option>
                      <option value="GENUS">Genus</option>
                      <option value="SUBGENUS">Subgenus</option>
                      <option value="SPECIES">Species</option>
                      <option value="SUBSPECIES">Subspecies</option>
                    </Select>
                  </FormControl>

                  <FormControl>
                    <FormLabel>Parent</FormLabel>
                    <Input
                      placeholder="Search for parent taxon..."
                      value={taxonDetail?.parent ? `${taxonDetail.parent.canonical_name} (${taxonDetail.parent.rank})` : ''}
                      isReadOnly
                      bg="gray.50"
                    />
                    <FormHelperText>Parent taxon in the hierarchy</FormHelperText>
                  </FormControl>

                  <FormControl>
                    <FormLabel>Name</FormLabel>
                    <Input
                      value={editingTaxon.canonical_name || editingTaxon.scientific_name || ''}
                      onChange={(e) => setEditingTaxon({ ...editingTaxon, canonical_name: e.target.value })}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Author</FormLabel>
                    <Input
                      value={editingTaxon.author || ''}
                      onChange={(e) => setEditingTaxon({ ...editingTaxon, author: e.target.value })}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Status</FormLabel>
                    <Select
                      value={editingTaxon.taxonomic_status || 'ACCEPTED'}
                      onChange={(e) => setEditingTaxon({ ...editingTaxon, taxonomic_status: e.target.value })}
                    >
                      <option value="ACCEPTED">Accepted</option>
                      <option value="SYNONYM">Synonym</option>
                      <option value="DOUBTFUL">Doubtful</option>
                    </Select>
                  </FormControl>

                  {showAcceptedTaxon && (
                    <FormControl>
                      <FormLabel>Accepted Taxon</FormLabel>
                      <Input
                        placeholder="Search for accepted taxon..."
                        value={editingTaxon.accepted_taxonomy_name || ''}
                        isReadOnly
                        bg="gray.50"
                      />
                    </FormControl>
                  )}

                  <Divider />

                  {/* Taxonomy Section */}
                  <Heading size="sm" color="teal.600">Taxonomic Information</Heading>

                  <FormControl>
                    <FormLabel>Species Group</FormLabel>
                    <Input
                      placeholder="Search for species group..."
                      value={taxonDetail?.species_group_name || ''}
                      isReadOnly
                      bg="gray.50"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Taxonomic Comments</FormLabel>
                    <Textarea
                      rows={3}
                      value={taxonDetail?.additional_data?.['Taxonomic Comments'] || taxonDetail?.additional_data?.['Taxonomic comments'] || ''}
                      placeholder="Enter taxonomic comments..."
                      onChange={(e) => {
                        // For now, just update the local state; saving requires proper state management
                      }}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Taxonomic References</FormLabel>
                    <Input
                      value={taxonDetail?.additional_data?.['Taxonomic References'] || ''}
                      placeholder="Enter taxonomic references..."
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Common Name</FormLabel>
                    <Input
                      value={taxonDetail?.common_name || ''}
                      placeholder="Common name"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>GBIF Key</FormLabel>
                    <HStack>
                      <Input
                        value={editingTaxon.gbif_key || ''}
                        placeholder="GBIF identifier"
                        onChange={(e) => setEditingTaxon({ ...editingTaxon, gbif_key: e.target.value ? parseInt(e.target.value) : undefined })}
                      />
                      {editingTaxon.gbif_key && (
                        <Link
                          href={`https://www.gbif.org/species/${editingTaxon.gbif_key}`}
                          isExternal
                          color="blue.500"
                        >
                          Check in GBIF <ExternalLinkIcon mx="2px" />
                        </Link>
                      )}
                    </HStack>
                  </FormControl>

                  <Divider />

                  {/* Biogeographic Section */}
                  <Heading size="sm" color="teal.600">Biogeographic Information</Heading>

                  <FormControl>
                    <FormLabel>Biogeographic Distribution</FormLabel>
                    <Input
                      placeholder="Search for biographic distribution..."
                      value={editingTaxon.biographic_distributions || ''}
                      isReadOnly
                      bg="gray.50"
                    />
                    <FormHelperText>Multiple distributions can be selected</FormHelperText>
                  </FormControl>

                  <FormControl>
                    <FormLabel>Biogeographic Comments</FormLabel>
                    <Textarea
                      rows={3}
                      value={taxonDetail?.additional_data?.['Biogeographic Comments'] || ''}
                      placeholder="Enter biogeographic comments..."
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Biogeographic References</FormLabel>
                    <Input
                      value={taxonDetail?.additional_data?.['Biogeographic References'] || ''}
                      placeholder="Enter biogeographic references..."
                    />
                  </FormControl>

                  <Divider />

                  {/* Environmental Section */}
                  <Heading size="sm" color="teal.600">Environmental Information</Heading>

                  <FormControl>
                    <FormLabel>Tags</FormLabel>
                    <Input
                      placeholder="Search for tags..."
                      value={editingTaxon.tag_list || ''}
                      isReadOnly
                      bg="gray.50"
                    />
                    <FormHelperText>Multiple tags can be selected</FormHelperText>
                  </FormControl>

                  <FormControl>
                    <FormLabel>Environmental Comments</FormLabel>
                    <Textarea
                      rows={3}
                      value={taxonDetail?.additional_data?.['Environmental Comments'] || ''}
                      placeholder="Enter environmental comments..."
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Environmental References</FormLabel>
                    <Input
                      value={taxonDetail?.additional_data?.['Environmental References'] || ''}
                      placeholder="Enter environmental references..."
                    />
                  </FormControl>

                  <Divider />

                  {/* Conservation Section */}
                  <Heading size="sm" color="teal.600">Conservation Information</Heading>

                  <FormControl>
                    <FormLabel>Conservation Status</FormLabel>
                    <Select
                      value={editingTaxon.iucn_status?.category || 'NE'}
                    >
                      <option value="NE">Not Evaluated (NE)</option>
                      <option value="DD">Data Deficient (DD)</option>
                      <option value="LC">Least Concern (LC)</option>
                      <option value="NT">Near Threatened (NT)</option>
                      <option value="VU">Vulnerable (VU)</option>
                      <option value="EN">Endangered (EN)</option>
                      <option value="CR">Critically Endangered (CR)</option>
                      <option value="EW">Extinct in the Wild (EW)</option>
                      <option value="EX">Extinct (EX)</option>
                    </Select>
                  </FormControl>

                  <FormControl>
                    <FormLabel>Conservation Comments</FormLabel>
                    <Textarea
                      rows={3}
                      value={taxonDetail?.additional_data?.['Conservation Comments'] || taxonDetail?.additional_data?.['Conservation comments'] || ''}
                      placeholder="Enter conservation comments..."
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Conservation References</FormLabel>
                    <Input
                      value={taxonDetail?.additional_data?.['Conservation References'] || ''}
                      placeholder="Enter conservation references..."
                    />
                  </FormControl>

                  <Divider />

                  {/* Action Buttons */}
                  <HStack justify="space-between" pt={4}>
                    <Button
                      colorScheme="red"
                      variant="outline"
                      onClick={() => handleDeleteTaxon(editingTaxon.id)}
                    >
                      DELETE
                    </Button>
                    <HStack>
                      <Button variant="ghost" onClick={goBackToList}>
                        Cancel
                      </Button>
                      <Button colorScheme="green" onClick={handleSaveTaxon}>
                        SAVE
                      </Button>
                    </HStack>
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
                <HStack align="stretch" spacing={4}>
                  {/* Left Sidebar - Taxon Groups */}
                  <Box
                    w="250px"
                    minW="250px"
                    maxH="calc(100vh - 220px)"
                    bg={cardBg}
                    borderRadius="md"
                    borderWidth={1}
                    borderColor="gray.200"
                    overflowY="auto"
                    position="sticky"
                    top="20px"
                  >
                    <VStack align="stretch" spacing={0}>
                      {/* Render taxon groups hierarchically */}
                      {taxonGroups
                        .filter((g) => !g.parent_id && g.is_approved !== false)
                        .sort((a, b) => (a.name || '').localeCompare(b.name || ''))
                        .map((group) => (
                          <React.Fragment key={group.id}>
                            {/* Parent group */}
                            <Box
                              px={3}
                              py={2}
                              bg={selectedGroup === group.id ? 'brand.50' : 'transparent'}
                              borderLeftWidth={selectedGroup === group.id ? 4 : 0}
                              borderLeftColor="brand.500"
                              cursor="pointer"
                              _hover={{ bg: selectedGroup === group.id ? 'brand.50' : 'gray.50' }}
                              onClick={() => setSelectedGroup(group.id)}
                            >
                              <HStack justify="space-between">
                                <HStack spacing={2}>
                                  <Text fontWeight={selectedGroup === group.id ? 'bold' : 'medium'} fontSize="sm">
                                    {group.name}
                                  </Text>
                                  {group.is_approved && (
                                    <CheckIcon color="green.500" boxSize={3} />
                                  )}
                                </HStack>
                                <IconButton
                                  aria-label="Group options"
                                  icon={<HamburgerIcon />}
                                  size="xs"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    openEditGroup(group);
                                  }}
                                />
                              </HStack>
                              {/* Validation stats */}
                              {group.validation_stats && (
                                <VStack align="stretch" spacing={0} mt={1} fontSize="xs">
                                  <HStack spacing={1}>
                                    <Badge colorScheme="green" size="sm">VALIDATED</Badge>
                                    <Text color="gray.600">
                                      {group.validation_stats.accepted_validated} Accepted
                                    </Text>
                                    <Text color="gray.500">
                                      {group.validation_stats.synonym_validated} Synonym
                                    </Text>
                                  </HStack>
                                  {group.validation_stats.total_unvalidated > 0 && (
                                    <HStack spacing={1}>
                                      <Badge colorScheme="orange" size="sm">UNVALIDATED</Badge>
                                      <Text color="gray.600">
                                        {group.validation_stats.accepted_unvalidated} Accepted
                                      </Text>
                                      <Text color="gray.500">
                                        {group.validation_stats.synonym_unvalidated} Synonym
                                      </Text>
                                    </HStack>
                                  )}
                                </VStack>
                              )}
                            </Box>
                            {/* Child groups (nested) */}
                            {group.children && group.children.length > 0 && (
                              <VStack align="stretch" spacing={0} pl={4}>
                                {group.children.map((child) => {
                                  const childGroup = taxonGroups.find((g) => g.id === child.id);
                                  return (
                                    <Box
                                      key={child.id}
                                      px={3}
                                      py={2}
                                      bg={selectedGroup === child.id ? 'brand.50' : 'transparent'}
                                      borderLeftWidth={selectedGroup === child.id ? 4 : 0}
                                      borderLeftColor="brand.500"
                                      cursor="pointer"
                                      _hover={{ bg: selectedGroup === child.id ? 'brand.50' : 'gray.50' }}
                                      onClick={() => setSelectedGroup(child.id)}
                                    >
                                      <HStack justify="space-between">
                                        <Text fontWeight={selectedGroup === child.id ? 'bold' : 'normal'} fontSize="sm">
                                          {child.name}
                                        </Text>
                                        <IconButton
                                          aria-label="Group options"
                                          icon={<HamburgerIcon />}
                                          size="xs"
                                          variant="ghost"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            if (childGroup) openEditGroup(childGroup);
                                          }}
                                        />
                                      </HStack>
                                      {/* Child validation stats */}
                                      {childGroup?.validation_stats && (
                                        <VStack align="stretch" spacing={0} mt={1} fontSize="xs">
                                          <HStack spacing={1}>
                                            <Badge colorScheme="green" size="sm">VAL</Badge>
                                            <Text color="gray.600">
                                              {childGroup.validation_stats.accepted_validated} Acc
                                            </Text>
                                            <Text color="gray.500">
                                              {childGroup.validation_stats.synonym_validated} Syn
                                            </Text>
                                          </HStack>
                                          {childGroup.validation_stats.total_unvalidated > 0 && (
                                            <HStack spacing={1}>
                                              <Badge colorScheme="orange" size="sm">UNVAL</Badge>
                                              <Text color="gray.600">
                                                {childGroup.validation_stats.accepted_unvalidated} Acc
                                              </Text>
                                            </HStack>
                                          )}
                                        </VStack>
                                      )}
                                    </Box>
                                  );
                                })}
                              </VStack>
                            )}
                          </React.Fragment>
                        ))}
                      {/* Add Group Button */}
                      {canManageTaxa && (
                        <Center py={3}>
                          <IconButton
                            aria-label="Add taxon group"
                            icon={<AddIcon />}
                            colorScheme="green"
                            size="sm"
                            onClick={openAddGroup}
                          />
                        </Center>
                      )}
                    </VStack>
                  </Box>

                  {/* Main Content Area */}
                  <Box flex={1}>
                    <Card bg={cardBg}>
                      <CardBody>
                        {/* Selected Group Title */}
                        {selectedGroup && (
                          <Heading size="md" mb={4}>
                            {taxonGroups.find((g) => g.id === selectedGroup)?.name || 'Taxa'}
                          </Heading>
                        )}

                        {/* Filters */}
                        <HStack spacing={4} mb={4} flexWrap="wrap">
                          <InputGroup maxW="300px">
                            <InputLeftElement>
                              <SearchIcon color="gray.400" />
                            </InputLeftElement>
                            <Input
                              placeholder="Taxon Name"
                              value={searchQuery}
                              onChange={(e) => setSearchQuery(e.target.value)}
                            />
                          </InputGroup>
                          <Button
                            leftIcon={<SearchIcon />}
                        colorScheme="green"
                        size="md"
                        onClick={() => setDebouncedSearch(searchQuery)}
                      >
                        Search
                      </Button>
                      <Button
                        leftIcon={<TriangleDownIcon />}
                        colorScheme="cyan"
                        size="md"
                        onClick={onFiltersToggle}
                      >
                        Filters
                      </Button>
                      <Button
                        leftIcon={<CheckIcon />}
                        variant="outline"
                        colorScheme="blue"
                        size="md"
                        onClick={handleApproveAllUnvalidated}
                      >
                        Approve All Unvalidated
                      </Button>
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

                    {/* Collapsible Filters Panel */}
                    {isFiltersOpen && (
                      <Box
                        bg="gray.100"
                        p={4}
                        mb={4}
                        borderRadius="md"
                        position="relative"
                      >
                        <IconButton
                          aria-label="Close filters"
                          icon={<CloseIcon />}
                          size="xs"
                          position="absolute"
                          top={2}
                          right={2}
                          onClick={onFiltersToggle}
                        />
                        <VStack spacing={4} align="stretch">
                          <HStack spacing={4}>
                            <FormControl maxW="200px">
                              <FormLabel fontSize="sm">Rank</FormLabel>
                              <Select
                                size="sm"
                                placeholder="All Ranks"
                                value={rankFilter}
                                onChange={(e) => setRankFilter(e.target.value)}
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
                            <FormControl maxW="200px">
                              <FormLabel fontSize="sm">Taxonomic Status</FormLabel>
                              <Select
                                size="sm"
                                placeholder="All Statuses"
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                              >
                                <option value="ACCEPTED">Accepted</option>
                                <option value="SYNONYM">Synonym</option>
                                <option value="DOUBTFUL">Doubtful</option>
                              </Select>
                            </FormControl>
                            <FormControl maxW="200px">
                              <FormLabel fontSize="sm">Validated</FormLabel>
                              <Select
                                size="sm"
                                placeholder="All"
                                value={validatedFilter}
                                onChange={(e) => setValidatedFilter(e.target.value)}
                              >
                                <option value="true">Yes</option>
                                <option value="false">No</option>
                              </Select>
                            </FormControl>
                            <FormControl maxW="200px">
                              <FormLabel fontSize="sm">Group</FormLabel>
                              <Select
                                size="sm"
                                placeholder="All Groups"
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
                          </HStack>
                          <HStack justify="flex-end">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setRankFilter('');
                                setStatusFilter('');
                                setValidatedFilter('');
                              }}
                            >
                              Clear Filters
                            </Button>
                            <Button
                              size="sm"
                              colorScheme="green"
                              onClick={() => {
                                setPage(1);
                                onFiltersToggle();
                              }}
                            >
                              Apply
                            </Button>
                          </HStack>
                        </VStack>
                      </Box>
                    )}

                    {/* Taxa Display - Table or Tree */}
                    {showTreeView ? (
                      // Phylogenetic Tree View with D3 dendrogram
                      <Box h="70vh" position="relative">
                        <PhylogeneticTree
                          taxonGroupId={selectedGroup || undefined}
                          onNodeDoubleClick={handleTreeNodeSelect}
                          showLegend
                          showControls
                          height="70vh"
                        />
                      </Box>
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
                            <Thead bg="gray.100">
                              <Tr>
                                <Th w="30px" p={1}></Th>
                                <Th minW="200px">Taxon Name</Th>
                                <Th minW="120px">Author(s)</Th>
                                <Th minW="100px">Family</Th>
                                <Th minW="100px">Status</Th>
                                <Th minW="120px">Accepted Taxon</Th>
                                <Th minW="80px">Rank</Th>
                                <Th minW="150px">Biogeographic distribution</Th>
                                <Th minW="100px">Tags</Th>
                                <Th minW="80px">Records</Th>
                                <Th w="60px"></Th>
                              </Tr>
                            </Thead>
                            <Tbody>
                              {taxa.map((taxon) => (
                                <React.Fragment key={taxon.id}>
                                  <Tr
                                    _hover={{ bg: 'gray.50' }}
                                    cursor="pointer"
                                    onClick={() => toggleRowExpansion(taxon.id)}
                                  >
                                    <Td p={1}>
                                      <IconButton
                                        aria-label="Expand"
                                        icon={expandedRows.has(taxon.id) ? <ChevronDownIcon /> : <ChevronRightIcon />}
                                        size="xs"
                                        variant="ghost"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          toggleRowExpansion(taxon.id);
                                        }}
                                      />
                                    </Td>
                                    <Td>
                                      <Text fontStyle="italic" fontWeight="medium">
                                        {taxon.canonical_name || taxon.scientific_name}
                                      </Text>
                                      <HStack spacing={1} mt={1}>
                                        {taxon.gbif_key && (
                                          <Badge
                                            colorScheme="yellow"
                                            size="sm"
                                            cursor="pointer"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              window.open(`https://www.gbif.org/species/${taxon.gbif_key}`, '_blank');
                                            }}
                                          >
                                            GBIF
                                          </Badge>
                                        )}
                                        {!taxon.verified && (
                                          <Badge colorScheme="gray" size="sm">Unvalidated</Badge>
                                        )}
                                      </HStack>
                                    </Td>
                                    <Td fontSize="sm">{taxon.author || ''}</Td>
                                    <Td fontSize="sm">
                                      {taxon.taxonomic_status?.includes('SYNONYM') ? '' : (taxon.family || '')}
                                    </Td>
                                    <Td>
                                      <Badge
                                        colorScheme={
                                          taxon.taxonomic_status === 'ACCEPTED' ? 'green' :
                                          taxon.taxonomic_status?.includes('SYNONYM') ? 'blue' : 'yellow'
                                        }
                                        size="sm"
                                      >
                                        {taxon.taxonomic_status}
                                      </Badge>
                                    </Td>
                                    <Td fontSize="sm" fontStyle="italic">
                                      {taxon.accepted_taxonomy_name || ''}
                                    </Td>
                                    <Td fontSize="sm">{taxon.rank}</Td>
                                    <Td fontSize="sm">{taxon.biographic_distributions || ''}</Td>
                                    <Td fontSize="sm">{taxon.tag_list || ''}</Td>
                                    <Td>
                                      <HStack spacing={1}>
                                        <Text fontSize="sm">{taxon.record_count ?? 0}</Text>
                                        <SearchIcon boxSize={3} color="gray.400" />
                                      </HStack>
                                    </Td>
                                    <Td>
                                      <HStack spacing={0}>
                                        {taxon.gbif_key && (
                                          <IconButton
                                            aria-label="View on GBIF"
                                            icon={<ExternalLinkIcon />}
                                            size="sm"
                                            variant="ghost"
                                            colorScheme="yellow"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              window.open(`https://www.gbif.org/species/${taxon.gbif_key}`, '_blank');
                                            }}
                                          />
                                        )}
                                        <IconButton
                                          aria-label="Edit taxon"
                                          icon={<EditIcon />}
                                          size="sm"
                                          variant="ghost"
                                          colorScheme="red"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            openEditView(taxon);
                                          }}
                                        />
                                        <IconButton
                                          aria-label="Delete taxon"
                                          icon={<DeleteIcon />}
                                          size="sm"
                                          variant="ghost"
                                          colorScheme="red"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteTaxon(taxon.id);
                                          }}
                                        />
                                      </HStack>
                                    </Td>
                                  </Tr>
                                  {/* Expanded detail row */}
                                  {expandedRows.has(taxon.id) && (
                                    <Tr>
                                      <Td colSpan={11} bg="gray.50" p={0}>
                                        {loadingDetails.has(taxon.id) ? (
                                          <Center py={4}>
                                            <Spinner size="sm" />
                                            <Text ml={2} fontSize="sm">Loading...</Text>
                                          </Center>
                                        ) : taxonDetails[taxon.id] ? (
                                          <Box p={4}>
                                            {/* Supra-generic Information, Infra Categories, Valid/Accepted Names */}
                                            <HStack align="stretch" spacing={4} mb={4}>
                                              {/* Supra-generic Information */}
                                              <Box flex={1} borderWidth={1} borderRadius="md" overflow="hidden">
                                                <Box bg="teal.500" color="white" px={3} py={1} fontSize="sm" fontWeight="bold">
                                                  Supra-generic Information
                                                </Box>
                                                <VStack align="stretch" spacing={0} fontSize="sm">
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Kingdom</Text>
                                                    <Text>{taxonDetails[taxon.id].kingdom || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Phylum</Text>
                                                    <Text>{taxonDetails[taxon.id].phylum || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Class</Text>
                                                    <Text>{taxonDetails[taxon.id].class_name || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Order</Text>
                                                    <Text>{taxonDetails[taxon.id].order || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1}>
                                                    <Text fontWeight="bold" w="100px">Family</Text>
                                                    <Text>{taxonDetails[taxon.id].family || ''}</Text>
                                                  </HStack>
                                                </VStack>
                                              </Box>

                                              {/* Infra Categories */}
                                              <Box flex={1} borderWidth={1} borderRadius="md" overflow="hidden">
                                                <Box bg="teal.500" color="white" px={3} py={1} fontSize="sm" fontWeight="bold">
                                                  Infra Categories
                                                </Box>
                                                <VStack align="stretch" spacing={0} fontSize="sm">
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Subfamily</Text>
                                                    <Text>{taxonDetails[taxon.id].subfamily || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Tribe</Text>
                                                    <Text>{taxonDetails[taxon.id].tribe || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1}>
                                                    <Text fontWeight="bold" w="100px">Subtribe</Text>
                                                    <Text>{taxonDetails[taxon.id].subtribe || ''}</Text>
                                                  </HStack>
                                                </VStack>
                                              </Box>

                                              {/* Valid/Accepted Names */}
                                              <Box flex={1} borderWidth={1} borderRadius="md" overflow="hidden">
                                                <Box bg="teal.500" color="white" px={3} py={1} fontSize="sm" fontWeight="bold">
                                                  Valid/Accepted Names
                                                </Box>
                                                <VStack align="stretch" spacing={0} fontSize="sm">
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Genus</Text>
                                                    <Text>{taxonDetails[taxon.id].genus || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Subgenus</Text>
                                                    <Text>{taxonDetails[taxon.id].subgenus || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Species group</Text>
                                                    <Text>{taxonDetails[taxon.id].species_group_name || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Species</Text>
                                                    <Text>{taxonDetails[taxon.id].species_name || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1} borderBottomWidth={1}>
                                                    <Text fontWeight="bold" w="100px">Subspecies</Text>
                                                    <Text>{taxonDetails[taxon.id].subspecies || ''}</Text>
                                                  </HStack>
                                                  <HStack px={3} py={1}>
                                                    <Text fontWeight="bold" w="100px">Author(s)</Text>
                                                    <Text>{taxonDetails[taxon.id].author || ''}</Text>
                                                  </HStack>
                                                </VStack>
                                              </Box>
                                            </HStack>

                                            {/* Additional Information */}
                                            <Box borderWidth={1} borderRadius="md" overflow="hidden">
                                              <Box bg="green.500" color="white" px={3} py={1} fontSize="sm" fontWeight="bold">
                                                Additional Information
                                              </Box>
                                              <VStack align="stretch" spacing={0} fontSize="sm">
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Taxonomic Comments</Text>
                                                  <Text>{taxonDetails[taxon.id].additional_data?.['Taxonomic Comments'] || taxonDetails[taxon.id].additional_data?.['Taxonomic comments'] || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Taxonomic References</Text>
                                                  <Text>{taxonDetails[taxon.id].additional_data?.['Taxonomic References'] || taxonDetails[taxon.id].additional_data?.['Species Name References'] || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Biogeographic Comments</Text>
                                                  <Text>{taxonDetails[taxon.id].additional_data?.['Biogeographic Comments'] || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Biogeographic References</Text>
                                                  <Text>{taxonDetails[taxon.id].additional_data?.['Biogeographic References'] || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Environmental Comments</Text>
                                                  <Text>{taxonDetails[taxon.id].additional_data?.['Environmental Comments'] || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Environmental References</Text>
                                                  <Text>{taxonDetails[taxon.id].additional_data?.['Environmental References'] || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Conservation Status</Text>
                                                  <Text>{taxonDetails[taxon.id].iucn_status_full_name || 'Not evaluated'}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Conservation Comments</Text>
                                                  <Text>{taxonDetails[taxon.id].additional_data?.['Conservation Comments'] || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Conservation References</Text>
                                                  <Text>{taxonDetails[taxon.id].additional_data?.['Conservation References'] || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1} borderBottomWidth={1}>
                                                  <Text fontWeight="bold" w="200px">Common Name</Text>
                                                  <Text>{taxonDetails[taxon.id].common_name || ''}</Text>
                                                </HStack>
                                                <HStack px={3} py={1}>
                                                  <Text fontWeight="bold" w="200px">GBIF Key</Text>
                                                  <Text>{taxonDetails[taxon.id].gbif_key || ''}</Text>
                                                </HStack>
                                              </VStack>
                                            </Box>
                                          </Box>
                                        ) : (
                                          <Center py={4}>
                                            <Text fontSize="sm" color="gray.500">No details available</Text>
                                          </Center>
                                        )}
                                      </Td>
                                    </Tr>
                                  )}
                                </React.Fragment>
                              ))}
                            </Tbody>
                          </Table>
                        </Box>

                        {/* Pagination - Original BIMS style */}
                        <HStack justify="space-between" mt={4} px={2}>
                          <HStack spacing={2}>
                            <Select
                              size="sm"
                              w="80px"
                              value={pageSize}
                              onChange={(e) => {
                                setPageSize(Number(e.target.value));
                                setPage(1);
                              }}
                            >
                              <option value={25}>25</option>
                              <option value={50}>50</option>
                              <option value={100}>100</option>
                            </Select>
                            <Text fontSize="sm" color="gray.600">entries per page</Text>
                          </HStack>

                          <Text fontSize="sm" color="gray.600">
                            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalCount)} of {totalCount} entries
                          </Text>

                          <HStack spacing={1}>
                            <Button
                              size="sm"
                              variant="outline"
                              isDisabled={page <= 1}
                              onClick={() => setPage(page - 1)}
                            >
                              &laquo;
                            </Button>
                            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                              let pageNum;
                              if (totalPages <= 5) {
                                pageNum = i + 1;
                              } else if (page <= 3) {
                                pageNum = i + 1;
                              } else if (page >= totalPages - 2) {
                                pageNum = totalPages - 4 + i;
                              } else {
                                pageNum = page - 2 + i;
                              }
                              return (
                                <Button
                                  key={pageNum}
                                  size="sm"
                                  variant={page === pageNum ? 'solid' : 'outline'}
                                  colorScheme={page === pageNum ? 'brand' : 'gray'}
                                  onClick={() => setPage(pageNum)}
                                >
                                  {pageNum}
                                </Button>
                              );
                            })}
                            <Button
                              size="sm"
                              variant="outline"
                              isDisabled={page >= totalPages}
                              onClick={() => setPage(page + 1)}
                            >
                              &raquo;
                            </Button>
                          </HStack>
                        </HStack>
                      </>
                      )
                    )}
                      </CardBody>
                    </Card>
                  </Box>
                </HStack>
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

        {/* Add/Edit Module Modal (matching original BIMS taxa_management.html editModuleModal) */}
        <Modal isOpen={isModuleModalOpen} onClose={handleCloseModuleModal} size="lg">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>
              {editingModule?.id === 0 ? 'Add Module' : 'Edit Module'}
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4} align="stretch">
                {/* Label */}
                <FormControl
                  isRequired
                  isInvalid={moduleFormTouched.name && !!moduleFormErrors.name}
                >
                  <FormLabel>
                    Label
                    <Text as="span" color="red.500" ml={1}>*</Text>
                  </FormLabel>
                  <Input
                    value={editingModule?.name || ''}
                    onChange={(e) => {
                      if (editingModule) {
                        setEditingModule({ ...editingModule, name: e.target.value });
                        // Clear error when user starts typing
                        if (moduleFormErrors.name && e.target.value.trim().length >= 2) {
                          setModuleFormErrors({ ...moduleFormErrors, name: '' });
                        }
                      }
                    }}
                    onBlur={() => {
                      setModuleFormTouched({ ...moduleFormTouched, name: true });
                      // Validate on blur
                      if (!editingModule?.name || editingModule.name.trim() === '') {
                        setModuleFormErrors({ ...moduleFormErrors, name: 'Module name is required' });
                      } else if (editingModule.name.trim().length < 2) {
                        setModuleFormErrors({ ...moduleFormErrors, name: 'Module name must be at least 2 characters' });
                      }
                    }}
                    placeholder="Enter module name"
                    borderColor={moduleFormTouched.name && moduleFormErrors.name ? 'red.500' : undefined}
                    focusBorderColor={moduleFormTouched.name && moduleFormErrors.name ? 'red.500' : 'brand.500'}
                    _hover={{ borderColor: moduleFormTouched.name && moduleFormErrors.name ? 'red.400' : 'gray.300' }}
                  />
                  {moduleFormTouched.name && moduleFormErrors.name && (
                    <Text color="red.500" fontSize="sm" mt={1}>
                      {moduleFormErrors.name}
                    </Text>
                  )}
                </FormControl>

                {/* Logo */}
                <FormControl>
                  <FormLabel>Logo</FormLabel>
                  <HStack spacing={4}>
                    {/* Show preview if available, otherwise show existing logo */}
                    {(editingModule?.logo_preview || editingModule?.logo_url) && (
                      <Image
                        src={editingModule.logo_preview || editingModule.logo_url}
                        alt="Module logo"
                        boxSize="60px"
                        objectFit="contain"
                        borderRadius="md"
                        border="1px solid"
                        borderColor="gray.200"
                      />
                    )}
                    <Input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file && editingModule) {
                          // Revoke old preview URL to prevent memory leak
                          if (editingModule.logo_preview) {
                            URL.revokeObjectURL(editingModule.logo_preview);
                          }
                          // Create a new preview URL for the selected file
                          const previewUrl = URL.createObjectURL(file);
                          setEditingModule({
                            ...editingModule,
                            logo_file: file,
                            logo_preview: previewUrl,
                          });
                        }
                      }}
                      p={1}
                    />
                  </HStack>
                </FormControl>

                {/* Additional Attributes */}
                <FormControl>
                  <FormLabel>Additional Attributes</FormLabel>
                  <VStack spacing={2} align="stretch">
                    <Button
                      colorScheme="yellow"
                      size="sm"
                      onClick={addModuleAttribute}
                      leftIcon={<AddIcon />}
                    >
                      Add Attribute +
                    </Button>
                    {editingModule?.additional_attributes.map((attr, index) => (
                      <HStack key={index}>
                        <Input
                          placeholder="Attribute name"
                          value={attr.name}
                          onChange={(e) => updateModuleAttribute(index, 'name', e.target.value)}
                          size="sm"
                        />
                        <Input
                          placeholder="Attribute value"
                          value={attr.value}
                          onChange={(e) => updateModuleAttribute(index, 'value', e.target.value)}
                          size="sm"
                        />
                        <IconButton
                          aria-label="Remove attribute"
                          icon={<CloseIcon />}
                          size="sm"
                          colorScheme="red"
                          variant="ghost"
                          onClick={() => removeModuleAttribute(index)}
                        />
                      </HStack>
                    ))}
                  </VStack>
                </FormControl>

                {/* Experts */}
                <FormControl>
                  <FormLabel>Experts</FormLabel>
                  <VStack spacing={2} align="stretch">
                    <HStack>
                      <InputGroup flex={1}>
                        <Input
                          placeholder="Search for an expert by name or email"
                          value={expertSearchQuery}
                          onChange={(e) => {
                            setExpertSearchQuery(e.target.value);
                            handleExpertSearch(e.target.value);
                          }}
                        />
                        {isSearchingExperts && (
                          <Box position="absolute" right={3} top="50%" transform="translateY(-50%)">
                            <Spinner size="sm" />
                          </Box>
                        )}
                      </InputGroup>
                      <Button
                        size="sm"
                        colorScheme="green"
                        leftIcon={<AddIcon />}
                        onClick={() => setIsCreatingExpert(true)}
                        title="Create a new expert if they don't exist in the system"
                      >
                        New
                      </Button>
                    </HStack>

                    {/* Create Expert Form */}
                    {isCreatingExpert && (
                      <Box
                        p={3}
                        border="1px solid"
                        borderColor="green.200"
                        borderRadius="md"
                        bg="green.50"
                      >
                        <Text fontWeight="medium" mb={2} fontSize="sm">Create New Expert</Text>
                        <VStack spacing={2}>
                          <HStack w="100%">
                            <FormControl isRequired flex={1}>
                              <Input
                                size="sm"
                                placeholder="First name *"
                                value={newExpertData.firstName}
                                onChange={(e) => setNewExpertData({ ...newExpertData, firstName: e.target.value })}
                                bg="white"
                              />
                            </FormControl>
                            <FormControl flex={1}>
                              <Input
                                size="sm"
                                placeholder="Last name"
                                value={newExpertData.lastName}
                                onChange={(e) => setNewExpertData({ ...newExpertData, lastName: e.target.value })}
                                bg="white"
                              />
                            </FormControl>
                          </HStack>
                          <FormControl isRequired>
                            <Input
                              size="sm"
                              type="email"
                              placeholder="Email address *"
                              value={newExpertData.email}
                              onChange={(e) => setNewExpertData({ ...newExpertData, email: e.target.value })}
                              bg="white"
                            />
                          </FormControl>
                          <HStack justify="flex-end" w="100%">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setIsCreatingExpert(false);
                                setNewExpertData({ firstName: '', lastName: '', email: '' });
                              }}
                            >
                              Cancel
                            </Button>
                            <Button
                              size="sm"
                              colorScheme="green"
                              onClick={handleCreateExpert}
                              isDisabled={!newExpertData.firstName.trim() || !newExpertData.email.trim()}
                            >
                              Create & Add
                            </Button>
                          </HStack>
                        </VStack>
                      </Box>
                    )}

                    {/* Search Results */}
                    {expertSearchResults.length > 0 && (
                      <Box
                        border="1px solid"
                        borderColor="gray.200"
                        borderRadius="md"
                        maxH="150px"
                        overflowY="auto"
                      >
                        {expertSearchResults.map((expert) => (
                          <Box
                            key={expert.id}
                            px={3}
                            py={2}
                            cursor="pointer"
                            _hover={{ bg: 'gray.100' }}
                            onClick={() => addExpertToModule(expert)}
                          >
                            {expert.name} (@{expert.username})
                          </Box>
                        ))}
                      </Box>
                    )}

                    {/* No Results Message */}
                    {expertSearchQuery.length >= 2 && !isSearchingExperts && expertSearchResults.length === 0 && (
                      <Text fontSize="sm" color="gray.500">
                        No experts found matching "{expertSearchQuery}". Click "New" to create one.
                      </Text>
                    )}

                    {/* Selected Experts */}
                    {editingModule?.experts && editingModule.experts.length > 0 && (
                      <Box>
                        <Text fontSize="sm" color="gray.600" mb={1}>Selected experts:</Text>
                        <HStack wrap="wrap" spacing={2}>
                          {editingModule.experts.map((expert) => (
                            <Badge
                              key={expert.id}
                              colorScheme="blue"
                              px={2}
                              py={1}
                              borderRadius="md"
                            >
                              {expert.name}
                              <IconButton
                                aria-label="Remove expert"
                                icon={<CloseIcon />}
                                size="xs"
                                variant="ghost"
                                ml={1}
                                onClick={() => removeExpertFromModule(expert.id)}
                              />
                            </Badge>
                          ))}
                        </HStack>
                      </Box>
                    )}
                  </VStack>
                </FormControl>

                {/* Taxa Upload Template */}
                <FormControl>
                  <FormLabel>Taxa Upload Template</FormLabel>
                  <VStack align="stretch" spacing={2}>
                    {editingModule?.taxa_upload_template_url && (
                      <Link href={editingModule.taxa_upload_template_url} isExternal color="blue.500">
                        Current template <ExternalLinkIcon mx="2px" />
                      </Link>
                    )}
                    <Input
                      type="file"
                      accept=".csv,.xls,.xlsx"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file && editingModule) {
                          setEditingModule({ ...editingModule, taxa_upload_template_file: file });
                        }
                      }}
                      p={1}
                    />
                  </VStack>
                </FormControl>

                {/* Occurrence Upload Templates */}
                <FormControl>
                  <FormLabel>Occurrence Upload Templates</FormLabel>
                  <VStack align="stretch" spacing={2}>
                    {editingModule?.occurrence_upload_template_urls && editingModule.occurrence_upload_template_urls.length > 0 && (
                      <VStack align="stretch" spacing={1}>
                        {editingModule.occurrence_upload_template_urls.map((url, index) => (
                          <HStack key={index} justify="space-between">
                            <Link href={url} isExternal color="blue.500" fontSize="sm">
                              Template {index + 1} <ExternalLinkIcon mx="2px" />
                            </Link>
                            <IconButton
                              aria-label="Remove template"
                              icon={<CloseIcon />}
                              size="xs"
                              variant="ghost"
                              colorScheme="red"
                              onClick={() => removeOccurrenceTemplate(index)}
                            />
                          </HStack>
                        ))}
                      </VStack>
                    )}
                    <Input
                      type="file"
                      accept=".csv,.xls,.xlsx"
                      multiple
                      onChange={(e) => {
                        const files = Array.from(e.target.files || []);
                        if (files.length > 0 && editingModule) {
                          setEditingModule({
                            ...editingModule,
                            occurrence_upload_template_files: [
                              ...(editingModule.occurrence_upload_template_files || []),
                              ...files,
                            ],
                          });
                        }
                      }}
                      p={1}
                    />
                    <FormHelperText>
                      You can select multiple files. Existing files will stay unless you remove them above.
                    </FormHelperText>
                  </VStack>
                </FormControl>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={handleCloseModuleModal}>
                Close
              </Button>
              <Button
                colorScheme="green"
                onClick={handleSaveModule}
                isLoading={isSavingModule}
                isDisabled={!editingModule?.name}
              >
                Save
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Container>
    </Box>
  );
};

export default TaxaManagementPage;
