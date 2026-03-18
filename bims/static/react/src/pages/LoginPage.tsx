/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Login page for BIMS React frontend.
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
  useColorModeValue,
} from '@chakra-ui/react';
import { ViewIcon, ViewOffIcon } from '@chakra-ui/icons';
import { Link as RouterLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const { login, isLoading, error, isAuthenticated, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Clear errors on mount
  useEffect(() => {
    clearError();
  }, [clearError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!username.trim()) {
      setFormError('Username is required');
      return;
    }
    if (!password) {
      setFormError('Password is required');
      return;
    }

    const success = await login(username, password);
    if (success) {
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  };

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box bg="bg.light" minH="calc(100vh - 120px)" py={12}>
      <Container maxW="md">
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
                Welcome Back
              </Heading>
              <Text color="gray.600">
                Sign in to access your BIMS account
              </Text>
            </VStack>

            {(error || formError) && (
              <Alert status="error" borderRadius="lg">
                <AlertIcon />
                {formError || error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <Stack spacing={4}>
                <FormControl isRequired isInvalid={!!formError && !username}>
                  <FormLabel>Username</FormLabel>
                  <Input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    size="lg"
                    autoComplete="username"
                  />
                </FormControl>

                <FormControl isRequired isInvalid={!!formError && !password}>
                  <FormLabel>Password</FormLabel>
                  <InputGroup size="lg">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      autoComplete="current-password"
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
                </FormControl>

                <HStack justify="flex-end">
                  <Link
                    as={RouterLink}
                    to="/forgot-password"
                    color="brand.600"
                    fontSize="sm"
                  >
                    Forgot password?
                  </Link>
                </HStack>

                <Button
                  type="submit"
                  size="lg"
                  colorScheme="brand"
                  isLoading={isLoading}
                  loadingText="Signing in..."
                  width="100%"
                  mt={2}
                >
                  Sign In
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
              Don't have an account?{' '}
              <Link as={RouterLink} to="/register" color="brand.600" fontWeight="600">
                Create one
              </Link>
            </Text>
          </VStack>
        </Box>
      </Container>
    </Box>
  );
};

export default LoginPage;
