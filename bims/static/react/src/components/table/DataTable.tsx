/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * DataTable - Reusable table component with sorting, batch operations, and export
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Checkbox,
  IconButton,
  Button,
  HStack,
  VStack,
  Box,
  Text,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  Badge,
  Tooltip,
  Flex,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  ChevronUpIcon,
  ChevronDownIcon,
  DownloadIcon,
  DeleteIcon,
  CheckIcon,
  CloseIcon,
  SearchIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  TriangleUpIcon,
  TriangleDownIcon,
} from '@chakra-ui/icons';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  width?: string;
  render?: (item: T, index: number) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
}

interface BatchAction {
  key: string;
  label: string;
  icon?: React.ReactElement;
  colorScheme?: string;
  onClick: (selectedIds: (string | number)[]) => void | Promise<void>;
  requiresConfirmation?: boolean;
  confirmMessage?: string;
}

interface ExportOption {
  key: string;
  label: string;
  format: 'csv' | 'excel' | 'pdf' | 'json';
  onClick: () => void | Promise<void>;
}

interface DataTableProps<T extends { id: string | number }> {
  data: T[];
  columns: Column<T>[];

  // Selection
  selectable?: boolean;
  selectedIds?: (string | number)[];
  onSelectionChange?: (selectedIds: (string | number)[]) => void;

  // Sorting
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (column: string, order: 'asc' | 'desc') => void;

  // Pagination
  page?: number;
  pageSize?: number;
  totalCount?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];

  // Batch actions
  batchActions?: BatchAction[];

  // Export
  exportOptions?: ExportOption[];

  // Search
  searchable?: boolean;
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;

  // Loading
  isLoading?: boolean;

  // Empty state
  emptyMessage?: string;

  // Row actions
  rowActions?: (item: T) => React.ReactNode;
}

