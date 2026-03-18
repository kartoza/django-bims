/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Header component with navigation menu.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
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
  Image,
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
} from '@chakra-ui/react';
import {
  HamburgerIcon,
  SearchIcon,
  ChevronDownIcon,
  SettingsIcon,
  InfoIcon,
  ExternalLinkIcon,
} from '@chakra-ui/icons';
import { Link as RouterLink, useLocation } from 'react-router-dom';

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
  const isMobile = useBreakpointValue({ base: true, md: false });

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/' || location.pathname === '';
    }
    return location.pathname.startsWith(path);
  };

  const navLinks = [
    { to: '/', label: 'Home' },
    { to: '/map', label: 'Map' },
  ];

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
        maxW="container.2xl"
        mx="auto"
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
              <VStack spacing={0} alignItems="flex-start" display={{ base: 'none', sm: 'flex' }}>
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
        <HStack spacing={1} display={{ base: 'none', md: 'flex' }}>
          {navLinks.map((link) => (
            <NavLink key={link.to} to={link.to} isActive={isActivePath(link.to)}>
              {link.label}
            </NavLink>
          ))}

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
              <MenuItem as={RouterLink} to="/map">
                <SearchIcon mr={2} /> Search Records
              </MenuItem>
              <MenuItem as="a" href="/upload/" target="_blank">
                Upload Data <ExternalLinkIcon ml={2} />
              </MenuItem>
              <MenuItem as="a" href="/download-request/" target="_blank">
                Download Requests <ExternalLinkIcon ml={2} />
              </MenuItem>
              <MenuDivider />
              <MenuItem as="a" href="/source-references/" target="_blank">
                Source References <ExternalLinkIcon ml={2} />
              </MenuItem>
            </MenuList>
          </Menu>

          {/* Admin Menu */}
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
              <MenuItem as="a" href="/admin/" target="_blank">
                <SettingsIcon mr={2} /> Django Admin <ExternalLinkIcon ml={2} />
              </MenuItem>
              <MenuItem as="a" href="/taxa-management/" target="_blank">
                Taxa Management <ExternalLinkIcon ml={2} />
              </MenuItem>
              <MenuItem as="a" href="/site-visit/list/" target="_blank">
                Site Visits <ExternalLinkIcon ml={2} />
              </MenuItem>
              <MenuDivider />
              <MenuItem as="a" href="/nonvalidated-site/" target="_blank">
                Pending Validation <ExternalLinkIcon ml={2} />
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>

        {/* Right Side Actions */}
        <HStack spacing={2}>
          {/* Help Menu */}
          <Menu>
            <MenuButton
              as={IconButton}
              aria-label="Help"
              icon={<InfoIcon />}
              variant="ghost"
              display={{ base: 'none', md: 'flex' }}
            />
            <MenuList>
              <MenuItem as="a" href="/links/" target="_blank">
                Resources & Links <ExternalLinkIcon ml={2} />
              </MenuItem>
              <MenuItem as="a" href="/contact/" target="_blank">
                Contact Us <ExternalLinkIcon ml={2} />
              </MenuItem>
              <MenuItem as="a" href="/bug-report/" target="_blank">
                Report a Bug <ExternalLinkIcon ml={2} />
              </MenuItem>
              <MenuDivider />
              <MenuItem as="a" href="https://github.com/kartoza/django-bims" target="_blank">
                GitHub <ExternalLinkIcon ml={2} />
              </MenuItem>
            </MenuList>
          </Menu>

          {/* User Menu / Login */}
          <Menu>
            <MenuButton
              as={Button}
              variant="outline"
              size="sm"
              colorScheme="brand"
              display={{ base: 'none', md: 'flex' }}
            >
              Account
            </MenuButton>
            <MenuList>
              <MenuItem as="a" href="/accounts/login/">
                Sign In
              </MenuItem>
              <MenuItem as="a" href="/accounts/signup/">
                Register
              </MenuItem>
              <MenuDivider />
              <MenuItem as="a" href="/profile/">
                My Profile
              </MenuItem>
            </MenuList>
          </Menu>

          {/* Mobile Menu Button */}
          <IconButton
            aria-label="Open menu"
            icon={<HamburgerIcon />}
            variant="ghost"
            display={{ base: 'flex', md: 'none' }}
            onClick={onOpen}
          />
        </HStack>
      </Flex>

      {/* Mobile Drawer */}
      <Drawer isOpen={isOpen} placement="right" onClose={onClose} size="xs">
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth={1}>Menu</DrawerHeader>
          <DrawerBody>
            <VStack spacing={4} align="stretch" mt={4}>
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  as={RouterLink}
                  to={link.to}
                  py={2}
                  fontWeight={isActivePath(link.to) ? '600' : '400'}
                  color={isActivePath(link.to) ? 'brand.600' : 'gray.700'}
                  onClick={onClose}
                >
                  {link.label}
                </Link>
              ))}

              <Text fontWeight="600" color="gray.500" fontSize="sm" mt={4}>
                Data
              </Text>
              <Link as="a" href="/upload/" py={1}>
                Upload Data
              </Link>
              <Link as="a" href="/download-request/" py={1}>
                Download Requests
              </Link>
              <Link as="a" href="/source-references/" py={1}>
                Source References
              </Link>

              <Text fontWeight="600" color="gray.500" fontSize="sm" mt={4}>
                Admin
              </Text>
              <Link as="a" href="/admin/" py={1}>
                Django Admin
              </Link>
              <Link as="a" href="/taxa-management/" py={1}>
                Taxa Management
              </Link>
              <Link as="a" href="/site-visit/list/" py={1}>
                Site Visits
              </Link>

              <Text fontWeight="600" color="gray.500" fontSize="sm" mt={4}>
                Account
              </Text>
              <Link as="a" href="/accounts/login/" py={1}>
                Sign In
              </Link>
              <Link as="a" href="/accounts/signup/" py={1}>
                Register
              </Link>
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};

export default Header;
