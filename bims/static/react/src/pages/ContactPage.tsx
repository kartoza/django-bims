/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Contact page with form.
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
  Button,
  Input,
  FormControl,
  FormLabel,
  Textarea,
  Select,
  useToast,
  Alert,
  AlertIcon,
  Link,
  SimpleGrid,
  Icon,
} from '@chakra-ui/react';
import { EmailIcon, ExternalLinkIcon } from '@chakra-ui/icons';

const ContactPage: React.FC = () => {
  const toast = useToast();
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    category: '',
    message: '',
  });

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await fetch('/api/contact/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setSubmitted(true);
        toast({
          title: 'Message Sent',
          description: 'We will get back to you soon.',
          status: 'success',
          duration: 5000,
        });
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to send message. Please try again.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const getCsrfToken = (): string => {
    const cookie = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  };

  const categories = [
    { value: 'general', label: 'General Inquiry' },
    { value: 'data', label: 'Data Question' },
    { value: 'technical', label: 'Technical Support' },
    { value: 'partnership', label: 'Partnership' },
    { value: 'feedback', label: 'Feedback' },
  ];

  if (submitted) {
    return (
      <Container maxW="container.md" py={16}>
        <Card>
          <CardBody textAlign="center" py={12}>
            <Icon as={EmailIcon} boxSize={12} color="green.500" mb={4} />
            <Heading size="lg" mb={4}>
              Thank You!
            </Heading>
            <Text color="gray.600" mb={6}>
              Your message has been sent. We will respond as soon as possible.
            </Text>
            <Button
              onClick={() => {
                setSubmitted(false);
                setFormData({
                  name: '',
                  email: '',
                  subject: '',
                  category: '',
                  message: '',
                });
              }}
            >
              Send Another Message
            </Button>
          </CardBody>
        </Card>
      </Container>
    );
  }

  return (
    <Container maxW="container.lg" py={8}>
      <VStack spacing={8} align="stretch">
        <Box textAlign="center">
          <Heading size="xl" mb={2}>
            Contact Us
          </Heading>
          <Text color="gray.600">
            Have questions? We'd love to hear from you.
          </Text>
        </Box>

        <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
          {/* Contact Form */}
          <Card gridColumn={{ md: 'span 2' }}>
            <CardBody>
              <form onSubmit={handleSubmit}>
                <VStack spacing={4} align="stretch">
                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                    <FormControl isRequired>
                      <FormLabel>Name</FormLabel>
                      <Input
                        value={formData.name}
                        onChange={(e) => handleChange('name', e.target.value)}
                        placeholder="Your name"
                      />
                    </FormControl>
                    <FormControl isRequired>
                      <FormLabel>Email</FormLabel>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleChange('email', e.target.value)}
                        placeholder="your@email.com"
                      />
                    </FormControl>
                  </SimpleGrid>

                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                    <FormControl isRequired>
                      <FormLabel>Category</FormLabel>
                      <Select
                        value={formData.category}
                        onChange={(e) => handleChange('category', e.target.value)}
                        placeholder="Select category"
                      >
                        {categories.map((cat) => (
                          <option key={cat.value} value={cat.value}>
                            {cat.label}
                          </option>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl isRequired>
                      <FormLabel>Subject</FormLabel>
                      <Input
                        value={formData.subject}
                        onChange={(e) => handleChange('subject', e.target.value)}
                        placeholder="Message subject"
                      />
                    </FormControl>
                  </SimpleGrid>

                  <FormControl isRequired>
                    <FormLabel>Message</FormLabel>
                    <Textarea
                      value={formData.message}
                      onChange={(e) => handleChange('message', e.target.value)}
                      placeholder="Your message..."
                      rows={6}
                    />
                  </FormControl>

                  <Button
                    type="submit"
                    colorScheme="brand"
                    isLoading={submitting}
                    size="lg"
                  >
                    Send Message
                  </Button>
                </VStack>
              </form>
            </CardBody>
          </Card>

          {/* Contact Info */}
          <VStack spacing={4} align="stretch">
            <Card>
              <CardBody>
                <Heading size="sm" mb={3}>
                  Quick Links
                </Heading>
                <VStack align="stretch" spacing={2}>
                  <Link href="https://github.com/kartoza/django-bims" isExternal color="brand.500">
                    GitHub Repository <ExternalLinkIcon mx={1} />
                  </Link>
                  <Link href="https://github.com/kartoza/django-bims/issues" isExternal color="brand.500">
                    Report an Issue <ExternalLinkIcon mx={1} />
                  </Link>
                  <Link href="https://kartoza.com" isExternal color="brand.500">
                    Kartoza Website <ExternalLinkIcon mx={1} />
                  </Link>
                </VStack>
              </CardBody>
            </Card>

            <Card>
              <CardBody>
                <Heading size="sm" mb={3}>
                  Development Team
                </Heading>
                <Text color="gray.600" fontSize="sm">
                  BIMS is developed and maintained by Kartoza, a South African
                  company specializing in open-source geospatial solutions.
                </Text>
              </CardBody>
            </Card>

            <Alert status="info" rounded="md">
              <AlertIcon />
              <Box fontSize="sm">
                For urgent technical issues, please create an issue on GitHub.
              </Box>
            </Alert>
          </VStack>
        </SimpleGrid>
      </VStack>
    </Container>
  );
};

export default ContactPage;
