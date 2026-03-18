/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Backups Management Page - Admin page for managing database backups
 * Allows superusers to browse and download backup files.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  Heading,
  Text,
  Card,
  CardHeader,
  CardBody,
  Skeleton,
  Button,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  useColorModeValue,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Input,
  InputGroup,
  InputLeftElement,
  Icon,
  Alert,
  AlertIcon,
  useToast,
  IconButton,
  Collapse,
  Tooltip,
} from '@chakra-ui/react';
import {
  ChevronRightIcon,
  DownloadIcon,
  SearchIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';

// File/folder icons
const FolderIcon = () => (
  <Icon viewBox="0 0 24 24" color="yellow.500">
    <path
      fill="currentColor"
      d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"
    />
  </Icon>
);

const FileIcon = () => (
  <Icon viewBox="0 0 24 24" color="gray.500">
    <path
      fill="currentColor"
      d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"
    />
  </Icon>
);

interface BackupFile {
  name: string;
  path: string;
  type: 'file' | 'folder';
  size?: string;
  modified?: string;
  children?: BackupFile[];
}

interface FolderRowProps {
  item: BackupFile;
  depth: number;
  searchQuery: string;
  onDownload: (path: string, name: string) => void;
}

const FolderRow: React.FC<FolderRowProps> = ({ item, depth, searchQuery, onDownload }) => {
  const [isOpen, setIsOpen] = useState(false);
  const bgHover = useColorModeValue('gray.50', 'gray.700');

  // Auto-expand if search matches children
  useEffect(() => {
    if (searchQuery && item.type === 'folder' && item.children) {
      const hasMatchingChild = item.children.some(child =>
        child.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
      if (hasMatchingChild) {
        setIsOpen(true);
      }
    }
  }, [searchQuery, item]);

  // Filter by search
  const matchesSearch = !searchQuery ||
    item.name.toLowerCase().includes(searchQuery.toLowerCase());

  if (!matchesSearch && item.type === 'file') {
    return null;
  }

  return (
    <>
      <Tr _hover={{ bg: bgHover }}>
        <Td>
          <HStack spacing={2} pl={depth * 4}>
            {item.type === 'folder' ? (
              <>
                <IconButton
                  aria-label={isOpen ? 'Collapse' : 'Expand'}
                  icon={isOpen ? <ChevronDownIcon /> : <ChevronRightIcon />}
                  size="xs"
                  variant="ghost"
                  onClick={() => setIsOpen(!isOpen)}
                />
                <FolderIcon />
              </>
            ) : (
              <>
                <Box w="24px" />
                <FileIcon />
              </>
            )}
            <Text
              fontWeight={item.type === 'folder' ? 'medium' : 'normal'}
              cursor={item.type === 'folder' ? 'pointer' : 'default'}
              onClick={() => item.type === 'folder' && setIsOpen(!isOpen)}
            >
              {item.name}
            </Text>
          </HStack>
        </Td>
        <Td>
          <Badge colorScheme={item.type === 'folder' ? 'blue' : 'gray'}>
            {item.type}
          </Badge>
        </Td>
        <Td>{item.size || '-'}</Td>
        <Td>{item.modified || '-'}</Td>
        <Td>
          {item.type === 'file' && (
            <Tooltip label="Download backup file">
              <IconButton
                aria-label="Download"
                icon={<DownloadIcon />}
                size="sm"
                colorScheme="blue"
                variant="ghost"
                onClick={() => onDownload(item.path, item.name)}
              />
            </Tooltip>
          )}
        </Td>
      </Tr>
      {item.type === 'folder' && item.children && (
        <Tr>
          <Td colSpan={5} p={0} border="none">
            <Collapse in={isOpen} animateOpacity>
              <Table size="sm" variant="simple">
                <Tbody>
                  {item.children.map((child, index) => (
                    <FolderRow
                      key={`${child.path}-${index}`}
                      item={child}
                      depth={depth + 1}
                      searchQuery={searchQuery}
                      onDownload={onDownload}
                    />
                  ))}
                </Tbody>
              </Table>
            </Collapse>
          </Td>
        </Tr>
      )}
    </>
  );
};

const BackupsManagementPage: React.FC = () => {
  const { user } = useAuth();
  const toast = useToast();

  const [backups, setBackups] = useState<BackupFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDownloading, setIsDownloading] = useState(false);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  // Fetch backup list
  const fetchBackups = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch from the existing backups management endpoint
      const response = await fetch('/backups-management/?format=json');

      if (!response.ok) {
        if (response.status === 403) {
          setError('You do not have permission to access backups. Superuser access required.');
        } else {
          throw new Error('Failed to fetch backups');
        }
        return;
      }

      const data = await response.json();

      // Parse the backup tree structure
      if (data.all_backups) {
        setBackups(parseBackupTree(data.all_backups));
      } else {
        setBackups([]);
      }
    } catch (err) {
      console.error('Failed to load backups:', err);
      setError('Failed to load backup files. Make sure you have superuser access.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBackups();
  }, [fetchBackups]);

  // Parse the backup tree from the legacy format
  const parseBackupTree = (tree: any): BackupFile[] => {
    if (!tree) return [];

    const result: BackupFile[] = [];

    Object.entries(tree).forEach(([key, value]: [string, any]) => {
      if (typeof value === 'object' && value !== null) {
        if (value.type === 'file') {
          result.push({
            name: key,
            path: value.path || key,
            type: 'file',
            size: value.size,
            modified: value.modified,
          });
        } else {
          // It's a folder
          result.push({
            name: key,
            path: value.path || key,
            type: 'folder',
            children: parseBackupTree(value),
          });
        }
      }
    });

    // Sort: folders first, then files, both alphabetically
    return result.sort((a, b) => {
      if (a.type !== b.type) {
        return a.type === 'folder' ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });
  };

  // Handle download
  const handleDownload = async (filePath: string, fileName: string) => {
    setIsDownloading(true);

    try {
      // Create a form submission to trigger the download
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/backups-management/';

      // Add CSRF token
      const csrfInput = document.createElement('input');
      csrfInput.type = 'hidden';
      csrfInput.name = 'csrfmiddlewaretoken';
      csrfInput.value = document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value || '';
      form.appendChild(csrfInput);

      // Add file path
      const fileInput = document.createElement('input');
      fileInput.type = 'hidden';
      fileInput.name = 'selected-file';
      fileInput.value = filePath;
      form.appendChild(fileInput);

      document.body.appendChild(form);
      form.submit();
      document.body.removeChild(form);

      toast({
        title: 'Download started',
        description: `Downloading ${fileName}`,
        status: 'success',
        duration: 3000,
      });
    } catch (err) {
      toast({
        title: 'Download failed',
        description: 'Failed to download backup file',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsDownloading(false);
    }
  };

  // Check if user is superuser
  if (!user?.isSuperuser) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
        <Container maxW="7xl">
          <Alert status="error">
            <AlertIcon />
            You do not have permission to access this page. Superuser access required.
          </Alert>
        </Container>
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box bg={bgColor} minH="calc(100vh - 140px)" p={6}>
        <Container maxW="7xl">
          <VStack spacing={6} align="stretch">
            <Skeleton height="40px" width="300px" />
            <Skeleton height="400px" />
          </VStack>
        </Container>
      </Box>
    );
  }

  return (
    <Box bg={bgColor} minH="calc(100vh - 140px)" p={6} overflowY="auto">
      <Container maxW="7xl">
        <VStack spacing={6} align="stretch">
          {/* Breadcrumb */}
          <Breadcrumb separator={<ChevronRightIcon color="gray.500" />}>
            <BreadcrumbItem>
              <BreadcrumbLink as={RouterLink} to="/">Home</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem isCurrentPage>
              <BreadcrumbLink>Backups Management</BreadcrumbLink>
            </BreadcrumbItem>
          </Breadcrumb>

          {/* Header */}
          <HStack justify="space-between" align="flex-start">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Backups Management</Heading>
              <Text color="gray.600">
                Browse and download database backup files
              </Text>
            </VStack>
            <Button
              colorScheme="blue"
              variant="outline"
              onClick={fetchBackups}
              isLoading={isLoading}
            >
              Refresh
            </Button>
          </HStack>

          {/* Error Alert */}
          {error && (
            <Alert status="error">
              <AlertIcon />
              {error}
            </Alert>
          )}

          {/* Search */}
          <Card bg={cardBg}>
            <CardBody>
              <InputGroup>
                <InputLeftElement pointerEvents="none">
                  <SearchIcon color="gray.400" />
                </InputLeftElement>
                <Input
                  placeholder="Search backup files..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </InputGroup>
            </CardBody>
          </Card>

          {/* Backups Table */}
          <Card bg={cardBg}>
            <CardHeader>
              <HStack justify="space-between">
                <Heading size="md">Backup Files</Heading>
                <Badge colorScheme="blue">
                  {backups.length} items
                </Badge>
              </HStack>
            </CardHeader>
            <CardBody>
              {backups.length > 0 ? (
                <Box overflowX="auto">
                  <Table size="sm" variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Name</Th>
                        <Th>Type</Th>
                        <Th>Size</Th>
                        <Th>Modified</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {backups.map((item, index) => (
                        <FolderRow
                          key={`${item.path}-${index}`}
                          item={item}
                          depth={0}
                          searchQuery={searchQuery}
                          onDownload={handleDownload}
                        />
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              ) : (
                <Text color="gray.500" textAlign="center" py={8}>
                  No backup files found in /home/web/backups
                </Text>
              )}
            </CardBody>
          </Card>

          {/* Info Card */}
          <Card bg={cardBg}>
            <CardBody>
              <Alert status="info" variant="subtle">
                <AlertIcon />
                <VStack align="start" spacing={1}>
                  <Text fontWeight="medium">Backup Directory</Text>
                  <Text fontSize="sm">
                    Backups are stored in <code>/home/web/backups</code>.
                    Click on a file to download it. Folders can be expanded to view their contents.
                  </Text>
                </VStack>
              </Alert>
            </CardBody>
          </Card>
        </VStack>
      </Container>
    </Box>
  );
};

export default BackupsManagementPage;
