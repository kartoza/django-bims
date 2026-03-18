# BIMS - Biodiversity Information Management System

## Specification Document

**Version**: 2.0.0
**Last Updated**: 2026-03-17

Made with love by [Kartoza](https://kartoza.com) | [Donate](https://github.com/sponsors/kartoza) | [GitHub](https://github.com/kartoza/django-bims)

---

## 1. Executive Summary

BIMS (Biodiversity Information Management System) is a comprehensive platform for managing, visualizing, and analyzing biodiversity data. The system enables researchers, conservation agencies, and citizen scientists to record, validate, and explore biological observations across geographic regions.

### Key Capabilities

- **Data Collection**: Record biological observations with taxonomic, spatial, and temporal metadata
- **Visualization**: Interactive map interface with clustering, filtering, and detailed site/taxon views
- **Analytics**: Conservation status charts, endemism analysis, and biodiversity dashboards
- **Data Export**: CSV downloads, checklists, and GIS data exports
- **API Access**: RESTful API and MCP (Model Context Protocol) server for AI integration
- **Multi-tenancy**: Support for multiple independent biodiversity portals

---

## 2. System Architecture

### 2.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django 5.x |
| API Framework | Django REST Framework |
| Database | PostgreSQL with PostGIS |
| Task Queue | Celery + Redis/RabbitMQ |
| Frontend (Legacy) | Backbone.js + RequireJS |
| Frontend (New) | React 18 + TypeScript + Chakra UI |
| Map Library | MapLibre GL JS |
| Build Tools | Webpack |
| MCP Server | Python + mcp library |

### 2.2 Module Structure

```
bims/
├── api/                    # API endpoints (legacy)
│   └── v1/                 # Versioned API (new)
│       ├── viewsets/       # DRF ViewSets
│       ├── serializers/    # API serializers
│       ├── filters/        # Filter backends
│       └── urls.py         # Router configuration
├── models/                 # Django models
├── static/
│   └── react/             # New React frontend
│       └── src/
│           ├── components/ # UI components
│           ├── pages/      # Page components
│           ├── stores/     # Zustand stores
│           ├── api/        # API client
│           └── types/      # TypeScript types
└── templates/             # Django templates

mcp_bims/                   # MCP Server
├── server.py              # Main server
├── tools/                 # MCP tools
├── clients/               # API clients
└── schemas/               # Pydantic schemas
```

---

## 3. Data Models

### 3.1 Core Entities

#### LocationSite
Represents a geographic sampling location.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String | Site name |
| site_code | String | Unique site identifier |
| geometry | Point/Polygon | Geographic location |
| location_type | ForeignKey | Type of location |
| ecosystem_type | String | Ecosystem classification |
| river_name | String | Associated river (optional) |
| validated | Boolean | Validation status |

#### Taxonomy
Taxonomic classification of species.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| scientific_name | String | Full scientific name |
| canonical_name | String | Name without author |
| rank | String | Taxonomic rank |
| iucn_status | ForeignKey | IUCN conservation status |
| endemism | ForeignKey | Endemism classification |
| parent | ForeignKey | Parent taxon |
| gbif_key | Integer | GBIF species key |

#### BiologicalCollectionRecord
Individual species observation records.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| uuid | UUID | Unique identifier |
| site | ForeignKey | Location site |
| taxonomy | ForeignKey | Species identification |
| collection_date | Date | Observation date |
| collector | ForeignKey | Observer/collector |
| abundance_number | Integer | Count or abundance |
| validated | Boolean | Validation status |

#### Survey (SiteVisit)
Grouping of observations from a single sampling event.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| site | ForeignKey | Location site |
| date | Date | Survey date |
| collector_string | String | Collector name(s) |
| validated | Boolean | Validation status |

### 3.2 Supporting Entities

- **TaxonGroup**: Module/category for organizing taxa (e.g., Fish, Invertebrates)
- **SourceReference**: Literature or data source citations
- **Boundary**: Administrative or ecological boundary polygons
- **UserBoundary**: User-defined geographic boundaries

---

## 4. API Specification

### 4.1 API Versioning

- Legacy API: `/api/` (unchanged for backward compatibility)
- New API: `/api/v1/` (RESTful, consistent response format)

### 4.2 Response Format

All v1 API responses follow this structure:

```json
{
  "success": true,
  "data": {...},
  "meta": {
    "count": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "next": "...",
    "previous": "..."
  },
  "errors": null
}
```

### 4.3 Endpoints

#### Location Sites
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sites/` | List sites with pagination and filters |
| GET | `/api/v1/sites/{id}/` | Get site details |
| POST | `/api/v1/sites/` | Create new site |
| PATCH | `/api/v1/sites/{id}/` | Update site |
| DELETE | `/api/v1/sites/{id}/` | Delete site |
| GET | `/api/v1/sites/nearby/` | Find nearby sites |
| GET | `/api/v1/sites/{id}/records/` | Get site's biological records |
| POST | `/api/v1/sites/{id}/validate/` | Validate a site |

#### Biological Records
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/records/` | List records with filters |
| GET | `/api/v1/records/{id}/` | Get record details |
| GET | `/api/v1/records/search/` | Advanced search |
| GET | `/api/v1/records/summary/` | Get summary statistics |

#### Taxonomy
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/taxa/` | List taxa |
| GET | `/api/v1/taxa/{id}/` | Get taxon details |
| GET | `/api/v1/taxa/find/` | Autocomplete search |
| GET | `/api/v1/taxa/{id}/tree/` | Get taxonomic hierarchy |
| GET | `/api/v1/taxa/{id}/records/` | Get taxon's records |

#### Taxon Groups
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/taxon-groups/` | List modules |
| GET | `/api/v1/taxon-groups/{id}/` | Get module details |
| GET | `/api/v1/taxon-groups/summary/` | Get module statistics |

#### Surveys
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/surveys/` | List surveys |
| GET | `/api/v1/surveys/{id}/` | Get survey details |
| POST | `/api/v1/surveys/{id}/validate/` | Validate survey |
| POST | `/api/v1/surveys/{id}/reject/` | Reject survey |
| POST | `/api/v1/surveys/bulk/validate/` | Bulk validate |

#### Downloads
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/downloads/csv/` | Request CSV download |
| POST | `/api/v1/downloads/checklist/` | Request checklist |
| GET | `/api/v1/tasks/{task_id}/` | Check task status |

### 4.4 Filter Parameters

Common filter parameters across list endpoints:

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| page_size | integer | Results per page |
| search | string | Full-text search |
| bbox | string | Bounding box (west,south,east,north) |
| year_from | integer | Filter from year |
| year_to | integer | Filter to year |
| validated | boolean | Validation status |
| taxon_group | integer | Taxon module ID |
| iucn_category | string | Conservation status |
| endemism | string | Endemism classification |

---

## 5. Frontend Specification

### 5.1 URL Structure

| URL | Component | Description |
|-----|-----------|-------------|
| `/map/` | Backbone App | Legacy map interface |
| `/new/` | React App | New map interface |
| `/new/map/` | MapPage | Interactive map |
| `/new/site/:id` | SiteDetail | Site dashboard |
| `/new/taxon/:id` | TaxonDetail | Taxon dashboard |

### 5.2 Component Architecture

```
App
├── AppProvider (Chakra, React Query)
├── MapLayout
│   ├── Header
│   ├── MapPage
│   │   ├── MapContainer (MapLibre)
│   │   ├── MapControls
│   │   ├── SearchPanel
│   │   │   ├── TaxonGroupFilter
│   │   │   ├── DateRangeFilter
│   │   │   ├── ConservationStatusFilter
│   │   │   ├── EndemismFilter
│   │   │   ├── CollectorFilter
│   │   │   └── SpatialFilter
│   │   ├── SiteDetailPanel
│   │   └── TaxonDetailPanel
│   └── Footer
```

### 5.3 Map Features

- **Base Maps**: OpenStreetMap tiles
- **Clustering**: Automatic point clustering at zoom levels < 14
- **Layers**: Sites, records, boundaries
- **Interactions**: Click to select, hover highlighting
- **Controls**: Zoom, scale, geolocation

### 5.4 Search Filters

| Filter | Type | Description |
|--------|------|-------------|
| Taxon Group | Multi-select | Filter by biodiversity module |
| Date Range | Range slider | Year from/to |
| Conservation Status | Multi-select | IUCN categories |
| Endemism | Multi-select | Endemism classification |
| Collector | Autocomplete | Collector name |
| Spatial | Boundary select | Administrative boundary |

---

## 6. MCP Server Specification

### 6.1 Overview

The MCP (Model Context Protocol) server enables AI assistants to interact with BIMS data through standardized tools and resources.

### 6.2 Resources

| URI | Name | Description |
|-----|------|-------------|
| `bims://modules` | BIMS Modules | Available taxon groups |
| `bims://conservation-statuses` | Conservation Statuses | IUCN categories |
| `bims://ecosystem-types` | Ecosystem Types | Available ecosystems |
| `bims://site/{id}` | Location Site | Dynamic site resource |
| `bims://taxon/{id}` | Taxon | Dynamic taxon resource |
| `bims://record/{id}` | Biological Record | Dynamic record resource |

### 6.3 Tools

#### Location Sites
- `list_location_sites` - List sites with filters
- `get_location_site` - Get site details
- `get_nearby_sites` - Find nearby sites
- `get_site_by_coordinates` - Find site at coordinates
- `create_location_site` - Create new site
- `merge_sites` - Merge duplicate sites
- `get_site_surveys` - Get site surveys
- `get_site_records` - Get site records

#### Biological Records
- `list_biological_records` - List records
- `get_biological_record` - Get record details
- `search_biological_records` - Advanced search
- `get_records_by_site` - Records grouped by site
- `get_records_by_taxon` - Records grouped by taxon
- `get_records_summary` - Summary statistics

#### Taxonomy
- `list_taxa` - List taxa
- `get_taxon` - Get taxon details
- `find_taxon` - Autocomplete search
- `get_taxon_tree` - Taxonomic hierarchy
- `get_taxon_images` - Taxon images
- `list_taxon_groups` - List modules
- `get_taxon_records` - Taxon's records

#### Analytics
- `get_module_summary` - Module statistics
- `get_site_summary` - Site statistics
- `get_conservation_status_chart` - Conservation data
- `get_endemism_chart` - Endemism data
- `request_csv_download` - Request CSV export
- `request_checklist_download` - Request checklist
- `get_download_status` - Check task status

#### Validation
- `validate_site_visit` - Validate survey
- `reject_site_visit` - Reject survey
- `get_pending_validations` - List pending
- `bulk_validate` - Bulk validation
- `bulk_reject` - Bulk rejection
- `validate_taxon` - Validate taxon
- `reject_taxon` - Reject taxon
- `get_validation_summary` - Validation stats

---

## 7. User Stories

### 7.1 Data Discovery

**US-001**: As a researcher, I want to search for species occurrences by name so that I can find relevant biodiversity data.

**Acceptance Criteria**:
- Search box accepts species names (scientific and common)
- Results show matching records with location and date
- Click on result navigates to record detail

**US-002**: As a conservation planner, I want to filter records by IUCN status so that I can focus on threatened species.

**Acceptance Criteria**:
- Filter panel shows all IUCN categories
- Multiple categories can be selected
- Results update immediately
- Map markers reflect filtered data

### 7.2 Data Entry

**US-003**: As a field researcher, I want to add new observation records so that my data contributes to the database.

**Acceptance Criteria**:
- Form validates required fields
- Location can be set via map click
- Taxon lookup with autocomplete
- Confirmation message on success

### 7.3 Data Validation

**US-004**: As a data manager, I want to validate submitted records so that data quality is maintained.

**Acceptance Criteria**:
- List of pending records shown
- Bulk selection available
- Validate/reject with comments
- Email notification to submitter

### 7.4 Data Export

**US-005**: As a GIS analyst, I want to download occurrence data as CSV so that I can analyze it in external tools.

**Acceptance Criteria**:
- Export button available on search results
- Filter applied to export
- Progress indicator for large exports
- Download link provided when ready

---

## 8. Business Rules

### 8.1 Validation Rules

- **BR-001**: Records require valid taxonomy reference
- **BR-002**: Collection date cannot be in the future
- **BR-003**: Coordinates must be within valid ranges
- **BR-004**: Site codes must be unique within tenant

### 8.2 Access Control

- **BR-005**: Anonymous users can view validated data only
- **BR-006**: Authenticated users can submit records
- **BR-007**: Data managers can validate/reject records
- **BR-008**: Administrators can manage users and settings

### 8.3 Data Integrity

- **BR-009**: Deleting a site cascades to orphan records
- **BR-010**: Taxonomic changes propagate to related records
- **BR-011**: Validation status affects data visibility

---

## 9. Functional Requirements

### 9.1 Map Interface

- **FR-001**: Display interactive map with base layer
- **FR-002**: Show location sites as clustered markers
- **FR-003**: Support zoom levels 2-18
- **FR-004**: Enable marker click for site details
- **FR-005**: Support bounding box selection
- **FR-006**: Display scale bar and attribution

### 9.2 Search and Filter

- **FR-007**: Full-text search across records
- **FR-008**: Filter by taxon group
- **FR-009**: Filter by date range
- **FR-010**: Filter by conservation status
- **FR-011**: Filter by geographic boundary
- **FR-012**: Combine multiple filters with AND logic

### 9.3 Detail Views

- **FR-013**: Display site overview with location info
- **FR-014**: Show site's biological records
- **FR-015**: Display taxon hierarchy
- **FR-016**: Show taxon images when available
- **FR-017**: List vernacular names

### 9.4 API

- **FR-018**: RESTful endpoints for all resources
- **FR-019**: Pagination for list endpoints
- **FR-020**: Standardized error responses
- **FR-021**: Authentication via token
- **FR-022**: Rate limiting for public access

---

## 10. Non-Functional Requirements

### 10.1 Performance

- **NFR-001**: Page load under 3 seconds
- **NFR-002**: API response under 500ms for simple queries
- **NFR-003**: Support 100 concurrent users
- **NFR-004**: Handle 1M+ records efficiently

### 10.2 Security

- **NFR-005**: HTTPS required for all endpoints
- **NFR-006**: SQL injection prevention
- **NFR-007**: XSS protection
- **NFR-008**: CSRF tokens for forms
- **NFR-009**: Sensitive data encryption at rest

### 10.3 Accessibility

- **NFR-010**: WCAG 2.1 AA compliance
- **NFR-011**: Keyboard navigation support
- **NFR-012**: Screen reader compatibility

### 10.4 Compatibility

- **NFR-013**: Modern browser support (Chrome, Firefox, Safari, Edge)
- **NFR-014**: Responsive design for mobile devices
- **NFR-015**: API versioning for backward compatibility

---

## 11. Testing Requirements

### 11.1 Unit Tests

- Model validation logic
- Serializer transformations
- Filter backend behavior
- Utility functions

### 11.2 Integration Tests

- API endpoint behavior
- Database transactions
- Celery task execution
- External service integration

### 11.3 End-to-End Tests

- User workflows
- Map interactions
- Search and filter operations
- Data export process

---

## 12. Documentation Requirements

### 12.1 User Documentation

- Getting started guide
- Feature tutorials
- FAQ section

### 12.2 Administrator Documentation

- Installation guide
- Configuration reference
- Backup procedures
- Troubleshooting guide

### 12.3 Developer Documentation

- Architecture overview
- API reference
- Contribution guidelines
- Code style guide

---

## Changelog

### Version 2.0.0 (2026-03-17)

- Added new `/api/v1/` REST API with ViewSets
- Added React + Chakra UI frontend at `/new/`
- Added MapLibre GL JS map integration
- Added MCP server for AI assistant integration
- Maintained backward compatibility with legacy frontend and API
