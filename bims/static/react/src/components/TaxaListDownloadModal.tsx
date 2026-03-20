/**
 * Modal for downloading taxa list with taxon group selection.
 */
import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Select,
  RadioGroup,
  Radio,
  Stack,
  useToast,
  Text,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { DownloadIcon } from '@chakra-ui/icons';
import { apiClient } from '../api/client';

interface TaxonGroup {
  id: number;
  name: string;
}

interface TaxaListDownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedTaxonGroupId?: number;
}

export const TaxaListDownloadModal: React.FC<TaxaListDownloadModalProps> = ({
  isOpen,
  onClose,
  preselectedTaxonGroupId,
}) => {
  const [taxonGroups, setTaxonGroups] = useState<TaxonGroup[]>([]);
  const [selectedTaxonGroupId, setSelectedTaxonGroupId] = useState<string>('');
  const [outputFormat, setOutputFormat] = useState<string>('csv');
  const [loading, setLoading] = useState(false);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const toast = useToast();

  // Load taxon groups on mount
  useEffect(() => {
    const fetchTaxonGroups = async () => {
      setLoadingGroups(true);
      try {
        const response = await apiClient.get('taxon-groups/');
        const groups = response.data?.data || response.data || [];
        setTaxonGroups(groups);

        // Set preselected group if provided
        if (preselectedTaxonGroupId) {
          setSelectedTaxonGroupId(preselectedTaxonGroupId.toString());
        }
      } catch (error) {
        console.error('Failed to load taxon groups:', error);
      } finally {
        setLoadingGroups(false);
      }
    };

    if (isOpen) {
      fetchTaxonGroups();
    }
  }, [isOpen, preselectedTaxonGroupId]);

  const handleDownload = async () => {
    if (!selectedTaxonGroupId) {
      toast({
        title: 'Taxon group required',
        description: 'Please select a taxon group to download.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.post('downloads/taxa-list/', {
        taxon_group_id: parseInt(selectedTaxonGroupId),
        output: outputFormat,
      });

      if (response.data?.data) {
        toast({
          title: 'Download started',
          description: response.data.data.message || 'You will receive an email when the download is ready.',
          status: 'success',
          duration: 5000,
        });
        onClose();
      }
    } catch (error: any) {
      console.error('Download request failed:', error);
      const message = error.response?.data?.errors?.detail || 'Failed to start download';
      toast({
        title: 'Download failed',
        description: message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Download Taxa List</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <Alert status="info" borderRadius="md">
              <AlertIcon />
              <Text fontSize="sm">
                The taxa list will be generated and sent to your email when ready.
              </Text>
            </Alert>

            <FormControl isRequired>
              <FormLabel>Taxon Group</FormLabel>
              <Select
                placeholder={loadingGroups ? 'Loading...' : 'Select taxon group'}
                value={selectedTaxonGroupId}
                onChange={(e) => setSelectedTaxonGroupId(e.target.value)}
                isDisabled={loadingGroups}
              >
                {taxonGroups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel>Output Format</FormLabel>
              <RadioGroup value={outputFormat} onChange={setOutputFormat}>
                <Stack direction="row" spacing={4}>
                  <Radio value="csv">CSV</Radio>
                  <Radio value="xlsx">Excel (XLSX)</Radio>
                </Stack>
              </RadioGroup>
            </FormControl>
          </Stack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button
            colorScheme="brand"
            leftIcon={<DownloadIcon />}
            onClick={handleDownload}
            isLoading={loading}
            loadingText="Starting..."
          >
            Download
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default TaxaListDownloadModal;
