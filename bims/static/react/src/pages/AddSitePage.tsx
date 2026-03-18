/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Add Location Site form page.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useRef, useEffect } from 'react';
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
  Button,
  Input,
  FormControl,
  FormLabel,
  FormHelperText,
  FormErrorMessage,
  Select,
  Textarea,
  NumberInput,
  NumberInputField,
  useToast,
  Flex,
  Grid,
  GridItem,
  Divider,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { useNavigate, useParams } from 'react-router-dom';
import { sitesApi, api } from '../api/client';
import maplibregl from 'maplibre-gl';

interface SiteFormData {
  site_code: string;
  name: string;
  description: string;
  latitude: number;
  longitude: number;
  river_name: string;
  ecosystem_type: string;
  wetland_name?: string;
  refined_geomorphological_zone?: string;
  original_geomorphological_zone?: string;
}

const AddSitePage: React.FC = () => {
  const { type = 'site' } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  const [formData, setFormData] = useState<SiteFormData>({
    site_code: '',
    name: '',
    description: '',
    latitude: -29.0,
    longitude: 24.5,
    river_name: '',
    ecosystem_type: 'river',
    wetland_name: '',
    refined_geomorphological_zone: '',
    original_geomorphological_zone: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const isWetland = type === 'wetland';

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: [
              'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
            ],
            tileSize: 256,
          },
        },
        layers: [
          {
            id: 'osm-tiles-layer',
            type: 'raster',
            source: 'osm-tiles',
          },
        ],
      },
      center: [formData.longitude, formData.latitude],
      zoom: 6,
    });

    map.addControl(new maplibregl.NavigationControl());

    // Add marker
    const marker = new maplibregl.Marker({ draggable: true })
      .setLngLat([formData.longitude, formData.latitude])
      .addTo(map);

    marker.on('dragend', () => {
      const lngLat = marker.getLngLat();
      setFormData((prev) => ({
        ...prev,
        longitude: parseFloat(lngLat.lng.toFixed(6)),
        latitude: parseFloat(lngLat.lat.toFixed(6)),
      }));
    });

    // Click to place marker
    map.on('click', (e) => {
      marker.setLngLat(e.lngLat);
      setFormData((prev) => ({
        ...prev,
        longitude: parseFloat(e.lngLat.lng.toFixed(6)),
        latitude: parseFloat(e.lngLat.lat.toFixed(6)),
      }));
    });

    mapRef.current = map;
    markerRef.current = marker;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update marker when coordinates change manually
  useEffect(() => {
    if (markerRef.current && mapRef.current) {
      markerRef.current.setLngLat([formData.longitude, formData.latitude]);
      mapRef.current.flyTo({
        center: [formData.longitude, formData.latitude],
        zoom: 10,
      });
    }
  }, [formData.latitude, formData.longitude]);

  const handleChange = (field: keyof SiteFormData, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.site_code) {
      newErrors.site_code = 'Site code is required';
    }
    if (!formData.name) {
      newErrors.name = 'Site name is required';
    }
    if (formData.latitude < -90 || formData.latitude > 90) {
      newErrors.latitude = 'Latitude must be between -90 and 90';
    }
    if (formData.longitude < -180 || formData.longitude > 180) {
      newErrors.longitude = 'Longitude must be between -180 and 180';
    }
    if (!formData.ecosystem_type) {
      newErrors.ecosystem_type = 'Ecosystem type is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors before submitting',
        status: 'error',
        duration: 5000,
      });
      return;
    }

    setSubmitting(true);

    try {
      const response = await sitesApi.create({
        ...formData,
        geometry: {
          type: 'Point',
          coordinates: [formData.longitude, formData.latitude],
        },
      });

      toast({
        title: 'Site Created',
        description: `Site "${formData.name}" has been created successfully`,
        status: 'success',
        duration: 5000,
      });

      navigate(`/map/site/${response.data.id}`);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create site',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const ecosystemTypes = [
    { value: 'river', label: 'River' },
    { value: 'wetland', label: 'Wetland' },
    { value: 'estuary', label: 'Estuary' },
    { value: 'dam', label: 'Dam' },
    { value: 'lake', label: 'Lake' },
  ];

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>
            {isWetland ? 'Add Wetland Site' : 'Add Location Site'}
          </Heading>
          <Text color="gray.600">
            {isWetland
              ? 'Create a new wetland monitoring site'
              : 'Create a new location site for biodiversity monitoring'}
          </Text>
        </Box>

        <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={6}>
          {/* Form */}
          <Card>
            <CardHeader>
              <Heading size="md">Site Details</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Grid templateColumns="1fr 1fr" gap={4}>
                  <FormControl isRequired isInvalid={!!errors.site_code}>
                    <FormLabel>Site Code</FormLabel>
                    <Input
                      value={formData.site_code}
                      onChange={(e) => handleChange('site_code', e.target.value)}
                      placeholder="e.g., RSITE001"
                    />
                    <FormErrorMessage>{errors.site_code}</FormErrorMessage>
                  </FormControl>

                  <FormControl isRequired isInvalid={!!errors.ecosystem_type}>
                    <FormLabel>Ecosystem Type</FormLabel>
                    <Select
                      value={formData.ecosystem_type}
                      onChange={(e) => handleChange('ecosystem_type', e.target.value)}
                    >
                      {ecosystemTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </Select>
                    <FormErrorMessage>{errors.ecosystem_type}</FormErrorMessage>
                  </FormControl>
                </Grid>

                <FormControl isRequired isInvalid={!!errors.name}>
                  <FormLabel>Site Name</FormLabel>
                  <Input
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="Enter site name"
                  />
                  <FormErrorMessage>{errors.name}</FormErrorMessage>
                </FormControl>

                <FormControl>
                  <FormLabel>River Name</FormLabel>
                  <Input
                    value={formData.river_name}
                    onChange={(e) => handleChange('river_name', e.target.value)}
                    placeholder="e.g., Orange River"
                  />
                </FormControl>

                {isWetland && (
                  <FormControl>
                    <FormLabel>Wetland Name</FormLabel>
                    <Input
                      value={formData.wetland_name}
                      onChange={(e) => handleChange('wetland_name', e.target.value)}
                      placeholder="Enter wetland name"
                    />
                  </FormControl>
                )}

                <FormControl>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => handleChange('description', e.target.value)}
                    placeholder="Describe the site..."
                    rows={3}
                  />
                </FormControl>

                <Divider />

                <Heading size="sm">Coordinates</Heading>

                <Alert status="info" rounded="md">
                  <AlertIcon />
                  <Text fontSize="sm">
                    Click on the map or drag the marker to set the site location
                  </Text>
                </Alert>

                <Grid templateColumns="1fr 1fr" gap={4}>
                  <FormControl isRequired isInvalid={!!errors.latitude}>
                    <FormLabel>Latitude</FormLabel>
                    <NumberInput
                      value={formData.latitude}
                      onChange={(_, value) => handleChange('latitude', value)}
                      precision={6}
                      step={0.001}
                      min={-90}
                      max={90}
                    >
                      <NumberInputField />
                    </NumberInput>
                    <FormHelperText>Decimal degrees (e.g., -33.9249)</FormHelperText>
                    <FormErrorMessage>{errors.latitude}</FormErrorMessage>
                  </FormControl>

                  <FormControl isRequired isInvalid={!!errors.longitude}>
                    <FormLabel>Longitude</FormLabel>
                    <NumberInput
                      value={formData.longitude}
                      onChange={(_, value) => handleChange('longitude', value)}
                      precision={6}
                      step={0.001}
                      min={-180}
                      max={180}
                    >
                      <NumberInputField />
                    </NumberInput>
                    <FormHelperText>Decimal degrees (e.g., 18.4241)</FormHelperText>
                    <FormErrorMessage>{errors.longitude}</FormErrorMessage>
                  </FormControl>
                </Grid>

                <HStack justify="flex-end" pt={4}>
                  <Button variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button
                    colorScheme="brand"
                    onClick={handleSubmit}
                    isLoading={submitting}
                  >
                    Create Site
                  </Button>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Map */}
          <Card>
            <CardHeader>
              <Heading size="md">Site Location</Heading>
            </CardHeader>
            <CardBody p={0}>
              <Box
                ref={mapContainer}
                h="500px"
                w="100%"
                borderBottomRadius="md"
              />
            </CardBody>
          </Card>
        </Grid>
      </VStack>
    </Container>
  );
};

export default AddSitePage;
