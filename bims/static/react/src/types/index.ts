/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Type definitions for BIMS React frontend.
 */

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  meta: Record<string, unknown> | null;
  errors: Record<string, unknown> | string | null;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  meta: {
    count: number;
    page: number;
    page_size: number;
    total_pages: number;
    next: string | null;
    previous: string | null;
  };
  errors: null;
}

// Location Site Types
export interface LocationType {
  id: number;
  name: string;
  description: string;
  allowed_geometry: string;
}

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface LocationSite {
  id: number;
  name: string;
  site_code: string;
  site_description: string;
  geometry: string | null;
  location_type: LocationType | null;
  river_name: string | null;
  ecosystem_type: string | null;
  wetland_name: string | null;
  owner_name: string | null;
  validated: boolean;
  created: string;
  modified: string;
}

export interface LocationSiteDetail extends LocationSite {
  location_context: Record<string, unknown>;
  coordinates: Coordinates | null;
  climate_data: Record<string, unknown> | null;
  refined_geomorphological: string | null;
  original_geomorphological: string | null;
  land_owner_detail: string | null;
  map_reference: string | null;
  additional_data: Record<string, unknown> | null;
}

// Taxonomy Types
export interface IUCNStatus {
  id: number;
  category: string;
  sensitive: boolean;
}

export interface Endemism {
  id: number;
  name: string;
  description: string;
}

export interface Taxonomy {
  id: number;
  scientific_name: string;
  canonical_name: string;
  rank: string;
  taxonomic_status: string;
  iucn_status: IUCNStatus | null;
  national_conservation_status: IUCNStatus | null;
  endemism: Endemism | null;
  common_name: string | null;
  gbif_key: number | null;
  verified: boolean;
  record_count: number | null;
}

export interface TaxonomyDetail extends Taxonomy {
  parent: {
    id: number;
    scientific_name: string;
    canonical_name: string;
    rank: string;
  } | null;
  vernacular_names: Array<{
    id: number;
    name: string;
    language: string;
  }>;
  tags: string[];
  biographic_distributions: Array<{
    name: string;
    doubtful: boolean;
  }>;
  hierarchy: Array<{
    id: number;
    name: string;
    rank: string;
  }>;
  images: Array<{
    id: number;
    url: string | null;
  }>;
}

// Biological Collection Record Types
export interface BiologicalCollectionRecord {
  id: number;
  uuid: string;
  site_name: string;
  site_code: string;
  taxon_name: string;
  taxon_rank: string;
  original_species_name: string;
  collection_date: string;
  collector_name: string | null;
  abundance_number: number | null;
  present: boolean;
  validated: boolean;
  coordinates: Coordinates | null;
  notes: string;
  created: string;
  modified: string;
}

// Taxon Group Types
export interface TaxonGroup {
  id: number;
  name: string;
  singular_name: string;
  category: string;
  display_order: number;
  parent_name: string | null;
  taxa_count: number;
  logo_url: string | null;
  extra_attributes: Record<string, unknown>;
}

// Survey Types
export interface Survey {
  id: number;
  uuid: string;
  site_name: string;
  site_code: string;
  date: string;
  collector_string: string;
  record_count: number;
  validation_status: string;
  validated: boolean;
  created: string;
  modified: string;
}

// Source Reference Types
export interface SourceReference {
  id: number;
  title: string | null;
  authors: string | null;
  year: number | null;
  reference_type: string;
  url: string | null;
  note: string;
  source_name: string;
}

// Boundary Types
export interface Boundary {
  id: number;
  name: string;
  code_name: string;
  type: string;
  geometry: string | null;
}

export interface UserBoundary {
  id: number;
  name: string;
  geometry: string | null;
  owner_name: string | null;
  created: string;
  modified: string;
}

// Filter Types
export interface SearchFilters {
  bbox?: string | null;
  search?: string;
  taxonGroups?: number[];
  taxon_name?: string;
  site_name?: string;
  site_code?: string;
  yearFrom?: number;
  yearTo?: number;
  validated?: boolean;
  iucnCategories?: string[];
  endemism?: string[];
  ecosystemType?: string;
  collectors?: string[];
  boundaryId?: number | null;
  // New filter types
  referenceCategories?: string[];
  sourceCollections?: string[];  // Source names like 'fbis', 'gbif', 'virtual_museum'
  gbifDatasets?: string[];
  [key: string]: string | number | boolean | string[] | number[] | null | undefined;
}

// Alias for backward compatibility
export type BiologicalRecord = BiologicalCollectionRecord & {
  latitude?: number;
  longitude?: number;
  iucn_status?: string;
};

// Map Types
export interface MapState {
  center: [number, number];
  zoom: number;
  selectedSiteId: number | null;
  selectedRecordId: number | null;
  visibleLayers: string[];
  drawMode: 'none' | 'point' | 'polygon' | 'line';
}

// UI Types
export interface PanelState {
  isOpen: boolean;
  activePanel: 'search' | 'site' | 'taxon' | 'record' | null;
  selectedId: number | null;
}

// Task Status Types
export interface TaskStatus {
  task_id: string;
  status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'REVOKED';
  ready: boolean;
  result?: Record<string, unknown>;
  error?: string;
  progress?: number;
}