export function DataTable<T extends { id: string | number }>({
  data,
  columns,
  selectable = false,
  selectedIds = [],
  onSelectionChange,
  sortBy,
  sortOrder = 'asc',
  onSort,
  page = 1,
  pageSize = 20,
  totalCount,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50, 100],
  batchActions = [],
  exportOptions = [],
  searchable = false,
  searchPlaceholder = 'Search...',
  onSearch,
  isLoading = false,
  emptyMessage = 'No data available',
  rowActions,
}: DataTableProps<T>) {
  const [localSearch, setLocalSearch] = useState('');
  const [confirmingAction, setConfirmingAction] = useState<string | null>(null);

  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const headerBg = useColorModeValue('gray.50', 'gray.800');

  const totalPages = totalCount ? Math.ceil(totalCount / pageSize) : 1;
  const allSelected = data.length > 0 && selectedIds.length === data.length;
  const someSelected = selectedIds.length > 0 && selectedIds.length < data.length;

  const handleSelectAll = useCallback(() => {
    if (!onSelectionChange) return;

    if (allSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(data.map((item) => item.id));
    }
  }, [allSelected, data, onSelectionChange]);

  const handleSelectRow = useCallback(
    (id: string | number) => {
      if (!onSelectionChange) return;

      if (selectedIds.includes(id)) {
        onSelectionChange(selectedIds.filter((selectedId) => selectedId !== id));
      } else {
        onSelectionChange([...selectedIds, id]);
      }
    },
    [selectedIds, onSelectionChange]
  );

  const handleSort = useCallback(
    (column: string) => {
      if (!onSort) return;

      const newOrder =
        sortBy === column && sortOrder === 'asc' ? 'desc' : 'asc';
      onSort(column, newOrder);
    },
    [sortBy, sortOrder, onSort]
  );

  const handleSearch = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setLocalSearch(value);
      onSearch?.(value);
    },
    [onSearch]
  );

  const handleBatchAction = useCallback(
    async (action: BatchAction) => {
      if (action.requiresConfirmation) {
        setConfirmingAction(action.key);
        return;
      }
      await action.onClick(selectedIds);
    },
    [selectedIds]
  );

  const confirmBatchAction = useCallback(
    async (action: BatchAction) => {
      await action.onClick(selectedIds);
      setConfirmingAction(null);
    },
    [selectedIds]
  );

  const SortIcon = ({ column }: { column: string }) => {
    if (sortBy !== column) {
      return null;
    }
    return sortOrder === 'asc' ? (
      <TriangleUpIcon boxSize={3} ml={1} />
    ) : (
      <TriangleDownIcon boxSize={3} ml={1} />
    );
  };

  return (
    <VStack spacing={4} align="stretch" w="100%">
      {/* Toolbar */}
      <Flex
        direction={{ base: 'column', md: 'row' }}
        justify="space-between"
        align={{ base: 'stretch', md: 'center' }}
        gap={4}
      >
        {/* Search */}
        {searchable && (
          <InputGroup maxW={{ base: '100%', md: '300px' }}>
            <InputLeftElement pointerEvents="none">
              <SearchIcon color="gray.400" />
            </InputLeftElement>
            <Input
              placeholder={searchPlaceholder}
              value={localSearch}
              onChange={handleSearch}
            />
          </InputGroup>
        )}

        <HStack spacing={2} flexWrap="wrap">
          {/* Batch Actions */}
          {selectable && selectedIds.length > 0 && (
            <>
              <Badge colorScheme="blue" fontSize="sm" px={2} py={1}>
                {selectedIds.length} selected
              </Badge>
              {batchActions.map((action) => (
                <React.Fragment key={action.key}>
                  {confirmingAction === action.key ? (
                    <HStack>
                      <Text fontSize="sm" color="red.500">
                        {action.confirmMessage || 'Confirm?'}
                      </Text>
                      <IconButton
                        aria-label="Confirm"
                        icon={<CheckIcon />}
                        size="sm"
                        colorScheme="green"
                        onClick={() => confirmBatchAction(action)}
                      />
                      <IconButton
                        aria-label="Cancel"
                        icon={<CloseIcon />}
                        size="sm"
                        variant="ghost"
                        onClick={() => setConfirmingAction(null)}
                      />
                    </HStack>
                  ) : (
                    <Button
                      size="sm"
                      leftIcon={action.icon}
                      colorScheme={action.colorScheme}
                      variant="outline"
                      onClick={() => handleBatchAction(action)}
                    >
                      {action.label}
                    </Button>
                  )}
                </React.Fragment>
              ))}
            </>
          )}

          {/* Export Options */}
          {exportOptions.length > 0 && (
            <Menu>
              <MenuButton
                as={Button}
                size="sm"
                leftIcon={<DownloadIcon />}
                variant="outline"
              >
                Export
              </MenuButton>
              <MenuList>
                {exportOptions.map((option) => (
                  <MenuItem key={option.key} onClick={option.onClick}>
                    {option.label}
                  </MenuItem>
                ))}
              </MenuList>
            </Menu>
          )}
        </HStack>
      </Flex>

      {/* Table */}
      <Box
        overflowX="auto"
        borderWidth={1}
        borderColor={borderColor}
        borderRadius="md"
      >
        <Table variant="simple" size="sm">
          <Thead bg={headerBg}>
            <Tr>
              {selectable && (
                <Th w="40px" px={2}>
                  <Checkbox
                    isChecked={allSelected}
                    isIndeterminate={someSelected}
                    onChange={handleSelectAll}
                  />
                </Th>
              )}
              {columns.map((column) => (
                <Th
                  key={column.key}
                  width={column.width}
                  textAlign={column.align || 'left'}
                  cursor={column.sortable ? 'pointer' : 'default'}
                  onClick={column.sortable ? () => handleSort(column.key) : undefined}
                  _hover={column.sortable ? { bg: hoverBg } : undefined}
                  userSelect="none"
                >
                  <HStack spacing={1} justify={column.align === 'right' ? 'flex-end' : 'flex-start'}>
                    <Text>{column.header}</Text>
                    {column.sortable && <SortIcon column={column.key} />}
                  </HStack>
                </Th>
              ))}
              {rowActions && <Th w="100px" textAlign="right">Actions</Th>}
            </Tr>
          </Thead>
          <Tbody>
            {data.length === 0 ? (
              <Tr>
                <Td
                  colSpan={columns.length + (selectable ? 1 : 0) + (rowActions ? 1 : 0)}
                  textAlign="center"
                  py={8}
                >
                  <Text color="gray.500">{emptyMessage}</Text>
                </Td>
              </Tr>
            ) : (
              data.map((item, index) => (
                <Tr
                  key={item.id}
                  _hover={{ bg: hoverBg }}
                  bg={selectedIds.includes(item.id) ? 'blue.50' : undefined}
                >
                  {selectable && (
                    <Td px={2}>
                      <Checkbox
                        isChecked={selectedIds.includes(item.id)}
                        onChange={() => handleSelectRow(item.id)}
                      />
                    </Td>
                  )}
                  {columns.map((column) => (
                    <Td key={column.key} textAlign={column.align || 'left'}>
                      {column.render
                        ? column.render(item, index)
                        : (item as Record<string, unknown>)[column.key] as React.ReactNode}
                    </Td>
                  ))}
                  {rowActions && (
                    <Td textAlign="right">{rowActions(item)}</Td>
                  )}
                </Tr>
              ))
            )}
          </Tbody>
        </Table>
      </Box>

      {/* Pagination */}
      {totalCount !== undefined && totalCount > 0 && (
        <Flex
          direction={{ base: 'column', md: 'row' }}
          justify="space-between"
          align="center"
          gap={4}
        >
          <HStack spacing={2}>
            <Text fontSize="sm" color="gray.500">
              Showing {(page - 1) * pageSize + 1} to{' '}
              {Math.min(page * pageSize, totalCount)} of {totalCount} results
            </Text>
          </HStack>

          <HStack spacing={4}>
            <HStack spacing={2}>
              <Text fontSize="sm" color="gray.500">
                Per page:
              </Text>
              <Select
                size="sm"
                value={pageSize}
                onChange={(e) => onPageSizeChange?.(Number(e.target.value))}
                w="80px"
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </Select>
            </HStack>

            <HStack spacing={1}>
              <IconButton
                aria-label="Previous page"
                icon={<ChevronLeftIcon />}
                size="sm"
                variant="ghost"
                isDisabled={page <= 1}
                onClick={() => onPageChange?.(page - 1)}
              />
              <Text fontSize="sm" color="gray.600" minW="80px" textAlign="center">
                Page {page} of {totalPages}
              </Text>
              <IconButton
                aria-label="Next page"
                icon={<ChevronRightIcon />}
                size="sm"
                variant="ghost"
                isDisabled={page >= totalPages}
                onClick={() => onPageChange?.(page + 1)}
              />
            </HStack>
          </HStack>
        </Flex>
      )}
    </VStack>
  );
}

export default DataTable;
