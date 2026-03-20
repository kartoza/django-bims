/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Error boundary component to catch React errors and display a fallback UI.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  VStack,
  Code,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Link,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Container maxW="container.md" py={12}>
          <VStack spacing={6} align="stretch">
            <Alert
              status="error"
              variant="subtle"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              textAlign="center"
              borderRadius="lg"
              py={8}
            >
              <AlertIcon boxSize="40px" mr={0} />
              <AlertTitle mt={4} mb={1} fontSize="lg">
                Something went wrong
              </AlertTitle>
              <AlertDescription maxWidth="sm">
                An unexpected error occurred. Please try refreshing the page or
                returning to the home page.
              </AlertDescription>
            </Alert>

            <VStack spacing={3}>
              <Button colorScheme="brand" onClick={this.handleReload}>
                Refresh Page
              </Button>
              <Button
                as={RouterLink}
                to="/"
                variant="ghost"
                onClick={this.handleGoHome}
              >
                Go to Home Page
              </Button>
            </VStack>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Box
                bg="gray.50"
                p={4}
                borderRadius="md"
                borderWidth={1}
                borderColor="gray.200"
              >
                <Heading size="sm" mb={2} color="red.600">
                  Error Details (Development Only)
                </Heading>
                <Code
                  display="block"
                  whiteSpace="pre-wrap"
                  p={3}
                  bg="gray.100"
                  borderRadius="md"
                  fontSize="xs"
                >
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack && (
                    <>
                      {'\n\nComponent Stack:'}
                      {this.state.errorInfo.componentStack}
                    </>
                  )}
                </Code>
              </Box>
            )}

            <Text fontSize="sm" color="gray.500" textAlign="center">
              If this problem persists, please{' '}
              <Link as={RouterLink} to="/bug-report" color="brand.500">
                report a bug
              </Link>
              .
            </Text>
          </VStack>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
