/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Registration page for BIMS React frontend.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  FormErrorMessage,
  FormHelperText,
  Heading,
  Input,
  InputGroup,
  InputRightElement,
  IconButton,
  Link,
  Stack,
  Text,
  Alert,
  AlertIcon,
  VStack,
  HStack,
  Divider,
  SimpleGrid,
  useColorModeValue,
} from '@chakra-ui/react';
import { ViewIcon, ViewOffIcon, CheckIcon, CloseIcon } from '@chakra-ui/icons';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';

const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    firstName: '',
    lastName: '',
    password1: '',
    password2: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const { register, isLoading, error, isAuthenticated, clearError } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Clear errors on mount
  useEffect(() => {
    clearError();
  }, [clearError]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    }

    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email address';
    }

    if (!formData.password1) {
      errors.password1 = 'Password is required';
    } else if (formData.password1.length < 8) {
      errors.password1 = 'Password must be at least 8 characters';
    }

    if (!formData.password2) {
      errors.password2 = 'Please confirm your password';
    } else if (formData.password1 !== formData.password2) {
      errors.password2 = 'Passwords do not match';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const success = await register(formData);
    if (success) {
      navigate('/', { replace: true });
    }
  };

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Password strength indicators
  const passwordChecks = {
    length: formData.password1.length >= 8,
    hasNumber: /\d/.test(formData.password1),
    hasLetter: /[a-zA-Z]/.test(formData.password1),
    match: formData.password1 === formData.password2 && formData.password2 !== '',
  };

  return (
    <Box bg="bg.light" minH="calc(100vh - 120px)" py={12}>
      <Container maxW="lg">
        <Box
          bg={bgColor}
          p={8}
          borderRadius="2xl"
          boxShadow="lg"
          borderWidth="1px"
          borderColor={borderColor}
        >
          <VStack spacing={6} align="stretch">
            <VStack spacing={2} textAlign="center">
              <Heading size="lg" color="gray.800">
                Create Account
              </Heading>
              <Text color="gray.600">
                Join BIMS to contribute to biodiversity monitoring
              </Text>
            </VStack>

            {error && (
              <Alert status="error" borderRadius="lg">
                <AlertIcon />
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <Stack spacing={4}>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <FormControl isInvalid={!!fieldErrors.firstName}>
                    <FormLabel>First Name</FormLabel>
                    <Input
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleChange}
                      placeholder="John"
                      size="lg"
                    />
                  </FormControl>

                  <FormControl isInvalid={!!fieldErrors.lastName}>
                    <FormLabel>Last Name</FormLabel>
                    <Input
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleChange}
                      placeholder="Doe"
                      size="lg"
                    />
                  </FormControl>
                </SimpleGrid>

                <FormControl isRequired isInvalid={!!fieldErrors.username}>
                  <FormLabel>Username</FormLabel>
                  <Input
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    placeholder="Choose a username"
                    size="lg"
                    autoComplete="username"
                  />
                  <FormErrorMessage>{fieldErrors.username}</FormErrorMessage>
                </FormControl>

                <FormControl isRequired isInvalid={!!fieldErrors.email}>
                  <FormLabel>Email Address</FormLabel>
                  <Input
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="you@example.com"
                    size="lg"
                    autoComplete="email"
                  />
                  <FormErrorMessage>{fieldErrors.email}</FormErrorMessage>
                </FormControl>

                <FormControl isRequired isInvalid={!!fieldErrors.password1}>
                  <FormLabel>Password</FormLabel>
                  <InputGroup size="lg">
                    <Input
                      name="password1"
                      type={showPassword ? 'text' : 'password'}
                      value={formData.password1}
                      onChange={handleChange}
                      placeholder="Create a strong password"
                      autoComplete="new-password"
                    />
                    <InputRightElement>
                      <IconButton
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                        icon={showPassword ? <ViewOffIcon /> : <ViewIcon />}
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowPassword(!showPassword)}
                      />
                    </InputRightElement>
                  </InputGroup>
                  <FormErrorMessage>{fieldErrors.password1}</FormErrorMessage>
                  {formData.password1 && (
                    <VStack align="start" mt={2} spacing={1}>
                      <PasswordCheck
                        passed={passwordChecks.length}
                        label="At least 8 characters"
                      />
                      <PasswordCheck
                        passed={passwordChecks.hasLetter}
                        label="Contains letters"
                      />
                      <PasswordCheck
                        passed={passwordChecks.hasNumber}
                        label="Contains numbers"
                      />
                    </VStack>
                  )}
                </FormControl>

                <FormControl isRequired isInvalid={!!fieldErrors.password2}>
                  <FormLabel>Confirm Password</FormLabel>
                  <InputGroup size="lg">
                    <Input
                      name="password2"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={formData.password2}
                      onChange={handleChange}
                      placeholder="Confirm your password"
                      autoComplete="new-password"
                    />
                    <InputRightElement>
                      <IconButton
                        aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                        icon={showConfirmPassword ? <ViewOffIcon /> : <ViewIcon />}
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      />
                    </InputRightElement>
                  </InputGroup>
                  <FormErrorMessage>{fieldErrors.password2}</FormErrorMessage>
                  {formData.password2 && (
                    <PasswordCheck
                      passed={passwordChecks.match}
                      label="Passwords match"
                    />
                  )}
                </FormControl>

                <Button
                  type="submit"
                  size="lg"
                  colorScheme="brand"
                  isLoading={isLoading}
                  loadingText="Creating account..."
                  width="100%"
                  mt={2}
                >
                  Create Account
                </Button>
              </Stack>
            </form>

            <HStack spacing={4}>
              <Divider />
              <Text fontSize="sm" color="gray.500" whiteSpace="nowrap">
                or
              </Text>
              <Divider />
            </HStack>

            <Text textAlign="center" fontSize="sm" color="gray.600">
              Already have an account?{' '}
              <Link as={RouterLink} to="/login" color="brand.600" fontWeight="600">
                Sign in
              </Link>
            </Text>
          </VStack>
        </Box>
      </Container>
    </Box>
  );
};

// Password check indicator component
interface PasswordCheckProps {
  passed: boolean;
  label: string;
}

const PasswordCheck: React.FC<PasswordCheckProps> = ({ passed, label }) => (
  <HStack spacing={2} fontSize="xs" color={passed ? 'fynbos.500' : 'gray.400'}>
    {passed ? <CheckIcon boxSize={3} /> : <CloseIcon boxSize={3} />}
    <Text>{label}</Text>
  </HStack>
);

export default RegisterPage;
