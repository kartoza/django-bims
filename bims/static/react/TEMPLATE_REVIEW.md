# Django Template to React Page Review Tracker

This document tracks the review of Django templates against their React implementations to ensure feature parity.

**Legend:**
- **Status**: `Not Started` | `In Progress` | `Reviewed` | `N/A` (not applicable for React)
- **Human Verified**: To be marked by human reviewer after testing

---

## Core User-Facing Pages

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `landing_page.html` | `LandingPage.tsx` | Reviewed | See detailed notes below | [ ] |
| `landing_page_fbis.html` | `LandingPage.tsx` | Reviewed | ~70% complete, missing theme/CMS | [ ] |
| `landing_page_dashboard.html` | `LandingPage.tsx` | Not Started | Dashboard variant | [ ] |
| `landing_page_dashboard_fbis.html` | `LandingPage.tsx` | Not Started | FBIS dashboard variant | [ ] |
| `map_page/bims.html` | `MapPage.tsx` | Reviewed | ~90% complete, missing config modals | [ ] |
| `summary_report.html` | `SummaryReportPage.tsx` | Reviewed | ~87% complete, missing nested reports | [ ] |

### landing_page.html - Detailed Review

**Django Template Features:**
1. Carousel/Header with customizable banners
2. Biodiversity data section with themed title
3. General Summary: Occurrences, Taxa, Users, Uploads, Downloads
4. FADA site variant with organism groups
5. Custom landing page sections (CMS-driven)
6. Funders/Partners section with logos
7. Footer with logo, social links, contact info

**React Implementation Status:**
- [x] Hero section (static, not carousel)
- [x] Stats section (Sites, Records, Taxa, Contributors)
- [x] Feature cards (Search, Visualize, Contribute, Download)
- [x] Ecosystems section (Rivers, Wetlands, etc.)
- [x] Taxon Groups section (dynamic from API)
- [x] CTA section

**Missing/Incomplete:**
- [ ] **Carousel support** - Django uses customizable carousels
- [ ] **Theme customization** - No API for theme colors/fonts
- [ ] **Funders/Partners section** - Not implemented
- [ ] **User Uploads/Downloads counts** - Only basic stats
- [ ] **Custom CMS sections** - No support for dynamic content blocks
- [ ] **Footer contact info** - Uses React app footer instead

### landing_page_fbis.html - Detailed Review

**Django Template Features:**
1. Hero/Header section with optional carousel or static header
2. Authentication-dependent buttons (Login/Sign Up/Explore)
3. "Coming soon" indicator based on site_ready flag
4. Platform overview stats (Occurrences, Taxa, Users, Uploads, Downloads)
5. Custom landing page sections (CMS-driven with dynamic content)
6. Funders/Partners section with logo grids
7. Footer with contact info (email, phone, addresses)
8. Social media links (Twitter, Facebook, Instagram)
9. Chart.js integration for data visualization
10. About section with navigation links and partner logos

**React Implementation Status:**
- [x] Hero section with glassmorphism backdrop
- [x] Call-to-action buttons (Explore Map, Get Started)
- [x] Platform stats (4 stats: Sites, Records, Taxa, Contributors)
- [x] Features section (4 feature cards)
- [x] Ecosystem types section
- [x] Taxon groups section (dynamic from API)
- [x] Responsive design with Chakra UI

**Missing/Incomplete:**
- [ ] **Carousel support** - Static hero only
- [ ] **Theme customization** - No API for colors/fonts/logo
- [ ] **Custom CMS sections** - No dynamic content blocks
- [ ] **Funders/Partners logos** - Not implemented
- [ ] **Footer with contact info** - No footer section
- [ ] **Social media links** - Not shown
- [ ] **Authentication conditional buttons** - Same buttons for all users
- [ ] **Chart.js visualization** - No charts
- [ ] **Site ready status** - Not checked

### map_page/bims.html - Detailed Review

