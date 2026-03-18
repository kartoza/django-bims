/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Source References listing and management page.
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
  Link,
  Flex,
  Spacer,
} from '@chakra-ui/react';
import {
  SearchIcon,
  AddIcon,
  ExternalLinkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ViewIcon,
  EditIcon,
  DeleteIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink } from 'react-router-dom';
import { api } from '../api/client';

interface SourceReference {
  id: number;
  title: string;
  authors: string;
  year: number;
  source_type: string;
  doi?: string;
  url?: string;
  record_count: number;
}

interface PaginatedResponse {
  success: boolean;
  data: SourceReference[];
  meta: {
    count: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

const SourceReferencesPage: React.FC = () => {
  const [references, setReferences] = useState<SourceReference[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const toast = useToast();

  useEffect(() => {
    fetchReferences();
  }, [page, searchTerm, sourceType]);

  const fetchReferences = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        page,
        page_size: 20,
      };
      if (searchTerm) params.search = searchTerm;
      if (sourceType) params.source_type = sourceType;

      const response = await api.getList<SourceReference>('source-references/', params);
      setReferences(response.data || []);
      setTotalPages(response.meta?.total_pages || 1);
      setTotalCount(response.meta?.count || 0);
    } catch (error) {
      toast({
        title: 'Error loading references',
        description: 'Could not fetch source references',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const sourceTypes = [
    { value: '', label: 'All Types' },
    { value: 'peer-reviewed', label: 'Peer Reviewed' },
    { value: 'published-report', label: 'Published Report' },
    { value: 'thesis', label: 'Thesis' },
    { value: 'database', label: 'Database' },
    { value: 'unpublished', label: 'Unpublished Data' },
  ];

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Flex align="center">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Source References</Heading>
            <Text color="gray.600">
              Browse and manage bibliographic references for biodiversity records
            </Text>
          </VStack>
          <Spacer />
          <Button
            as={RouterLink}
            to="/add/source-reference"
            colorScheme="brand"
            leftIcon={<AddIcon />}
          >
            Add Reference
          </Button>
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
                  placeholder="Search by title, author, or DOI..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setPage(1);
                  }}
                />
              </InputGroup>
              <Select
                maxW="200px"
                value={sourceType}
                onChange={(e) => {
                  setSourceType(e.target.value);
                  setPage(1);
                }}
              >
                {sourceTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </Select>
              <Text color="gray.500" fontSize="sm">
                {totalCount} references found
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
            ) : references.length === 0 ? (
              <Center py={12}>
                <VStack>
                  <Text color="gray.500">No references found</Text>
                  <Button as={RouterLink} to="/add/source-reference" size="sm">
                    Add your first reference
                  </Button>
                </VStack>
              </Center>
            ) : (
              <Box overflowX="auto">
                <Table variant="simple">
                  <Thead bg="gray.50">
                    <Tr>
                      <Th>Title</Th>
                      <Th>Authors</Th>
                      <Th>Year</Th>
                      <Th>Type</Th>
                      <Th isNumeric>Records</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {references.map((ref) => (
                      <Tr key={ref.id} _hover={{ bg: 'gray.50' }}>
                        <Td maxW="400px">
                          <Text noOfLines={2} fontWeight="500">
                            {ref.title}
                          </Text>
                          {ref.doi && (
                            <Link
                              href={`https://doi.org/${ref.doi}`}
                              isExternal
                              fontSize="sm"
                              color="brand.500"
                            >
                              DOI: {ref.doi} <ExternalLinkIcon mx={1} boxSize={3} />
                            </Link>
                          )}
                        </Td>
                        <Td maxW="200px">
                          <Text noOfLines={1}>{ref.authors}</Text>
                        </Td>
                        <Td>{ref.year}</Td>
                        <Td>
                          <Badge colorScheme="blue" variant="subtle">
                            {ref.source_type}
                          </Badge>
                        </Td>
                        <Td isNumeric>
                          <Badge colorScheme="green">{ref.record_count}</Badge>
                        </Td>
                        <Td>
                          <HStack spacing={1}>
                            <IconButton
                              as={RouterLink}
                              to={`/source-references/${ref.id}`}
                              aria-label="View"
                              icon={<ViewIcon />}
                              size="sm"
                              variant="ghost"
                            />
                            <IconButton
                              as={RouterLink}
                              to={`/source-references/${ref.id}/edit`}
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
    </Container>
  );
};

export default SourceReferencesPage;
