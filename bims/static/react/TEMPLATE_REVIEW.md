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
| `landing_page_fbis.html` | `LandingPage.tsx` | Not Started | FBIS variant of landing page | [ ] |
| `landing_page_dashboard.html` | `LandingPage.tsx` | Not Started | Dashboard variant | [ ] |
| `landing_page_dashboard_fbis.html` | `LandingPage.tsx` | Not Started | FBIS dashboard variant | [ ] |
| `map_page/bims.html` | `MapPage.tsx` | Not Started | Main map with filters, layers, search | [ ] |
| `summary_report.html` | `SummaryReportPage.tsx` | Not Started | Stats, counts, data quality metrics | [ ] |

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

---

## Authentication & Account Pages

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `account/login.html` | `LoginPage.tsx` | Not Started | Email/password login | [ ] |
| `account/signup.html` | `RegisterPage.tsx` | Not Started | User registration | [ ] |
| `account/logout.html` | N/A | N/A | Handled by auth provider | [ ] |
| `account/password_reset.html` | `LoginPage.tsx` | Not Started | Password reset flow | [ ] |
| `account/password_reset_done.html` | N/A | N/A | Redirect/message only | [ ] |
| `account/password_reset_from_key.html` | N/A | Not Started | Reset from email link | [ ] |
| `account/password_change.html` | `ProfilePage.tsx` | Not Started | Change password form | [ ] |
| `account/email_confirm.html` | N/A | N/A | Email verification | [ ] |
| `account/verification_sent.html` | N/A | N/A | Confirmation message | [ ] |
| `account/email.html` | `ProfilePage.tsx` | Not Started | Email management | [ ] |

---

## User Profile

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `user/profile.html` | `ProfilePage.tsx` | Not Started | User profile, contributions, stats | [ ] |
| `people/profile_detail.html` | `ProfilePage.tsx` | Not Started | Detailed profile view | [ ] |
| `avatar/add.html` | `ProfilePage.tsx` | Not Started | Avatar upload | [ ] |
| `avatar/change.html` | `ProfilePage.tsx` | Not Started | Change avatar | [ ] |

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
| `location_site_form_view.html` | `AddSitePage.tsx` | Not Started | Add/Edit site with map, geocontext | [ ] |
| `location_site/location_site_form_base.html` | `AddSitePage.tsx` | Not Started | Base site form fields | [ ] |
| `wetland_site_form.html` | `AddSitePage.tsx` | Not Started | Wetland-specific site form | [ ] |
| `location_site_detail.html` | `SiteVisitsPage.tsx` | Not Started | Site detail view | [ ] |

---

## Data Entry - Collections/Records

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `collections_form_page.html` | `AddRecordPage.tsx` | Not Started | Fish/Invert/Algae record form | [ ] |
| `collections_form_layouts/algae_biomass.html` | `AddRecordPage.tsx` | Not Started | Algae-specific form fields | [ ] |

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
| `non_validated_location_site.html` | `ValidationPage.tsx` | Not Started | Unvalidated sites list | [ ] |
| `non_validated_list.html` | `ValidationPage.tsx` | Not Started | Unvalidated records list | [ ] |
| `non_validated_user_list.html` | `ValidationPage.tsx` | Not Started | User-specific unvalidated | [ ] |

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
| `uploader.html` | `UploadPage.tsx` | Not Started | CSV upload with progress | [ ] |
| `taxa_uploader.html` | `UploadPage.tsx` | Not Started | Taxa CSV upload | [ ] |
| `taxa_validation_uploader.html` | `UploadPage.tsx` | Not Started | Taxa validation upload | [ ] |
| `collections_uploader.html` | `UploadPage.tsx` | Not Started | Collections bulk upload | [ ] |
| `harvest_collection.html` | `HarvestPage.tsx` | Not Started | Harvest external data | [ ] |
| `harvest_gbif_species.html` | `HarvestPage.tsx` | Not Started | GBIF species import | [ ] |
| `shapefile_uploader.html` | `UploadPage.tsx` | Not Started | Shapefile upload | [ ] |

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
| `dashboard_management.html` | `DashboardSettingsPage.tsx` | Not Started | Dashboard config | [ ] |
| `spatial_dashboard.html` | `SiteDashboardPage.tsx` | Not Started | Spatial analytics | [ ] |
| `tracking/dashboard.html` | `AnalyticsDashboardPage.tsx` | Not Started | Analytics/tracking | [ ] |

---

## SASS (South African Scoring System)

| Template | React Page | Status | AI Notes | Human Verified |
|----------|-----------|--------|----------|----------------|
| `sass/form_page.html` | `SASSDashboardPage.tsx` | Not Started | SASS data entry | [ ] |
| `sass/form_only_read_page.html` | `SASSDashboardPage.tsx` | Not Started | Read-only SASS view | [ ] |
| `sass/sass_dashboard_single_site.html` | `SASSDashboardPage.tsx` | Not Started | Single site SASS | [ ] |
| `sass/sass_dashboard_multiple_sites.html` | `SASSDashboardPage.tsx` | Not Started | Multi-site SASS | [ ] |
| `sass/sass_list_page.html` | `SASSDashboardPage.tsx` | Not Started | SASS records list | [ ] |

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
| Core Pages | 6 | 1 | 0 |
| Authentication | 10 | 0 | 0 |
| User Profile | 4 | 0 | 0 |
| Taxa Management | 3 | 3 | 0 |
| Location Sites | 4 | 0 | 0 |
| Collections | 2 | 0 | 0 |
| Abiotic/Chemical | 5 | 0 | 0 |
| Water Temperature | 3 | 0 | 0 |
| Site Visits | 4 | 1 | 0 |
| Validation | 3 | 0 | 0 |
| Source References | 9 | 1 | 0 |
| Upload/Import | 7 | 0 | 0 |
| Layers | 5 | 0 | 0 |
| Dashboards | 3 | 0 | 0 |
| SASS | 5 | 0 | 0 |
| Admin | 2 | 0 | 0 |
| Utility | 4 | 0 | 0 |
| **TOTAL** | **79** | **6** | **0** |

---

## Notes

- Templates marked as "Reviewed" have been compared against their React implementations
- "Human Verified" should be marked after manual testing in browser
- Some templates may map to multiple React pages or components
- N/A templates are server-side only and don't need React equivalents

---

*Last Updated: 2026-03-21*
*Generated by Claude Code*