**Django Template Features:**
1. Global JS config (date bounds, basemaps, API keys, URLs)
2. User permissions (can validate, is staff, is superuser)
3. Map container with OpenLayers 9.2.4
4. General info modal (flatpage content, don't show again)
5. Print error modal
6. Template includes (map, search-panel, side-panel, dashboard)
7. Feature flags (SASS, water temp, climate, pesticide)
8. Geoserver config (layers, clustering)
9. Multi-resolution map support
10. Complex filter URL parameter handling

**React Implementation Status:**
- [x] DeckGL map with multiple basemap styles
- [x] Map controls (zoom, export, layers)
- [x] Search panel with filter integration
- [x] Site/Taxon detail panels
- [x] 3D map toggle with URL persistence
- [x] Full URL state management (lat, lng, z, filters)
- [x] IndexedDB caching with version validation
- [x] Global and viewport point loading
- [x] Fly-to navigation
- [x] Context layers via WMS

**Missing/Incomplete:**
- [ ] **General info modal** - No first-visit modal
- [ ] **Print error modal** - No print error handling
- [ ] **Feature flags from server** - Hardcoded in React
- [ ] **User validation permissions in UI** - Not reflected
- [ ] **Edit functionality** - Detail panels are view-only
- [ ] **Bulk actions** - No bulk selection
- [ ] **Site visit creation from map** - Not implemented

### summary_report.html - Detailed Review

**Django Template Features:**
1. General Data Report (/api/summary-general-report/)
2. Location Context Report (/api/location-context-report/)
3. Background process monitoring (Celery task status)
4. Collapsible report panels
5. Recursive nested object to table rendering
6. Duplicate records download button
7. Email notification for download requests
8. Number formatting (numberWithCommas)

**React Implementation Status:**
- [x] System statistics display (6 stats grid)
- [x] Loading state with skeleton loaders
- [x] Summary data fetching from API
- [x] Cached data indicator
- [x] Report generation (CSV, Checklist)
- [x] Taxon group selection for reports
- [x] Progress tracking with polling
- [x] Download requests table with status
- [x] Delete downloads with confirmation
- [x] Taxa list download modal
- [x] Module statistics card

**Missing/Incomplete:**
- [ ] **Location Context Report** - Second report not shown
- [ ] **Background process monitoring** - Celery tasks not displayed
- [ ] **Collapsible report sections** - Uses cards instead
- [ ] **Nested object table rendering** - Flat stats only
- [ ] **Duplicate records download** - Not implemented

---

## Authentication & Account Pages

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `account/login.html` | `LoginPage.tsx` | Reviewed | Core auth works, missing OAuth | [ ] |
| `account/signup.html` | `RegisterPage.tsx` | Reviewed | Good validation, missing reCAPTCHA | [ ] |
| `account/logout.html` | N/A | N/A | Handled by auth provider | [ ] |
| `account/password_reset.html` | `LoginPage.tsx` | Not Started | Password reset flow | [ ] |
| `account/password_reset_done.html` | N/A | N/A | Redirect/message only | [ ] |
| `account/password_reset_from_key.html` | N/A | Not Started | Reset from email link | [ ] |
| `account/password_change.html` | `ProfilePage.tsx` | Reviewed | Modal-based change works | [ ] |
| `account/email_confirm.html` | N/A | N/A | Email verification | [ ] |
| `account/verification_sent.html` | N/A | N/A | Confirmation message | [ ] |
| `account/email.html` | `ProfilePage.tsx` | Not Started | Email management | [ ] |

### account/login.html - Detailed Review

**Django Template Features:**
1. Custom theme support for login modal logo/title
2. Django form auto-rendering with `form.as_p`
3. CSRF token protection
4. Redirect field for post-login navigation
5. Google and GitHub OAuth buttons (JavaScript)
6. Bootstrap 3.3.5 styling
7. jQuery/Chosen dependencies

**React Implementation Status:**
- [x] Username/password input fields
- [x] Form validation (client-side)
- [x] Error handling and display
- [x] Password visibility toggle
- [x] Forgot password link
- [x] Sign-up link
- [x] Loading state
- [x] Redirect on successful login
- [x] Chakra UI styling with dark mode

**Missing/Incomplete:**
- [ ] **OAuth integration** - Google/GitHub login buttons
- [ ] **Custom theme logo** - Not supported
- [ ] **Social account connections** - Not implemented

### account/signup.html - Detailed Review

**Django Template Features:**
1. Custom theme signup modal logo
2. Django form auto-rendering
3. Non-field error handling
4. reCAPTCHA token input
5. CSRF protection
6. Redirect field support

**React Implementation Status:**
- [x] First/last name fields
- [x] Username with validation (min 3 chars)
- [x] Email with regex validation
- [x] Password with visibility toggle
- [x] Confirm password with match validation
- [x] Password strength indicators
- [x] Field-level error messages
- [x] Loading state
- [x] Sign-in link

**Missing/Incomplete:**
- [ ] **reCAPTCHA** - Not integrated
- [ ] **Custom theme logo** - Not supported
- [ ] **Terms acceptance checkbox** - Not implemented
- [ ] **Organization field** - Available in Django

---

## User Profile

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `user/profile.html` | `ProfilePage.tsx` | Reviewed | Partial - missing contributions | [ ] |
| `people/profile_detail.html` | `ProfilePage.tsx` | Reviewed | Same as above | [ ] |
| `avatar/add.html` | `ProfilePage.tsx` | Not Started | Avatar upload | [ ] |
| `avatar/change.html` | `ProfilePage.tsx` | Not Started | Change avatar | [ ] |

### user/profile.html - Detailed Review

**Django Template Features:**
1. Two-column layout (profile left, content right)
2. User status badges (active/inactive)
3. Organization and role display
4. Edit profile modal
5. Three-tab interface (Overview, Site Visits, References)
6. Chart.js contributions chart
7. Site visits count and list
8. Collection records count
9. Source references list
10. Pagination for site visits (6 per page)
11. Role dropdown (5 options)

**React Implementation Status:**
- [x] User avatar
- [x] Full name with fallback
- [x] Staff and Admin badges
- [x] Organization display
- [x] Member since date
- [x] Edit profile button
- [x] Stats cards (Records, Site Visits, Uploads, Pending)
- [x] Tabbed interface (Profile, Settings, Activity)
- [x] Password change modal
- [x] Loading states and error handling
- [x] Dark mode support

**Missing/Incomplete:**
- [ ] **Contributions chart** - Chart.js visualization
- [ ] **Site visits list** - Tab content not implemented
- [ ] **Source references list** - Not implemented
- [ ] **Pagination** - Not implemented
- [ ] **Role dropdown** - Not in profile editing
- [ ] **Activity tab** - Placeholder only

---

## Taxa Management

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `taxa_management.html` | `TaxaManagementPage.tsx` | Reviewed | Full taxa list, filters, Add Module modal, edit taxon | [ ] |
| `edit_taxon.html` | `TaxaManagementPage.tsx` | Reviewed | Full edit form with all fields | [ ] |
| `_taxongroup_item.html` | `TaxaManagementPage.tsx` | Reviewed | Sidebar group item component | [ ] |

---

## Data Entry - Location Sites

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `location_site_form_view.html` | `AddSitePage.tsx` | Reviewed | ~40% complete, missing geocontext | [ ] |
| `location_site/location_site_form_base.html` | `AddSitePage.tsx` | Reviewed | Same as above | [ ] |
| `wetland_site_form.html` | `AddSitePage.tsx` | Not Started | Wetland-specific site form | [ ] |
| `location_site_detail.html` | `SiteVisitsPage.tsx` | Not Started | Site detail view | [ ] |

### location_site_form_view.html - Detailed Review

**Django Template Features:**
1. Map with marker placement and dragging
2. Site code auto-generation from context
3. River name auto-fetch (FBIS)
4. Geomorphological zone selection
5. Owner field with selection
6. Site image upload with carousel
7. Disclaimer checkbox (required)
8. Existing site proximity warning (500m)
9. Multi-module data links (SASS, water temp)
10. Project-specific conditional fields
11. Delete confirmation modal

**React Implementation Status:**
- [x] Map with interactive marker
- [x] Lat/Lng input fields with validation
- [x] Basic site code input
- [x] Site name and description
- [x] Ecosystem type selection
- [x] Form validation
- [x] Error messaging

**Missing/Incomplete:**
- [ ] **Site code auto-generation** - Context-based naming
- [ ] **River name auto-fetch** - FBIS feature
- [ ] **Geomorphological zone** - Not implemented
- [ ] **Site image upload** - No file upload
- [ ] **Disclaimer checkbox** - Required validation
- [ ] **Proximity warnings** - 500m threshold
- [ ] **Owner selection** - Field missing
- [ ] **Delete functionality** - Not implemented
- [ ] **Wetland-specific fields** - Not implemented

---

## Data Entry - Collections/Records

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `collections_form_page.html` | `AddRecordPage.tsx` | Reviewed | ~65% complete, missing multi-taxa | [ ] |
| `collections_form_layouts/algae_biomass.html` | `AddRecordPage.tsx` | Not Started | Algae-specific form fields | [ ] |

### collections_form_page.html - Detailed Review

**Django Template Features:**
1. Dual map display (site + records)
2. Nearest sites search table
3. Inline site creation modal
4. Embargo period field
5. Hydroperiod dropdown (wetlands)
6. Broad/specific biotope selection
7. Substratum selection
8. Algae curation process dropdown
9. Site image multi-upload
10. Taxon table with multiple taxa
11. GBIF taxon search integration
12. Confirmation modal before submit
13. Disclaimer checkbox

**React Implementation Status:**
- [x] Site search/selection autocomplete
- [x] Taxon search/selection autocomplete
- [x] Source reference selection
- [x] Collection date field
- [x] Collector field
- [x] Abundance number and type
- [x] Sampling method dropdown
- [x] Broad biotope selection
- [x] Form validation and errors
- [x] Success notifications

**Missing/Incomplete:**
- [ ] **Nearest sites table** - No proximity display
- [ ] **Inline site creation** - Modal not implemented
- [ ] **Embargo period** - Field missing
- [ ] **Hydroperiod field** - Wetlands only
- [ ] **Specific biotope** - Only broad biotope
- [ ] **Substratum selection** - Not implemented
- [ ] **Algae curation process** - Not implemented
- [ ] **Site image upload** - Not implemented
- [ ] **Multi-taxa per record** - Single taxon only
- [ ] **GBIF search integration** - Not implemented
- [ ] **Confirmation modal** - Not implemented
- [ ] **Disclaimer checkbox** - Not implemented

---

## Abiotic/Chemical Data

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `abiotic/abiotic_form.html` | Not Implemented | Not Started | Abiotic data entry form | [ ] |
| `chemical/chemical_form.html` | Not Implemented | Not Started | Chemical records form | [ ] |
| `physico_chemical_form.html` | `PhysicoChemicalDashboardPage.tsx` | Not Started | Physico-chemical data | [ ] |
| `physico_chemical_single_site.html` | `PhysicoChemicalDashboardPage.tsx` | Not Started | Single site view | [ ] |
| `physico_chemical_uploader.html` | `UploadPage.tsx` | Not Started | Bulk upload | [ ] |

---

## Water Temperature

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `water_temperature_form.html` | `WaterTemperatureDashboardPage.tsx` | Not Started | Temperature data entry | [ ] |
| `water_temperature_edit_form.html` | `WaterTemperatureDashboardPage.tsx` | Not Started | Edit temperature data | [ ] |
| `water_temperature_single_site.html` | `WaterTemperatureDashboardPage.tsx` | Not Started | Single site view | [ ] |

---

## Site Visits / Surveys

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `site_visit/site_visit_list.html` | `SiteVisitsPage.tsx` | Reviewed | See detailed notes below | [ ] |
| `site_visit/site_visit_detail.html` | `SiteVisitsPage.tsx` | Not Started | Survey detail view | [ ] |
| `site_visit/site_visit_update.html` | `SiteVisitsPage.tsx` | Not Started | Edit survey | [ ] |
| `survey_list.html` | `SiteVisitsPage.tsx` | Not Started | Alternative survey list | [ ] |

### site_visit_list.html - Detailed Review

**Django Template Features:**
1. Sidebar with metrics (Site visits count, Sites count, Records count)
2. Filters: Owner autocomplete, Site code input, Module dropdown
3. Table columns: Site code, Site description, Sampling date, Owner, Total occurrences, Actions
4. Bulk select with checkboxes and select all
5. Bulk actions bar (Validate Selected, Reject Selected, Clear Selection)
6. Individual actions: View, Update, Delete, Send for validation, Validate, Reject
7. SASS badge indicator on site visits
8. Validation status display
9. Column sorting arrows
10. Pagination
11. Modal dialogs for validation/rejection with reason input
12. Link to unvalidated data

**React Implementation Status:**
- [x] Search input
- [x] Validation filter dropdown
- [x] Table with basic columns
- [x] Bulk select with checkboxes
- [x] Bulk actions menu (Validate/Reject)
- [x] View/Edit action buttons
- [x] Pagination
- [x] Reject modal with reason textarea

**Missing/Incomplete:**
- [ ] **Sidebar metrics panel** - Site visits/Sites/Records counts not shown
- [ ] **Owner autocomplete filter** - Not implemented
- [ ] **Site code filter** - Not implemented
- [ ] **Module dropdown filter** - Not implemented
- [ ] **Site description column** - Not shown in table
- [ ] **SASS badge indicator** - Not implemented
- [ ] **Column sorting** - No sort arrows
- [ ] **Send for validation action** - Not implemented
- [ ] **Delete action** - Not implemented
- [ ] **Link to unvalidated data** - Not implemented

---

## Validation

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `non_validated_location_site.html` | `ValidationPage.tsx` | Reviewed | Good, missing map/filters | [ ] |
| `non_validated_list.html` | `ValidationPage.tsx` | Reviewed | Good, missing map/detail modal | [ ] |
| `non_validated_user_list.html` | `ValidationPage.tsx` | Reviewed | Poor, missing edit/delete | [ ] |

### non_validated_list.html - Detailed Review

**Django Template Features:**
1. Filter by species name, collection date, owner
2. Map display for location visualization
3. Data table with validation actions
4. Clickable site links for map zoom
5. Species detail modal
6. Confirm Validate/Reject modals
7. Pagination controls

**React Implementation Status:**
- [x] Multi-tab interface (Sites, Surveys, Records, Taxa)
- [x] Table display of pending items
- [x] Validate/Reject API calls
- [x] Rejection reason modal
- [x] Loading/error states
- [x] Tab-based filtering

**Missing/Incomplete:**
- [ ] **Map visualization** - No map display
- [ ] **Zoom to location** - Not implemented
- [ ] **Detail modal** - View full record data
- [ ] **Filter by owner** - Not implemented
- [ ] **Filter by date range** - Not implemented
- [ ] **Pagination** - Uses page_size: 50 only

### non_validated_user_list.html - Detailed Review

**Django Template Features:**
1. Filter by species name, collection date
2. Map display
3. Edit and Delete actions per row
4. Ready for validation status
5. Send email validation button
6. Delete confirmation modal
7. Detail modal for record

**React Implementation Status:**
- [ ] No direct implementation
- [ ] Partially in ValidationPage records tab

**Missing/Incomplete:**
- [ ] **Edit record functionality** - Not implemented
- [ ] **Delete record functionality** - Not implemented
- [ ] **Ready for validation status** - Not shown
- [ ] **Send email to validator** - Not implemented
- [ ] **Map visualization** - Not implemented
- [ ] **Detail modal** - Not implemented

---

## Source References

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `source_reference_list.html` | `SourceReferencesPage.tsx` | Reviewed | See detailed notes below | [ ] |
| `source_references/add_source_reference.html` | `SourceReferencesPage.tsx` | Not Started | Add reference form | [ ] |
| `edit_source_reference.html` | `SourceReferencesPage.tsx` | Not Started | Edit reference | [ ] |
| `source_references/new_unpublished_data_modal.html` | `SourceReferencesPage.tsx` | Not Started | Unpublished data modal | [ ] |
| `source_references/new_database_record_modal.html` | `SourceReferencesPage.tsx` | Not Started | Database record modal | [ ] |
| `source_references/new_document_modal.html` | `SourceReferencesPage.tsx` | Not Started | Document modal | [ ] |
| `source_references/reference_list.html` | `SourceReferencesPage.tsx` | Not Started | Reference list component | [ ] |
| `source_references/source_reference_page.html` | `SourceReferencesPage.tsx` | Not Started | Full reference page | [ ] |
| `source_references/source_reference_select.html` | Components | Not Started | Reference selector | [ ] |

### source_reference_list.html - Detailed Review

**Django Template Features:**
1. Search input with icon
2. Type filter sidebar with checkboxes and counts per type
3. Author(s) multi-select filter with Apply button
4. Card-based reference display with:
   - Reference type label
   - Title with link
   - Source info
   - Year and authors icons
   - Copy Document ID button (for Published types)
   - Metadata file download link
5. Clickable occurrence count badges (links to map with reference filter)
6. Chemical/Water temperature data count badges
7. Edit/Delete actions for staff
8. Delete records action (separate from delete reference)
9. Pagination

**React Implementation Status:**
- [x] Search input
- [x] Type filter dropdown
- [x] Table with Title, Authors, Year, Type, Records, Actions columns
- [x] DOI link display
- [x] View/Edit action buttons
- [x] Pagination
- [x] Add Reference button

**Missing/Incomplete:**
- [ ] **Card-based layout** - Currently uses table instead of cards
- [ ] **Type filter with checkboxes and counts** - Uses simple dropdown
- [ ] **Author multi-select filter** - Not implemented
- [ ] **Reference source info** - Not displayed
- [ ] **Copy Document ID button** - Not implemented
- [ ] **Clickable occurrence badges** - No map link integration
- [ ] **Chemical/Water temperature data counts** - Not shown
- [ ] **Metadata file download link** - Not implemented
- [ ] **Delete reference action** - Not implemented
- [ ] **Delete records action** - Not implemented

---

## Upload/Import Pages

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `uploader.html` | `UploadPage.tsx` | Reviewed | ~45% complete, missing licence | [ ] |
| `taxa_uploader.html` | `UploadPage.tsx` | Reviewed | Same upload component | [ ] |
| `taxa_validation_uploader.html` | `UploadPage.tsx` | Not Started | Taxa validation upload | [ ] |
| `collections_uploader.html` | `UploadPage.tsx` | Reviewed | Same upload component | [ ] |
| `harvest_collection.html` | `HarvestPage.tsx` | Not Started | Harvest external data | [ ] |
| `harvest_gbif_species.html` | `HarvestPage.tsx` | Not Started | GBIF species import | [ ] |
| `shapefile_uploader.html` | `UploadPage.tsx` | Reviewed | Same upload component | [ ] |

### uploader.html - Detailed Review

**Django Template Features:**
1. Guidelines download link
2. Template download link
3. Source reference inputs (Author, Date, Title)
4. Uploader name and email fields
5. Upload type dropdown
6. Dynamic file input (CSV/XLSX/ZIP)
7. Notes textarea
8. Data licence selection (CC0, CC-BY, CC-BY-NC)
9. Licence description display
10. Honeypot field for bot prevention
11. reCAPTCHA integration
12. Form validation

**React Implementation Status:**
- [x] Multiple upload type tabs
- [x] File selection input
- [x] Upload progress tracking
- [x] Success/error notifications
- [x] Taxon group selection
- [x] Template download buttons
- [x] Instructions panel
- [x] Responsive layout

**Missing/Incomplete:**
- [ ] **Uploader name/email** - Fields missing
- [ ] **Source reference inputs** - Author, Date, Title
- [ ] **Notes textarea** - Not implemented
- [ ] **Data licence selection** - CC0, CC-BY, CC-BY-NC
- [ ] **Licence description** - Not shown
- [ ] **Honeypot field** - Bot prevention
- [ ] **reCAPTCHA** - Not integrated
- [ ] **Guidelines download** - Link missing
- [ ] **Embargo/metadata fields** - Not implemented

---

## Layers & Context

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `context_layers.html` | `ContextLayersPage.tsx` | Not Started | Context layer management | [ ] |
| `visualization_layers.html` | `VisualizationLayersPage.tsx` | Not Started | Visualization layers | [ ] |
| `layers/layer_metadata_upload.html` | `ContextLayersPage.tsx` | Not Started | Layer metadata form | [ ] |
| `spatial_layer_upload.html` | `ContextLayersPage.tsx` | Not Started | Spatial layer upload | [ ] |
| `upload_layer.html` | `ContextLayersPage.tsx` | Not Started | Generic layer upload | [ ] |

---

## Dashboards

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `dashboard_management.html` | `DashboardSettingsPage.tsx` | Reviewed | Partial, missing GridStack | [ ] |
| `spatial_dashboard.html` | `SiteDashboardPage.tsx` | Reviewed | Good, missing abiotic | [ ] |
| `tracking/dashboard.html` | `AnalyticsDashboardPage.tsx` | Reviewed | Excellent | [ ] |

### dashboard_management.html - Detailed Review

**Django Template Features:**
1. Module/Taxon Group selector
2. GridStack drag-and-drop widget manager
3. Trash zone for removing widgets
4. 12 default widgets
5. Grid layout config (x, y, width, height)
6. Layout serialization to JSON
7. Reset dashboard functionality
8. Save configuration button

**React Implementation Status:**
- [x] Widget enable/disable functionality
- [x] Cache management features
- [x] Available widget types (10 types)

**Missing/Incomplete:**
- [ ] **GridStack drag-and-drop** - Visual interface
- [ ] **Widget position/size persistence** - Not saved
- [ ] **Module group filtering** - Not implemented
- [ ] **Trash/removal zone UI** - Not implemented
- [ ] **Layout reset modal** - Not implemented

### spatial_dashboard.html - Detailed Review

**Django Template Features:**
1. Two-column layout (5:7 split)
2. Filter History table
3. Distribution map with download
4. Overview summary with CSV download
5. 6 pie charts (Origin, Endemism, Conservation Status)
6. Line/Bar charts with downloads
7. Species download list button

**React Implementation Status:**
- [x] Multi-module summary data
- [x] Chart components (Pie, Bar)
- [x] Download functionality
- [x] Error and loading states

**Missing/Incomplete:**
- [ ] **Filter history section** - Not implemented
- [ ] **Distribution map** - Not in summary view
- [ ] **Red List Index chart** - Not implemented
- [ ] **Individual chart downloads** - SVG export

---

## SASS (South African Scoring System)

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `sass/form_page.html` | `SASSDashboardPage.tsx` | Not Started | SASS data entry | [ ] |
| `sass/form_only_read_page.html` | `SASSDashboardPage.tsx` | Not Started | Read-only SASS view | [ ] |
| `sass/sass_dashboard_single_site.html` | `SASSDashboardPage.tsx` | Reviewed | Excellent | [ ] |
| `sass/sass_dashboard_multiple_sites.html` | `SASSDashboardPage.tsx` | Not Started | Multi-site SASS | [ ] |
| `sass/sass_list_page.html` | `SASSDashboardPage.tsx` | Not Started | SASS records list | [ ] |

### sass_dashboard_single_site.html - Detailed Review

**Django Template Features:**
1. SASS version info
2. SASS score and ASPT values
3. Taxa count tracking
4. Ecological category (A-F rating)
5. Historical SASS trend charts
6. Sensitivity breakdown pie chart
7. Biotope distribution data
8. Taxa sensitivity table
9. Ecoregion and geomorphological zone

**React Implementation Status:**
- [x] SASS score tracking
- [x] Ecological category color coding
- [x] Sensitivity breakdown pie chart
- [x] Biotope data visualization
- [x] Historical trend charts
- [x] Taxa sensitivity table
- [x] Breadcrumb navigation

**Missing/Incomplete:**
- [ ] **SASS version selector** - Interactive version
- [ ] **Detailed taxa table** - Abundance data
- [ ] **SASS assessment history** - Not detailed

---

## Admin/Management

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `backups_management.html` | `BackupsManagementPage.tsx` | Not Started | Backup management | [ ] |
| `download_request_list.html` | `DownloadsPage.tsx` | Not Started | Download requests | [ ] |

---

## Other/Utility

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `bug_report_template.html` | `BugReportPage.tsx` | Not Started | Bug report form | [ ] |
| `contactus/contact.html` | `ContactPage.tsx` | Not Started | Contact form | [ ] |
| `links/links.html` | `ResourcesPage.tsx` | Not Started | External links | [ ] |
| `flatpages/default.html` | `AboutPage.tsx` | Not Started | Static content pages | [ ] |

---

## Not Applicable for React (Server-side only)

| Template | Reason |
|----------|--------|
| `404.html` | Error page handled by Django |
| `500.html` | Error page handled by Django |
| `admin/*.html` | Django admin customizations |
| `email/*.html` | Email templates |
| `base.html` | Django base template |
| `main_base.html` | Django base template |
| `geonode_base.html` | GeoNode integration |
| `navigation_bar.html` | Django navigation (React has own) |
| `footer.html` | Django footer (React has own) |
| `carousel*.html` | Landing page components |
| `includes/*.html` | Django template includes |
| `paginator_template.html` | Django pagination |
| `recaptcha.html` | Captcha integration |
| `documents/*.html` | GeoNode documents |
| `socialaccount/*.html` | Social auth templates |
| `ordered_model/*.html` | Admin ordering |
| `ckeditor/*.html` | Rich text editor |
| `td_biblio/*.html` | Bibliography system |
| `metadata_base.html` | Metadata forms |
| `thermal/*.html` | Thermal analysis (specialized) |
| `climate/*.html` | Climate data (specialized) |
| `pesticide/*.html` | Pesticide data (specialized) |

---

## Review Progress Summary

| Category | Total | Reviewed | Human Verified |
|----------|-------|----------|----------------|
| Core Pages | 6 | 4 | 0 |
| Authentication | 10 | 3 | 0 |
| User Profile | 4 | 2 | 0 |
| Taxa Management | 3 | 3 | 0 |
| Location Sites | 4 | 2 | 0 |
| Collections | 2 | 1 | 0 |
| Abiotic/Chemical | 5 | 0 | 0 |
| Water Temperature | 3 | 0 | 0 |
| Site Visits | 4 | 1 | 0 |
| Validation | 3 | 3 | 0 |
| Source References | 9 | 1 | 0 |
| Upload/Import | 7 | 4 | 0 |
| Layers | 5 | 0 | 0 |
| Dashboards | 3 | 3 | 0 |
| SASS | 5 | 1 | 0 |
| Admin | 2 | 0 | 0 |
| Utility | 4 | 0 | 0 |
| **TOTAL** | **79** | **28** | **0** |

---

## Notes

- Templates marked as "Reviewed" have been compared against their React implementations
- "Human Verified" should be marked after manual testing in browser
- Some templates may map to multiple React pages or components
- N/A templates are server-side only and don't need React equivalents

---

*Last Updated: 2026-03-21*
*Generated by Claude Code*

---

## Implementation Priority Matrix

### High Priority (Critical for MVP)
- Site code auto-generation logic
- Multi-taxa per record support
- Map visualizations across dashboards
- GridStack drag-and-drop for dashboard settings
- OAuth integration (Google/GitHub)
- reCAPTCHA for forms

### Medium Priority (Enhanced UX)
- User contributions chart
- Site visits list in profile
- Geomorphological zone context
- Image upload/carousel
- Filter history display
- Export to image functionality

### Low Priority (Enhancements)
- Custom theme/branding support
- CMS-driven landing page sections
- Funders/Partners section
- SASS version comparison
- Abiotic data visualization
