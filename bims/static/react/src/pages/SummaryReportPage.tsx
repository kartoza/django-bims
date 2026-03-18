/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Summary Report generation page.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardBody,
  CardHeader,
  FormControl,
  FormLabel,
  FormHelperText,
  Select,
  Button,
  useToast,
  useColorModeValue,
  SimpleGrid,
  Checkbox,
  CheckboxGroup,
  Divider,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { DownloadIcon, RepeatIcon, ViewIcon } from '@chakra-ui/icons';

interface ReportConfig {
  reportType: string;
  taxonGroup: string;
  boundary: string;
  dateRange: string;
  sections: string[];
}

interface GeneratedReport {
  id: string;
  name: string;
  type: string;
  generatedAt: string;
  status: 'ready' | 'generating' | 'failed';
  downloadUrl?: string;
  size?: string;
}

const SummaryReportPage: React.FC = () => {
  const toast = useToast();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  const [config, setConfig] = useState<ReportConfig>({
    reportType: 'overview',
    taxonGroup: '',
    boundary: '',
    dateRange: 'all',
    sections: ['summary', 'species_list', 'conservation', 'charts'],
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);

  const [reports, setReports] = useState<GeneratedReport[]>([
    {
      id: '1',
      name: 'Fish Module Overview - 2024',
      type: 'Module Summary',
      generatedAt: '2024-01-15T10:30:00Z',
      status: 'ready',
      downloadUrl: '#',
      size: '2.4 MB',
    },
    {
      id: '2',
      name: 'Western Cape Biodiversity Report',
      type: 'Regional Summary',
      generatedAt: '2024-01-14T14:20:00Z',
      status: 'ready',
      downloadUrl: '#',
      size: '5.1 MB',
    },
    {
      id: '3',
      name: 'Conservation Status Analysis',
      type: 'Conservation Report',
      generatedAt: '2024-01-13T09:15:00Z',
      status: 'ready',
      downloadUrl: '#',
      size: '1.8 MB',
    },
  ]);

  const handleSectionChange = (values: string[]) => {
    setConfig((prev) => ({ ...prev, sections: values }));
  };

  const generateReport = async () => {
    setIsGenerating(true);
    setGenerationProgress(0);

    try {
      // Simulate report generation with progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 300));
        setGenerationProgress(i);
      }

      const newReport: GeneratedReport = {
        id: Date.now().toString(),
        name: `${config.reportType === 'overview' ? 'Overview' : 'Custom'} Report - ${new Date().toLocaleDateString()}`,
        type: config.reportType,
        generatedAt: new Date().toISOString(),
        status: 'ready',
        downloadUrl: '#',
        size: '1.2 MB',
      };

      setReports((prev) => [newReport, ...prev]);

      toast({
        title: 'Report generated',
        description: 'Your summary report is ready for download.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Generation failed',
        description: 'Failed to generate report. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsGenerating(false);
      setGenerationProgress(0);
    }
  };

  return (
    <Box h="100%" overflowY="auto">
      {/* Header */}
      <Box bg={headerBg} color="white" py={8}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Heading size="lg">Summary Reports</Heading>
              <Text opacity={0.9}>
                Generate comprehensive biodiversity summary reports
              </Text>
            </VStack>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={8}>
          {/* Report Configuration */}
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Generate New Report</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={6} align="stretch">
                <FormControl>
                  <FormLabel>Report Type</FormLabel>
                  <Select
                    value={config.reportType}
                    onChange={(e) =>
                      setConfig((prev) => ({ ...prev, reportType: e.target.value }))
                    }
                  >
                    <option value="overview">System Overview</option>
                    <option value="module">Module Summary</option>
                    <option value="regional">Regional Report</option>
                    <option value="conservation">Conservation Status</option>
                    <option value="trends">Temporal Trends</option>
                    <option value="custom">Custom Report</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Taxon Group</FormLabel>
                  <Select
                    value={config.taxonGroup}
                    onChange={(e) =>
                      setConfig((prev) => ({ ...prev, taxonGroup: e.target.value }))
                    }
                    placeholder="All groups"
                  >
                    <option value="fish">Fish</option>
                    <option value="invertebrates">Invertebrates</option>
                    <option value="algae">Algae</option>
                    <option value="plants">Plants</option>
                    <option value="odonata">Odonata</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Geographic Boundary</FormLabel>
                  <Select
                    value={config.boundary}
                    onChange={(e) =>
                      setConfig((prev) => ({ ...prev, boundary: e.target.value }))
                    }
                    placeholder="All regions"
                  >
                    <option value="wc">Western Cape</option>
                    <option value="ec">Eastern Cape</option>
                    <option value="kzn">KwaZulu-Natal</option>
                    <option value="gp">Gauteng</option>
                    <option value="lp">Limpopo</option>
                    <option value="mp">Mpumalanga</option>
                    <option value="nw">North West</option>
                    <option value="fs">Free State</option>
                    <option value="nc">Northern Cape</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Date Range</FormLabel>
                  <Select
                    value={config.dateRange}
                    onChange={(e) =>
                      setConfig((prev) => ({ ...prev, dateRange: e.target.value }))
                    }
                  >
                    <option value="all">All Time</option>
                    <option value="year">Past Year</option>
                    <option value="5years">Past 5 Years</option>
                    <option value="10years">Past 10 Years</option>
                    <option value="custom">Custom Range</option>
                  </Select>
                </FormControl>

                <Divider />

                <FormControl>
                  <FormLabel>Report Sections</FormLabel>
                  <CheckboxGroup
                    value={config.sections}
                    onChange={handleSectionChange}
                    colorScheme="brand"
                  >
                    <VStack align="start" spacing={2}>
                      <Checkbox value="summary">Executive Summary</Checkbox>
                      <Checkbox value="species_list">Species List</Checkbox>
                      <Checkbox value="conservation">Conservation Status</Checkbox>
                      <Checkbox value="charts">Charts & Visualizations</Checkbox>
                      <Checkbox value="maps">Distribution Maps</Checkbox>
                      <Checkbox value="trends">Temporal Trends</Checkbox>
                      <Checkbox value="references">Source References</Checkbox>
                    </VStack>
                  </CheckboxGroup>
                </FormControl>

                {isGenerating && (
                  <Box>
                    <Text fontSize="sm" mb={2}>
                      Generating report... {generationProgress}%
                    </Text>
                    <Progress
                      value={generationProgress}
                      colorScheme="brand"
                      borderRadius="full"
                    />
                  </Box>
                )}

                <Button
                  colorScheme="brand"
                  size="lg"
                  leftIcon={<RepeatIcon />}
                  onClick={generateReport}
                  isLoading={isGenerating}
                  loadingText="Generating..."
                >
                  Generate Report
                </Button>
              </VStack>
            </CardBody>
          </Card>

          {/* Quick Stats */}
          <VStack spacing={6} align="stretch">
            <SimpleGrid columns={2} spacing={4}>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel>Total Reports</StatLabel>
                    <StatNumber>{reports.length}</StatNumber>
                    <StatHelpText>Generated</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel>Available</StatLabel>
                    <StatNumber color="green.500">
                      {reports.filter((r) => r.status === 'ready').length}
                    </StatNumber>
                    <StatHelpText>Ready to download</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>

            <Card bg={cardBg}>
              <CardHeader>
                <Heading size="md">Report Templates</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={3} align="stretch">
                  <Alert status="info" borderRadius="md">
                    <AlertIcon />
                    <Text fontSize="sm">
                      Use templates to quickly generate standardized reports
                    </Text>
                  </Alert>

                  <Button variant="outline" justifyContent="start">
                    Annual Biodiversity Summary
                  </Button>
                  <Button variant="outline" justifyContent="start">
                    Module Status Report
                  </Button>
                  <Button variant="outline" justifyContent="start">
                    Conservation Assessment
                  </Button>
                  <Button variant="outline" justifyContent="start">
                    Data Quality Report
                  </Button>
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </SimpleGrid>

        {/* Generated Reports */}
        <Card bg={cardBg} mt={8}>
          <CardHeader>
            <Heading size="md">Generated Reports</Heading>
          </CardHeader>
          <CardBody>
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Report Name</Th>
                  <Th>Type</Th>
                  <Th>Generated</Th>
                  <Th>Size</Th>
                  <Th>Status</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {reports.map((report) => (
                  <Tr key={report.id}>
                    <Td fontWeight="medium">{report.name}</Td>
                    <Td>
                      <Badge colorScheme="purple">{report.type}</Badge>
                    </Td>
                    <Td>{new Date(report.generatedAt).toLocaleDateString()}</Td>
                    <Td>{report.size}</Td>
                    <Td>
                      <Badge
                        colorScheme={
                          report.status === 'ready'
                            ? 'green'
                            : report.status === 'generating'
                              ? 'blue'
                              : 'red'
                        }
                      >
                        {report.status}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <Button
                          size="sm"
                          leftIcon={<ViewIcon />}
                          variant="ghost"
                          isDisabled={report.status !== 'ready'}
                        >
                          View
                        </Button>
                        <Button
                          size="sm"
                          leftIcon={<DownloadIcon />}
                          colorScheme="brand"
                          variant="ghost"
                          isDisabled={report.status !== 'ready'}
                        >
                          Download
                        </Button>
                      </HStack>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </CardBody>
        </Card>
      </Container>
    </Box>
  );
};

export default SummaryReportPage;
