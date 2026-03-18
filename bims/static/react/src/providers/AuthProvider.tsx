/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Authentication context provider for BIMS React frontend.
 * Handles login, logout, registration, and user state.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';

interface User {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  isSuperuser: boolean;
  dateJoined: string;
  profileImage?: string;
}

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  register: (data: RegisterData) => Promise<boolean>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

interface RegisterData {
  username: string;
  email: string;
  password1: string;
  password2: string;
  firstName?: string;
  lastName?: string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch current user on mount
  const refreshUser = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Try to get current user from session
      const response = await apiClient.get('auth/user/');
      if (response.data?.data) {
        const userData = response.data.data;
        setUser({
          id: userData.id,
          username: userData.username,
          email: userData.email,
          firstName: userData.first_name || '',
          lastName: userData.last_name || '',
          isStaff: userData.is_staff || false,
          isSuperuser: userData.is_superuser || false,
          dateJoined: userData.date_joined,
          profileImage: userData.profile_image,
        });
      } else {
        setUser(null);
      }
    } catch (err: any) {
      // 401/403 means not authenticated - that's okay
      if (err.response?.status !== 401 && err.response?.status !== 403) {
        console.error('Error fetching user:', err);
      }
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (username: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      // Get CSRF token first
      await apiClient.get('auth/csrf/');

      // Login request
      const response = await apiClient.post('auth/login/', {
        username,
        password,
      });

      if (response.data?.success) {
        await refreshUser();
        return true;
      } else {
        setError(response.data?.error || 'Login failed');
        return false;
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.error ||
        err.response?.data?.detail ||
        'Login failed. Please check your credentials.';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [refreshUser]);

  const logout = useCallback(async () => {
    try {
      setIsLoading(true);
      await apiClient.post('auth/logout/');
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (data: RegisterData): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      // Get CSRF token first
      await apiClient.get('auth/csrf/');

      const response = await apiClient.post('auth/register/', {
        username: data.username,
        email: data.email,
        password1: data.password1,
        password2: data.password2,
        first_name: data.firstName,
        last_name: data.lastName,
      });

      if (response.data?.success) {
        // Auto-login after registration
        await refreshUser();
        return true;
      } else {
        setError(response.data?.error || 'Registration failed');
        return false;
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.error ||
        err.response?.data?.detail ||
        Object.values(err.response?.data || {}).flat().join(', ') ||
        'Registration failed. Please try again.';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [refreshUser]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value: AuthContextValue = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    logout,
    register,
    refreshUser,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthProvider;
