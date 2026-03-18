/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Site Visits (Surveys) listing page.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Button,
  HStack,
  VStack,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Card,
  CardBody,
  Spinner,
  Center,
  IconButton,
  useToast,
  Flex,
  Spacer,
  Checkbox,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Textarea,
} from '@chakra-ui/react';
import {
  SearchIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ViewIcon,
  EditIcon,
  DeleteIcon,
  CheckIcon,
  CloseIcon,
  ChevronDownIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { surveysApi } from '../api/client';

interface SiteVisit {
  id: number;
  site_name: string;
  site_code: string;
  date: string;
  collector: string;
  owner: string;
  record_count: number;
  validated: boolean;
  rejected: boolean;
}

const SiteVisitsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [visits, setVisits] = useState<SiteVisit[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [validationFilter, setValidationFilter] = useState(searchParams.get('inReview') || '');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [rejectReason, setRejectReason] = useState('');
  const [actionType, setActionType] = useState<'validate' | 'reject'>('validate');
  const toast = useToast();

  useEffect(() => {
    fetchVisits();
  }, [page, searchTerm, validationFilter]);

  const fetchVisits = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        page,
        page_size: 20,
      };
      if (searchTerm) params.search = searchTerm;
      if (validationFilter === 'pending') params.validated = false;
      if (validationFilter === 'validated') params.validated = true;
      if (validationFilter === 'rejected') params.rejected = true;

      const response = await surveysApi.list(params);
      setVisits(response.data || []);
      setTotalPages(response.meta?.total_pages || 1);
      setTotalCount(response.meta?.count || 0);
    } catch (error) {
      toast({
        title: 'Error loading site visits',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(visits.map((v) => v.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelect = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter((i) => i !== id));
    }
  };

  const handleBulkAction = async () => {
    try {
      if (actionType === 'validate') {
        await surveysApi.bulkValidate(selectedIds);
        toast({
          title: 'Visits validated',
          status: 'success',
          duration: 3000,
        });
      } else {
        await surveysApi.bulkReject(selectedIds, rejectReason);
        toast({
          title: 'Visits rejected',
          status: 'success',
          duration: 3000,
        });
      }
      setSelectedIds([]);
      setRejectReason('');
      onClose();
      fetchVisits();
    } catch (error) {
      toast({
        title: 'Action failed',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const openBulkAction = (type: 'validate' | 'reject') => {
    setActionType(type);
    if (type === 'reject') {
      onOpen();
    } else {
      handleBulkAction();
    }
  };

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Flex align="center">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Site Visits</Heading>
            <Text color="gray.600">
              Browse and manage field survey records
            </Text>
          </VStack>
          <Spacer />
          {selectedIds.length > 0 && (
            <Menu>
              <MenuButton as={Button} colorScheme="brand" rightIcon={<ChevronDownIcon />}>
                Actions ({selectedIds.length})
              </MenuButton>
              <MenuList>
                <MenuItem icon={<CheckIcon />} onClick={() => openBulkAction('validate')}>
                  Validate Selected
                </MenuItem>
                <MenuItem icon={<CloseIcon />} color="red.500" onClick={() => openBulkAction('reject')}>
                  Reject Selected
                </MenuItem>
              </MenuList>
            </Menu>
          )}
        </Flex>

        {/* Filters */}
        <Card>
          <CardBody>
            <HStack spacing={4} flexWrap="wrap">
              <InputGroup maxW="400px">
                <InputLeftElement>
                  <SearchIcon color="gray.400" />
                </InputLeftElement>
                <Input
                  placeholder="Search by site name, collector..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setPage(1);
                  }}
                />
              </InputGroup>
              <Select
                maxW="200px"
                value={validationFilter}
                onChange={(e) => {
                  setValidationFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Visits</option>
                <option value="pending">Pending Validation</option>
                <option value="validated">Validated</option>
                <option value="rejected">Rejected</option>
              </Select>
              <Text color="gray.500" fontSize="sm">
                {totalCount} visits found
              </Text>
            </HStack>
          </CardBody>
        </Card>

        {/* Table */}
        <Card>
          <CardBody p={0}>
            {loading ? (
              <Center py={12}>
                <Spinner size="xl" color="brand.500" />
              </Center>
            ) : visits.length === 0 ? (
              <Center py={12}>
                <Text color="gray.500">No site visits found</Text>
              </Center>
            ) : (
              <Box overflowX="auto">
                <Table variant="simple">
                  <Thead bg="gray.50">
                    <Tr>
                      <Th w="40px">
                        <Checkbox
                          isChecked={selectedIds.length === visits.length}
                          isIndeterminate={selectedIds.length > 0 && selectedIds.length < visits.length}
                          onChange={(e) => handleSelectAll(e.target.checked)}
                        />
                      </Th>
                      <Th>Site</Th>
                      <Th>Date</Th>
                      <Th>Collector</Th>
                      <Th isNumeric>Records</Th>
                      <Th>Status</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {visits.map((visit) => (
                      <Tr key={visit.id} _hover={{ bg: 'gray.50' }}>
                        <Td>
                          <Checkbox
                            isChecked={selectedIds.includes(visit.id)}
                            onChange={(e) => handleSelect(visit.id, e.target.checked)}
                          />
                        </Td>
                        <Td>
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="500">{visit.site_name}</Text>
                            <Text fontSize="sm" color="gray.500">
                              {visit.site_code}
                            </Text>
                          </VStack>
                        </Td>
                        <Td>{new Date(visit.date).toLocaleDateString()}</Td>
                        <Td>{visit.collector}</Td>
                        <Td isNumeric>
                          <Badge colorScheme="blue">{visit.record_count}</Badge>
                        </Td>
                        <Td>
                          {visit.validated ? (
                            <Badge colorScheme="green">Validated</Badge>
                          ) : visit.rejected ? (
                            <Badge colorScheme="red">Rejected</Badge>
                          ) : (
                            <Badge colorScheme="yellow">Pending</Badge>
                          )}
                        </Td>
                        <Td>
                          <HStack spacing={1}>
                            <IconButton
                              as={RouterLink}
                              to={`/site-visits/${visit.id}`}
                              aria-label="View"
                              icon={<ViewIcon />}
                              size="sm"
                              variant="ghost"
                            />
                            <IconButton
                              as={RouterLink}
                              to={`/site-visits/${visit.id}/edit`}
                              aria-label="Edit"
                              icon={<EditIcon />}
                              size="sm"
                              variant="ghost"
                            />
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

      {/* Reject Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Reject Site Visits</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <Text>
                You are about to reject {selectedIds.length} site visit(s).
              </Text>
              <Textarea
                placeholder="Reason for rejection (optional)"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="red" onClick={handleBulkAction}>
              Reject
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  );
};

export default SiteVisitsPage;
