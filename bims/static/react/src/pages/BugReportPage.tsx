/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Bug Report / Issue Submission page.
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
  Input,
  Textarea,
  Select,
  Button,
  useToast,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Link,
  Icon,
  Divider,
  Badge,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import { CheckCircleIcon, WarningIcon, InfoIcon } from '@chakra-ui/icons';

const BugReportPage: React.FC = () => {
  const toast = useToast();
  const headerBg = useColorModeValue('brand.500', 'brand.600');
  const cardBg = useColorModeValue('white', 'gray.700');

  const [formData, setFormData] = useState({
    title: '',
    category: '',
    severity: '',
    description: '',
    stepsToReproduce: '',
    expectedBehavior: '',
    actualBehavior: '',
    browserInfo: navigator.userAgent,
    url: window.location.href,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // In a real implementation, this would submit to the API
      // For now, simulate submission
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setSubmitted(true);
      toast({
        title: 'Bug report submitted',
        description: 'Thank you for your feedback. We will investigate this issue.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Submission failed',
        description: 'There was an error submitting your report. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <Box>
        <Box bg={headerBg} color="white" py={12}>
          <Container maxW="container.md">
            <VStack spacing={4} textAlign="center">
              <Heading size="xl">Bug Report Submitted</Heading>
            </VStack>
          </Container>
        </Box>

        <Container maxW="container.md" py={8}>
          <Alert
            status="success"
            variant="subtle"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            textAlign="center"
            height="300px"
            borderRadius="md"
          >
            <AlertIcon boxSize="40px" mr={0} />
            <AlertTitle mt={4} mb={1} fontSize="lg">
              Thank you for your report!
            </AlertTitle>
            <AlertDescription maxWidth="sm">
              We have received your bug report and will investigate the issue. You may
              receive a follow-up email if we need additional information.
            </AlertDescription>
            <Button
              mt={6}
              colorScheme="brand"
              onClick={() => {
                setSubmitted(false);
                setFormData({
                  title: '',
                  category: '',
                  severity: '',
                  description: '',
                  stepsToReproduce: '',
                  expectedBehavior: '',
                  actualBehavior: '',
                  browserInfo: navigator.userAgent,
                  url: window.location.href,
                });
              }}
            >
              Submit Another Report
            </Button>
          </Alert>
        </Container>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box bg={headerBg} color="white" py={12}>
        <Container maxW="container.xl">
          <VStack spacing={4} textAlign="center">
            <Heading size="xl">Report a Bug</Heading>
            <Text fontSize="lg" maxW="2xl" opacity={0.9}>
              Help us improve BIMS by reporting issues you encounter
            </Text>
          </VStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <HStack align="start" spacing={8} flexWrap={{ base: 'wrap', lg: 'nowrap' }}>
          {/* Bug Report Form */}
          <Card flex="2" bg={cardBg} minW={{ base: '100%', lg: 'auto' }}>
            <CardHeader>
              <Heading size="md">Bug Report Form</Heading>
            </CardHeader>
            <CardBody>
              <form onSubmit={handleSubmit}>
                <VStack spacing={6} align="stretch">
                  <FormControl isRequired>
                    <FormLabel>Issue Title</FormLabel>
                    <Input
                      name="title"
                      value={formData.title}
                      onChange={handleChange}
                      placeholder="Brief description of the issue"
                    />
                  </FormControl>

                  <HStack spacing={4} flexWrap={{ base: 'wrap', md: 'nowrap' }}>
                    <FormControl isRequired flex="1" minW={{ base: '100%', md: 'auto' }}>
                      <FormLabel>Category</FormLabel>
                      <Select
                        name="category"
                        value={formData.category}
                        onChange={handleChange}
                        placeholder="Select category"
                      >
                        <option value="map">Map/Visualization</option>
                        <option value="search">Search/Filters</option>
                        <option value="data">Data Entry</option>
                        <option value="download">Downloads/Export</option>
                        <option value="upload">File Upload</option>
                        <option value="account">Account/Login</option>
                        <option value="performance">Performance</option>
                        <option value="ui">User Interface</option>
                        <option value="other">Other</option>
                      </Select>
                    </FormControl>

                    <FormControl isRequired flex="1" minW={{ base: '100%', md: 'auto' }}>
                      <FormLabel>Severity</FormLabel>
                      <Select
                        name="severity"
                        value={formData.severity}
                        onChange={handleChange}
                        placeholder="Select severity"
                      >
                        <option value="critical">Critical - Cannot use system</option>
                        <option value="high">High - Major feature broken</option>
                        <option value="medium">Medium - Feature partially working</option>
                        <option value="low">Low - Minor inconvenience</option>
                      </Select>
                    </FormControl>
                  </HStack>

                  <FormControl isRequired>
                    <FormLabel>Description</FormLabel>
                    <Textarea
                      name="description"
                      value={formData.description}
                      onChange={handleChange}
                      placeholder="Describe the issue in detail"
                      rows={4}
                    />
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel>Steps to Reproduce</FormLabel>
                    <Textarea
                      name="stepsToReproduce"
                      value={formData.stepsToReproduce}
                      onChange={handleChange}
                      placeholder="1. Go to...&#10;2. Click on...&#10;3. Observe..."
                      rows={4}
                    />
                    <FormHelperText>
                      List the exact steps to reproduce the bug
                    </FormHelperText>
                  </FormControl>

                  <HStack spacing={4} flexWrap={{ base: 'wrap', md: 'nowrap' }}>
                    <FormControl flex="1" minW={{ base: '100%', md: 'auto' }}>
                      <FormLabel>Expected Behavior</FormLabel>
                      <Textarea
                        name="expectedBehavior"
                        value={formData.expectedBehavior}
                        onChange={handleChange}
                        placeholder="What should happen"
                        rows={3}
                      />
                    </FormControl>

                    <FormControl flex="1" minW={{ base: '100%', md: 'auto' }}>
                      <FormLabel>Actual Behavior</FormLabel>
                      <Textarea
                        name="actualBehavior"
                        value={formData.actualBehavior}
                        onChange={handleChange}
                        placeholder="What actually happened"
                        rows={3}
                      />
                    </FormControl>
                  </HStack>

                  <Divider />

                  <Alert status="info" borderRadius="md">
                    <AlertIcon />
                    <Box>
                      <Text fontSize="sm" fontWeight="medium">
                        System Information (auto-collected)
                      </Text>
                      <Text fontSize="xs" color="gray.600">
                        Browser: {navigator.userAgent.substring(0, 50)}...
                      </Text>
                    </Box>
                  </Alert>

                  <Button
                    type="submit"
                    colorScheme="brand"
                    size="lg"
                    isLoading={isSubmitting}
                    loadingText="Submitting..."
                  >
                    Submit Bug Report
                  </Button>
                </VStack>
              </form>
            </CardBody>
          </Card>

          {/* Tips Sidebar */}
          <Card flex="1" bg={cardBg} minW={{ base: '100%', lg: '300px' }}>
            <CardHeader>
              <Heading size="md">Tips for Good Bug Reports</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Box>
                  <HStack mb={2}>
                    <Icon as={CheckCircleIcon} color="green.500" />
                    <Text fontWeight="medium">Be Specific</Text>
                  </HStack>
                  <Text fontSize="sm" color="gray.600">
                    Include exact error messages, URLs, and data you were working with.
                  </Text>
                </Box>

                <Box>
                  <HStack mb={2}>
                    <Icon as={CheckCircleIcon} color="green.500" />
                    <Text fontWeight="medium">Steps Matter</Text>
                  </HStack>
                  <Text fontSize="sm" color="gray.600">
                    Clear reproduction steps help us fix bugs faster.
                  </Text>
                </Box>

                <Box>
                  <HStack mb={2}>
                    <Icon as={CheckCircleIcon} color="green.500" />
                    <Text fontWeight="medium">Screenshots Help</Text>
                  </HStack>
                  <Text fontSize="sm" color="gray.600">
                    If possible, include screenshots or screen recordings.
                  </Text>
                </Box>

                <Divider />

                <Box>
                  <HStack mb={2}>
                    <Icon as={InfoIcon} color="blue.500" />
                    <Text fontWeight="medium">GitHub Issues</Text>
                  </HStack>
                  <Text fontSize="sm" color="gray.600">
                    For technical issues, you can also submit issues directly on{' '}
                    <Link
                      href="https://github.com/kartoza/django-bims/issues"
                      isExternal
                      color="brand.500"
                    >
                      GitHub
                    </Link>
                    .
                  </Text>
                </Box>

                <Box>
                  <HStack mb={2}>
                    <Icon as={WarningIcon} color="orange.500" />
                    <Text fontWeight="medium">Security Issues</Text>
                  </HStack>
                  <Text fontSize="sm" color="gray.600">
                    For security vulnerabilities, please email{' '}
                    <Link href="mailto:security@kartoza.com" color="brand.500">
                      security@kartoza.com
                    </Link>{' '}
                    instead of submitting here.
                  </Text>
                </Box>
              </VStack>
            </CardBody>
          </Card>
        </HStack>
      </Container>
    </Box>
  );
};

export default BugReportPage;
