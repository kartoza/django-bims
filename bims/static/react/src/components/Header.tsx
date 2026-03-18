/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Header component with full navigation menu matching original BIMS.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Flex,
  HStack,
  IconButton,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  MenuGroup,
  Text,
  Link,
  useDisclosure,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  VStack,
  useBreakpointValue,
  Avatar,
  Badge,
  Divider,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import {
  HamburgerIcon,
  SearchIcon,
  ChevronDownIcon,
  SettingsIcon,
  InfoIcon,
  ExternalLinkIcon,
  AddIcon,
  DownloadIcon,
  EditIcon,
  ViewIcon,
  CheckIcon,
  StarIcon,
  AtSignIcon,
  LockIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink, useLocation } from 'react-router-dom';

// User type - will be fetched from API
interface User {
  id: number;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  isSuperuser: boolean;
  isStaff: boolean;
}

interface NavLinkProps {
  to: string;
  children: React.ReactNode;
  isActive?: boolean;
}

const NavLink: React.FC<NavLinkProps> = ({ to, children, isActive }) => (
  <Link
    as={RouterLink}
    to={to}
    px={3}
    py={2}
    rounded="md"
    fontWeight={isActive ? '600' : '400'}
    color={isActive ? 'brand.600' : 'gray.700'}
    bg={isActive ? 'brand.50' : 'transparent'}
    _hover={{
      textDecoration: 'none',
      bg: 'brand.50',
      color: 'brand.600',
    }}
  >
    {children}
  </Link>
);

