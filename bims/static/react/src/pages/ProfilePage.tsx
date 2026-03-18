/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * User Profile Page - Display and edit user profile information.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  Heading,
  Text,
  Avatar,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Card,
  CardBody,
  CardHeader,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Badge,
  Divider,
  useToast,
  Spinner,
  Center,
  Alert,
  AlertIcon,
  IconButton,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  useColorModeValue,
} from '@chakra-ui/react';
import { EditIcon, CheckIcon, CloseIcon } from '@chakra-ui/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';
import { apiClient } from '../api/client';

interface UserProfile {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  isSuperuser: boolean;
  dateJoined: string;
  lastLogin?: string;
  bio?: string;
  organization?: string;
  profileImage?: string;
}

interface UserStats {
  totalRecords: number;
  totalSiteVisits: number;
  totalUploads: number;
  pendingValidations: number;
}

const ProfilePage: React.FC = () => {
  const { username } = useParams<{ username?: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const { user: currentUser, isAuthenticated, refreshUser } = useAuth();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Form state for editing
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    bio: '',
    organization: '',
  });

  // Password change state
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  const isOwnProfile = !username || (currentUser && currentUser.username === username);
  const targetUsername = username || currentUser?.username;

  // Fetch profile data
  useEffect(() => {
    const fetchProfile = async () => {
      if (!targetUsername) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        // For own profile, use the auth endpoint
        if (isOwnProfile && currentUser) {
          setProfile({
            id: currentUser.id,
            username: currentUser.username,
            email: currentUser.email,
            firstName: currentUser.firstName,
            lastName: currentUser.lastName,
            isStaff: currentUser.isStaff,
            isSuperuser: currentUser.isSuperuser,
            dateJoined: currentUser.dateJoined,
            profileImage: currentUser.profileImage,
          });

          setFormData({
            firstName: currentUser.firstName || '',
            lastName: currentUser.lastName || '',
            email: currentUser.email || '',
            bio: '',
            organization: '',
          });

          // Fetch user stats
          try {
            const statsResponse = await apiClient.get(`users/${currentUser.id}/stats/`);
            if (statsResponse.data?.data) {
              setStats(statsResponse.data.data);
            }
          } catch (e) {
            // Stats endpoint might not exist yet
            setStats({
              totalRecords: 0,
              totalSiteVisits: 0,
              totalUploads: 0,
              pendingValidations: 0,
            });
          }
        } else {
          // Fetch other user's profile
          const response = await apiClient.get(`users/${targetUsername}/`);
          if (response.data?.data) {
            const userData = response.data.data;
            setProfile({
              id: userData.id,
              username: userData.username,
              email: userData.email || '',
              firstName: userData.first_name || '',
              lastName: userData.last_name || '',
              isStaff: userData.is_staff || false,
              isSuperuser: userData.is_superuser || false,
              dateJoined: userData.date_joined,
              profileImage: userData.profile_image,
              bio: userData.bio,
              organization: userData.organization,
            });
          }
        }
      } catch (error) {
        console.error('Failed to fetch profile:', error);
        toast({
          title: 'Error',
          description: 'Failed to load profile',
          status: 'error',
          duration: 5000,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [targetUsername, isOwnProfile, currentUser, toast]);

  // Handle profile update
  const handleSaveProfile = useCallback(async () => {
    setIsSaving(true);
    try {
      const response = await apiClient.patch('auth/update_profile/', {
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
      });

      if (response.data?.success !== false) {
        await refreshUser();
        setIsEditing(false);
        toast({
          title: 'Profile updated',
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to update profile',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSaving(false);
    }
  }, [formData, refreshUser, toast]);

  // Handle password change
  const handleChangePassword = useCallback(async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast({
        title: 'Error',
        description: 'Passwords do not match',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setIsSaving(true);
    try {
      const response = await apiClient.post('auth/change_password/', {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword,
      });

      if (response.data?.success !== false) {
        onClose();
        setPasswordData({
          currentPassword: '',
          newPassword: '',
          confirmPassword: '',
        });
        toast({
          title: 'Password changed',
          description: 'Your password has been updated successfully',
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to change password',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSaving(false);
    }
  }, [passwordData, onClose, toast]);

  if (!isAuthenticated && isOwnProfile) {
    return (
      <Container maxW="container.md" py={10}>
        <Alert status="warning">
          <AlertIcon />
          Please sign in to view your profile.
        </Alert>
      </Container>
    );
  }

  if (isLoading) {
    return (
      <Center h="calc(100vh - 140px)">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (!profile) {
    return (
      <Container maxW="container.md" py={10}>
        <Alert status="error">
          <AlertIcon />
          Profile not found.
        </Alert>
      </Container>
    );
  }

  return (
    <Box bg={bgColor} minH="calc(100vh - 100px)" py={8}>
      <Container maxW="container.lg">
        {/* Profile Header */}
        <Card bg={cardBg} mb={6}>
          <CardBody>
            <HStack spacing={6} align="start" flexWrap="wrap">
              <Avatar
                size="2xl"
                name={`${profile.firstName} ${profile.lastName}` || profile.username}
                src={profile.profileImage}
              />
              <VStack align="start" flex={1} spacing={2}>
                <HStack>
                  <Heading size="lg">
                    {profile.firstName && profile.lastName
                      ? `${profile.firstName} ${profile.lastName}`
                      : profile.username}
                  </Heading>
                  {profile.isStaff && (
                    <Badge colorScheme="purple">Staff</Badge>
                  )}
                  {profile.isSuperuser && (
                    <Badge colorScheme="red">Admin</Badge>
                  )}
                </HStack>
                <Text color="gray.500">@{profile.username}</Text>
                {profile.organization && (
                  <Text color="gray.600">{profile.organization}</Text>
                )}
                <Text fontSize="sm" color="gray.500">
                  Member since {new Date(profile.dateJoined).toLocaleDateString()}
                </Text>
              </VStack>
              {isOwnProfile && (
                <Button
                  leftIcon={<EditIcon />}
                  colorScheme="brand"
                  variant="outline"
                  onClick={() => setIsEditing(!isEditing)}
                >
                  {isEditing ? 'Cancel' : 'Edit Profile'}
                </Button>
              )}
            </HStack>
          </CardBody>
        </Card>

        {/* Stats Cards */}
        {stats && (
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} mb={6}>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Records</StatLabel>
                  <StatNumber>{stats.totalRecords.toLocaleString()}</StatNumber>
                  <StatHelpText>Total contributions</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Site Visits</StatLabel>
                  <StatNumber>{stats.totalSiteVisits.toLocaleString()}</StatNumber>
                  <StatHelpText>Field surveys</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Uploads</StatLabel>
                  <StatNumber>{stats.totalUploads.toLocaleString()}</StatNumber>
                  <StatHelpText>Data files</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            {profile.isStaff && (
              <Card bg={cardBg}>
                <CardBody>
                  <Stat>
                    <StatLabel>Pending</StatLabel>
                    <StatNumber color="orange.500">
                      {stats.pendingValidations}
                    </StatNumber>
                    <StatHelpText>Awaiting validation</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            )}
          </SimpleGrid>
        )}

        {/* Profile Tabs */}
        <Card bg={cardBg}>
          <Tabs>
            <TabList px={4}>
              <Tab>Profile</Tab>
              {isOwnProfile && <Tab>Settings</Tab>}
              <Tab>Activity</Tab>
            </TabList>

            <TabPanels>
              {/* Profile Tab */}
              <TabPanel>
                {isEditing ? (
                  <VStack spacing={4} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <FormControl>
                        <FormLabel>First Name</FormLabel>
                        <Input
                          value={formData.firstName}
                          onChange={(e) =>
                            setFormData({ ...formData, firstName: e.target.value })
                          }
                        />
                      </FormControl>
                      <FormControl>
                        <FormLabel>Last Name</FormLabel>
                        <Input
                          value={formData.lastName}
                          onChange={(e) =>
                            setFormData({ ...formData, lastName: e.target.value })
                          }
                        />
                      </FormControl>
                    </SimpleGrid>
                    <FormControl>
                      <FormLabel>Email</FormLabel>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) =>
                          setFormData({ ...formData, email: e.target.value })
                        }
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>Bio</FormLabel>
                      <Textarea
                        value={formData.bio}
                        onChange={(e) =>
                          setFormData({ ...formData, bio: e.target.value })
                        }
                        placeholder="Tell us about yourself..."
                        rows={4}
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>Organization</FormLabel>
                      <Input
                        value={formData.organization}
                        onChange={(e) =>
                          setFormData({ ...formData, organization: e.target.value })
                        }
                        placeholder="Your organization or institution"
                      />
                    </FormControl>
                    <HStack justify="flex-end">
                      <Button
                        variant="ghost"
                        onClick={() => setIsEditing(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        colorScheme="brand"
                        leftIcon={<CheckIcon />}
                        onClick={handleSaveProfile}
                        isLoading={isSaving}
                      >
                        Save Changes
                      </Button>
                    </HStack>
                  </VStack>
                ) : (
                  <VStack spacing={4} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <Box>
                        <Text fontWeight="medium" color="gray.500" fontSize="sm">
                          Email
                        </Text>
                        <Text>{profile.email || 'Not set'}</Text>
                      </Box>
                      <Box>
                        <Text fontWeight="medium" color="gray.500" fontSize="sm">
                          Username
                        </Text>
                        <Text>{profile.username}</Text>
                      </Box>
                    </SimpleGrid>
                    {profile.bio && (
                      <Box>
                        <Text fontWeight="medium" color="gray.500" fontSize="sm">
                          Bio
                        </Text>
                        <Text>{profile.bio}</Text>
                      </Box>
                    )}
                  </VStack>
                )}
              </TabPanel>

              {/* Settings Tab (own profile only) */}
              {isOwnProfile && (
                <TabPanel>
                  <VStack spacing={6} align="stretch">
                    <Box>
                      <Heading size="sm" mb={4}>
                        Security
                      </Heading>
                      <Button colorScheme="brand" variant="outline" onClick={onOpen}>
                        Change Password
                      </Button>
                    </Box>
                    <Divider />
                    <Box>
                      <Heading size="sm" mb={4}>
                        Notifications
                      </Heading>
                      <Text color="gray.500">
                        Email notification settings coming soon.
                      </Text>
                    </Box>
                  </VStack>
                </TabPanel>
              )}

              {/* Activity Tab */}
              <TabPanel>
                <VStack spacing={4} align="stretch">
                  <Text color="gray.500" textAlign="center" py={8}>
                    Activity feed coming soon. This will show recent records,
                    site visits, and other contributions.
                  </Text>
                </VStack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Card>

        {/* Password Change Modal */}
        <Modal isOpen={isOpen} onClose={onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Change Password</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Current Password</FormLabel>
                  <Input
                    type="password"
                    value={passwordData.currentPassword}
                    onChange={(e) =>
                      setPasswordData({
                        ...passwordData,
                        currentPassword: e.target.value,
                      })
                    }
                  />
                </FormControl>
                <FormControl isRequired>
                  <FormLabel>New Password</FormLabel>
                  <Input
                    type="password"
                    value={passwordData.newPassword}
                    onChange={(e) =>
                      setPasswordData({
                        ...passwordData,
                        newPassword: e.target.value,
                      })
                    }
                  />
                </FormControl>
                <FormControl isRequired>
                  <FormLabel>Confirm New Password</FormLabel>
                  <Input
                    type="password"
                    value={passwordData.confirmPassword}
                    onChange={(e) =>
                      setPasswordData({
                        ...passwordData,
                        confirmPassword: e.target.value,
                      })
                    }
                  />
                </FormControl>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onClose}>
                Cancel
              </Button>
              <Button
                colorScheme="brand"
                onClick={handleChangePassword}
                isLoading={isSaving}
              >
                Change Password
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Container>
    </Box>
  );
};

export default ProfilePage;