const Header: React.FC = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const location = useLocation();
  const isMobile = useBreakpointValue({ base: true, lg: false });

  // Mock user state - in production, fetch from API
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    // Try to get user info from a cookie or make API call
    // For now, check if we have a session cookie
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/v1/auth/user/', {
          credentials: 'include',
        });
        if (response.ok) {
          const userData = await response.json();
          if (userData.success && userData.data) {
            setUser(userData.data);
            setIsAuthenticated(true);
          }
        }
      } catch {
        // Not authenticated
        setIsAuthenticated(false);
        setUser(null);
      }
    };
    checkAuth();
  }, []);

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/' || location.pathname === '';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <Box
      as="header"
      bg="white"
      borderBottomWidth={1}
      borderColor="gray.200"
      position="sticky"
      top={0}
      zIndex={100}
      boxShadow="sm"
    >
      <Flex
        h="60px"
        px={{ base: 4, md: 6 }}
        alignItems="center"
        justifyContent="space-between"
        maxW="100%"
      >
        {/* Logo and Brand */}
        <HStack spacing={3}>
          <Link as={RouterLink} to="/" _hover={{ textDecoration: 'none' }}>
            <HStack spacing={2}>
              <Box
                w="40px"
                h="40px"
                bg="brand.500"
                borderRadius="lg"
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Text color="white" fontWeight="bold" fontSize="xl">
                  B
                </Text>
              </Box>
              <VStack spacing={0} alignItems="flex-start" display={{ base: 'none', md: 'flex' }}>
                <Text fontWeight="bold" fontSize="lg" color="gray.800" lineHeight={1.2}>
                  BIMS
                </Text>
                <Text fontSize="xs" color="gray.500" lineHeight={1}>
                  Biodiversity Information
                </Text>
              </VStack>
            </HStack>
          </Link>
        </HStack>

        {/* Desktop Navigation */}
        <HStack spacing={1} display={{ base: 'none', lg: 'flex' }}>
          <NavLink to="/" isActive={isActivePath('/')}>
            Home
          </NavLink>
          <NavLink to="/map" isActive={isActivePath('/map')}>
            Map
          </NavLink>

          {/* Data Menu */}
          <Menu>
            <MenuButton
              as={Button}
              variant="ghost"
              rightIcon={<ChevronDownIcon />}
              fontWeight="400"
              color="gray.700"
              _hover={{ bg: 'brand.50', color: 'brand.600' }}
            >
              Data
            </MenuButton>
            <MenuList>
              <MenuItem as={RouterLink} to="/map" icon={<SearchIcon />}>
                Search Records
              </MenuItem>
              <MenuItem as={RouterLink} to="/source-references" icon={<ViewIcon />}>
                Source References
              </MenuItem>
              <MenuItem as={RouterLink} to="/site-visits" icon={<ViewIcon />}>
                Site Visits
              </MenuItem>
              <MenuDivider />
              <MenuItem as={RouterLink} to="/downloads" icon={<DownloadIcon />}>
                Download Requests
              </MenuItem>
              <MenuItem as="a" href="/download-taxa-list/" icon={<DownloadIcon />}>
                Download Taxa List <ExternalLinkIcon ml={1} boxSize={3} />
              </MenuItem>
            </MenuList>
          </Menu>

          {/* Upload Menu */}
          <Menu>
            <MenuButton
              as={Button}
              variant="ghost"
              rightIcon={<ChevronDownIcon />}
              fontWeight="400"
              color="gray.700"
              _hover={{ bg: 'brand.50', color: 'brand.600' }}
            >
              Upload
            </MenuButton>
            <MenuList>
              <MenuItem as={RouterLink} to="/upload/occurrence" icon={<AddIcon />}>
                Occurrence Data
              </MenuItem>
              <MenuItem as={RouterLink} to="/upload/taxa" icon={<AddIcon />}>
                Taxonomic Data
              </MenuItem>
              <MenuItem as={RouterLink} to="/upload/physico-chemical" icon={<AddIcon />}>
                Physico-Chemical Data
              </MenuItem>
              <MenuItem as={RouterLink} to="/upload/water-temperature" icon={<AddIcon />}>
                Water Temperature
              </MenuItem>
              <MenuDivider />
              <MenuItem as={RouterLink} to="/upload/shapefile" icon={<AddIcon />}>
                Shapefile / Boundary
              </MenuItem>
              <MenuItem as={RouterLink} to="/upload/spatial-layer" icon={<AddIcon />}>
                Spatial Layer
              </MenuItem>
            </MenuList>
          </Menu>

          {/* Add Data Menu */}
          <Menu>
            <MenuButton
              as={Button}
              variant="ghost"
              rightIcon={<ChevronDownIcon />}
              fontWeight="400"
              color="gray.700"
              _hover={{ bg: 'brand.50', color: 'brand.600' }}
            >
              Add
            </MenuButton>
            <MenuList>
              <MenuItem as={RouterLink} to="/add/site" icon={<AddIcon />}>
                Location Site
              </MenuItem>
              <MenuItem as={RouterLink} to="/add/wetland" icon={<AddIcon />}>
                Wetland Site
              </MenuItem>
              <MenuDivider />
              <MenuItem as={RouterLink} to="/add/fish" icon={<AddIcon />}>
                Fish Record
              </MenuItem>
              <MenuItem as={RouterLink} to="/add/invertebrate" icon={<AddIcon />}>
                Invertebrate Record
              </MenuItem>
              <MenuItem as={RouterLink} to="/add/algae" icon={<AddIcon />}>
                Algae Record
              </MenuItem>
              <MenuItem as={RouterLink} to="/add/module" icon={<AddIcon />}>
                Module Record
              </MenuItem>
              <MenuDivider />
              <MenuItem as={RouterLink} to="/add/abiotic" icon={<AddIcon />}>
                Abiotic Data
              </MenuItem>
              <MenuItem as={RouterLink} to="/add/source-reference" icon={<AddIcon />}>
                Source Reference
              </MenuItem>
            </MenuList>
          </Menu>

          {/* Validation Menu (Staff/Superuser only) */}
          {(user?.isStaff || user?.isSuperuser) && (
            <Menu>
              <MenuButton
                as={Button}
                variant="ghost"
                rightIcon={<ChevronDownIcon />}
                fontWeight="400"
                color="gray.700"
                _hover={{ bg: 'brand.50', color: 'brand.600' }}
              >
                Validate
              </MenuButton>
              <MenuList>
                <MenuItem as={RouterLink} to="/validate/sites" icon={<CheckIcon />}>
                  Pending Sites
                </MenuItem>
                <MenuItem as={RouterLink} to="/validate/records" icon={<CheckIcon />}>
                  Pending Records
                </MenuItem>
                <MenuItem as={RouterLink} to="/validate/taxa" icon={<CheckIcon />}>
                  Taxa Proposals
                </MenuItem>
              </MenuList>
            </Menu>
          )}

          {/* Admin Menu (Staff/Superuser only) */}
          {(user?.isStaff || user?.isSuperuser) && (
            <Menu>
              <MenuButton
                as={Button}
                variant="ghost"
                rightIcon={<ChevronDownIcon />}
                fontWeight="400"
                color="gray.700"
                _hover={{ bg: 'brand.50', color: 'brand.600' }}
              >
                Admin
              </MenuButton>
              <MenuList>
                <MenuItem as={RouterLink} to="/admin/taxa" icon={<SettingsIcon />}>
                  Taxa Management
                </MenuItem>
                <MenuItem as={RouterLink} to="/admin/dashboard" icon={<SettingsIcon />}>
                  Dashboard Settings
                </MenuItem>
                <MenuItem as={RouterLink} to="/admin/layers" icon={<SettingsIcon />}>
                  Visualization Layers
                </MenuItem>
                <MenuItem as={RouterLink} to="/admin/context-layers" icon={<SettingsIcon />}>
                  Context Layers
                </MenuItem>
                <MenuDivider />
                <MenuItem as={RouterLink} to="/harvest/gbif" icon={<DownloadIcon />}>
                  Harvest from GBIF
                </MenuItem>
                <MenuItem as={RouterLink} to="/harvest/species" icon={<DownloadIcon />}>
                  Harvest Species
                </MenuItem>
                <MenuDivider />
                {user?.isSuperuser && (
                  <>
                    <MenuItem as={RouterLink} to="/admin/summary" icon={<ViewIcon />}>
                      Summary Report
                    </MenuItem>
                    <MenuItem as={RouterLink} to="/admin/backups" icon={<SettingsIcon />}>
                      Backups Management
                    </MenuItem>
                    <MenuDivider />
                  </>
                )}
                <MenuItem as="a" href="/admin/" icon={<ExternalLinkIcon />}>
                  Django Admin <ExternalLinkIcon ml={1} boxSize={3} />
                </MenuItem>
              </MenuList>
            </Menu>
          )}

          {/* About/Help Menu */}
          <Menu>
            <MenuButton
              as={Button}
              variant="ghost"
              rightIcon={<ChevronDownIcon />}
              fontWeight="400"
              color="gray.700"
              _hover={{ bg: 'brand.50', color: 'brand.600' }}
            >
              About
            </MenuButton>
            <MenuList>
              <MenuItem as={RouterLink} to="/about" icon={<InfoIcon />}>
                About BIMS
              </MenuItem>
              <MenuItem as={RouterLink} to="/contact" icon={<AtSignIcon />}>
                Contact Us
              </MenuItem>
              <MenuItem as={RouterLink} to="/resources" icon={<ViewIcon />}>
                Resources & Links
              </MenuItem>
              <MenuDivider />
              <MenuItem as={RouterLink} to="/bug-report" icon={<EditIcon />}>
                Report a Bug
              </MenuItem>
              <MenuItem as="a" href="https://github.com/kartoza/django-bims" target="_blank" icon={<ExternalLinkIcon />}>
                GitHub
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>

        {/* Right Side Actions */}
        <HStack spacing={2}>
          {/* Upload Button (Desktop) */}
          <Button
            as={RouterLink}
            to="/upload/occurrence"
            colorScheme="brand"
            size="sm"
            leftIcon={<AddIcon />}
            display={{ base: 'none', lg: 'flex' }}
          >
            Upload
          </Button>

          {/* User Menu */}
          {isAuthenticated && user ? (
            <Menu>
              <MenuButton
                as={Button}
                variant="ghost"
                size="sm"
                display={{ base: 'none', md: 'flex' }}
              >
                <HStack spacing={2}>
                  <Avatar size="xs" name={user.username} />
                  <Text display={{ base: 'none', lg: 'block' }}>
                    {user.firstName || user.username}
                  </Text>
                  <ChevronDownIcon />
                </HStack>
              </MenuButton>
              <MenuList>
                <MenuGroup title="Account">
                  <MenuItem as={RouterLink} to={`/profile/${user.username}`} icon={<ViewIcon />}>
                    My Profile
                  </MenuItem>
                  <MenuItem as={RouterLink} to="/my-site-visits" icon={<ViewIcon />}>
                    My Site Visits
                  </MenuItem>
                  <MenuItem as={RouterLink} to="/downloads" icon={<DownloadIcon />}>
                    Download Requests
                  </MenuItem>
                </MenuGroup>
                <MenuDivider />
                <MenuItem as="a" href="/accounts/logout/" icon={<LockIcon />} color="red.500">
                  Log Out
                </MenuItem>
              </MenuList>
            </Menu>
          ) : (
            <HStack spacing={2} display={{ base: 'none', md: 'flex' }}>
              <Button as="a" href="/accounts/login/" variant="ghost" size="sm">
                Sign In
              </Button>
              <Button as="a" href="/accounts/signup/" colorScheme="brand" variant="outline" size="sm">
                Register
              </Button>
            </HStack>
          )}

          {/* Mobile Menu Button */}
          <IconButton
            aria-label="Open menu"
            icon={<HamburgerIcon />}
            variant="ghost"
            display={{ base: 'flex', lg: 'none' }}
            onClick={onOpen}
          />
        </HStack>
      </Flex>

      {/* Mobile Drawer */}
      <Drawer isOpen={isOpen} placement="right" onClose={onClose} size="sm">
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth={1}>
            <HStack>
              <Box
                w="32px"
                h="32px"
                bg="brand.500"
                borderRadius="md"
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Text color="white" fontWeight="bold" fontSize="md">
                  B
                </Text>
              </Box>
              <Text>BIMS Menu</Text>
            </HStack>
          </DrawerHeader>
          <DrawerBody p={0}>
            <Accordion allowMultiple>
              {/* Navigation Links */}
              <Box p={4}>
                <VStack align="stretch" spacing={2}>
                  <Link as={RouterLink} to="/" py={2} onClick={onClose}>
                    Home
                  </Link>
                  <Link as={RouterLink} to="/map" py={2} onClick={onClose}>
                    Map
                  </Link>
                </VStack>
              </Box>

              <Divider />

              {/* Data Section */}
              <AccordionItem border="none">
                <AccordionButton>
                  <Box flex="1" textAlign="left" fontWeight="600">
                    Data
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel pb={4}>
                  <VStack align="stretch" spacing={2}>
                    <Link as={RouterLink} to="/source-references" onClick={onClose}>
                      Source References
                    </Link>
                    <Link as={RouterLink} to="/site-visits" onClick={onClose}>
                      Site Visits
                    </Link>
                    <Link as={RouterLink} to="/downloads" onClick={onClose}>
                      Download Requests
                    </Link>
                  </VStack>
                </AccordionPanel>
              </AccordionItem>

              {/* Upload Section */}
              <AccordionItem border="none">
                <AccordionButton>
                  <Box flex="1" textAlign="left" fontWeight="600">
                    Upload
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel pb={4}>
                  <VStack align="stretch" spacing={2}>
                    <Link as={RouterLink} to="/upload/occurrence" onClick={onClose}>
                      Occurrence Data
                    </Link>
                    <Link as={RouterLink} to="/upload/taxa" onClick={onClose}>
                      Taxonomic Data
                    </Link>
                    <Link as={RouterLink} to="/upload/physico-chemical" onClick={onClose}>
                      Physico-Chemical
                    </Link>
                    <Link as={RouterLink} to="/upload/shapefile" onClick={onClose}>
                      Shapefile
                    </Link>
                  </VStack>
                </AccordionPanel>
              </AccordionItem>

              {/* Add Section */}
              <AccordionItem border="none">
                <AccordionButton>
                  <Box flex="1" textAlign="left" fontWeight="600">
                    Add Data
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel pb={4}>
                  <VStack align="stretch" spacing={2}>
                    <Link as={RouterLink} to="/add/site" onClick={onClose}>
                      Location Site
                    </Link>
                    <Link as={RouterLink} to="/add/fish" onClick={onClose}>
                      Fish Record
                    </Link>
                    <Link as={RouterLink} to="/add/invertebrate" onClick={onClose}>
                      Invertebrate Record
                    </Link>
                    <Link as={RouterLink} to="/add/algae" onClick={onClose}>
                      Algae Record
                    </Link>
                    <Link as={RouterLink} to="/add/source-reference" onClick={onClose}>
                      Source Reference
                    </Link>
                  </VStack>
                </AccordionPanel>
              </AccordionItem>

              {/* Admin Section */}
              {(user?.isStaff || user?.isSuperuser) && (
                <AccordionItem border="none">
                  <AccordionButton>
                    <Box flex="1" textAlign="left" fontWeight="600">
                      Admin
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel pb={4}>
                    <VStack align="stretch" spacing={2}>
                      <Link as={RouterLink} to="/validate/sites" onClick={onClose}>
                        Pending Validation
                      </Link>
                      <Link as={RouterLink} to="/admin/taxa" onClick={onClose}>
                        Taxa Management
                      </Link>
                      <Link as="a" href="/admin/" onClick={onClose}>
                        Django Admin
                      </Link>
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              )}

              {/* About Section */}
              <AccordionItem border="none">
                <AccordionButton>
                  <Box flex="1" textAlign="left" fontWeight="600">
                    About
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel pb={4}>
                  <VStack align="stretch" spacing={2}>
                    <Link as={RouterLink} to="/about" onClick={onClose}>
                      About BIMS
                    </Link>
                    <Link as={RouterLink} to="/contact" onClick={onClose}>
                      Contact Us
                    </Link>
                    <Link as={RouterLink} to="/resources" onClick={onClose}>
                      Resources
                    </Link>
                    <Link as={RouterLink} to="/bug-report" onClick={onClose}>
                      Report a Bug
                    </Link>
                  </VStack>
                </AccordionPanel>
              </AccordionItem>

              <Divider />

              {/* Account Section */}
              <Box p={4}>
                {isAuthenticated && user ? (
                  <VStack align="stretch" spacing={2}>
                    <HStack>
                      <Avatar size="sm" name={user.username} />
                      <Text fontWeight="600">{user.username}</Text>
                    </HStack>
                    <Link as={RouterLink} to={`/profile/${user.username}`} onClick={onClose}>
                      My Profile
                    </Link>
                    <Link as={RouterLink} to="/my-site-visits" onClick={onClose}>
                      My Site Visits
                    </Link>
                    <Link as="a" href="/accounts/logout/" color="red.500">
                      Log Out
                    </Link>
                  </VStack>
                ) : (
                  <VStack align="stretch" spacing={2}>
                    <Button as="a" href="/accounts/login/" colorScheme="brand" w="100%">
                      Sign In
                    </Button>
                    <Button as="a" href="/accounts/signup/" variant="outline" w="100%">
                      Register
                    </Button>
                  </VStack>
                )}
              </Box>
            </Accordion>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};

export default Header;
