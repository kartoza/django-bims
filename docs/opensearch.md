# OpenSearch Integration

This document describes the OpenSearch integration in django-bims: what it indexes,
how the index is kept in sync, and how it is used by the dashboard and search APIs.

---

## Table of Contents

1. [Overview](#overview)
2. [Infrastructure](#infrastructure)
3. [Configuration](#configuration)
4. [Index Schema](#index-schema)
5. [Keeping the Index in Sync](#keeping-the-index-in-sync)
   - [Real-time signals](#real-time-signals)
   - [Bulk reindex](#bulk-reindex)
   - [Reindex admin page](#reindex-admin-page)
6. [Query Builder](#query-builder)
7. [APIs backed by OpenSearch](#apis-backed-by-opensearch)
   - [Collection search](#collection-search)
   - [Location sites summary](#location-sites-summary)
   - [Multi-location sites overview](#multi-location-sites-overview)
8. [Fallback behaviour](#fallback-behaviour)
9. [Adding new fields to the index](#adding-new-fields-to-the-index)
10. [Celery queues](#celery-queues)

---

## Overview

OpenSearch is used as a secondary query layer alongside PostgreSQL. All
`BiologicalCollectionRecord` rows are mirrored into a single flat index
(`bims_collections`). Reads for the public search API and the dashboard
aggregation endpoints are routed to OpenSearch, while writes (saves/deletes)
continue to go to PostgreSQL and are then propagated to the index
asynchronously via Celery tasks.

The integration is **optional**. If `OPENSEARCH_HOST` is not set (or the
cluster is unreachable) every endpoint that uses OpenSearch falls back
transparently to the existing PostgreSQL-based implementation.

---

## Infrastructure

The OpenSearch cluster is run as a Docker container alongside the application:

```yaml
# deployment/docker-compose.dev.yml
opensearch:
  image: opensearchproject/opensearch:2
  environment:
    - discovery.type=single-node
    - DISABLE_SECURITY_PLUGIN=true
    - OPENSEARCH_JAVA_OPTS=-Xms16g -Xmx16g
  ports:
    - "9200:9200"
    - "9600:9600"
```

The Python client is `opensearch-py` (`opensearchpy`).

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| `OPENSEARCH_HOST` | `localhost` | Hostname of the OpenSearch node |
| `OPENSEARCH_PORT` | `9200` | Port of the OpenSearch node |

Set via environment variables. The dev Docker Compose file sets
`OPENSEARCH_HOST=opensearch` so the application container resolves the
service by name.

The client is a module-level singleton in `bims/opensearch/client.py`:

```python
def get_client() -> OpenSearch:
    # returns a cached OpenSearch instance
```

The cluster is also configured at reindex time to allow large bucket counts:

```python
client.cluster.put_settings(body={
    'persistent': {'search.max_buckets': 200000}
})
```

---

## Index Schema

**Index name:** `bims_collections`

**Definition:** `bims/opensearch/indices.py` → `COLLECTIONS_MAPPING`

Each document represents one `BiologicalCollectionRecord`. The schema is flat
(no nested objects) so all aggregations run in constant-time bucket resolution.

### Field reference

| Field | Type | Source |
|---|---|---|
| `schema_name` | keyword | `connection.schema_name` at index time |
| `record_id` | integer | `record.id` |
| `uuid` | keyword | `record.uuid` |
| `taxonomy_id` | integer | `record.taxonomy_id` |
| `canonical_name` | text + keyword | `taxonomy.canonical_name` |
| `scientific_name` | text + keyword | `taxonomy.scientific_name` |
| `vernacular_names` | text | `taxonomy.vernacular_names` (list) |
| `tags` | keyword | `taxonomy.tags` (list) |
| `endemism` | keyword | `taxonomy.endemism.name` |
| `conservation_status` | keyword | `taxonomy.iucn_status.category` |
| `national_conservation_status` | keyword | `taxonomy.national_conservation_status.category` |
| `origin` | keyword | `taxonomy.origin.origin_key` |
| `taxonomy_rank` | keyword | `taxonomy.rank` |
| `taxonomy_status` | keyword | `taxonomy.taxonomic_status` |
| `module_group_id` | integer | `record.module_group_id` |
| `module_group_name` | keyword | `record.module_group.name` |
| `taxon_group_ids` | integer | `taxonomy.taxongroup_set` (list) |
| `site_id` | integer | `record.site_id` |
| `site_code` | text + keyword | `record.site.site_code` |
| `site_name` | text + keyword | `record.site.name` |
| `river_name` | text + keyword | `record.site.river.name` |
| `ecosystem_type` | keyword | `record.site.ecosystem_type` |
| `location` | geo_point | `record.site.geometry_point` |
| `location_context_groups` | keyword | group keys for the site (list) |
| `location_context_values` | keyword | `group_key|value` pairs for the site (list) |
| `collection_date` | date | `record.collection_date` |
| `collector` | text | `record.collector` |
| `original_species_name` | text | `record.original_species_name` |
| `data_type` | keyword | `record.data_type` (defaults to `public` when empty) |
| `sampling_method` | keyword | `record.sampling_method.sampling_method` |
| `biotope` | keyword | `record.biotope.name` |
| `owner_id` | integer | `record.owner_id` |
| `is_validated` | boolean | `record.validated` |
| `ready_for_validation` | boolean | `record.ready_for_validation` |
| `end_embargo_date` | date | `record.end_embargo_date` |

### Composite document ID

```
{schema_name}_{record_id}
```

This prevents collisions between the same `record_id` across different tenant
schemas.

### Location context fields

`location_context_groups` stores every group key associated with a site:

```
["combination_saprovince_sadc_boundary", "monthly_rainfall_april", ...]
```

`location_context_values` stores `key|value` pairs:

```
["combination_saprovince_sadc_boundary|Western Cape", "monthly_rainfall_april|40", ...]
```

These enable the spatial filter feature without joining to the
`LocationContext` table at query time.

---

## Keeping the Index in Sync

### Real-time signals

`bims/signals/opensearch.py` registers Django signal handlers that fire
whenever a `BiologicalCollectionRecord` is saved or deleted. Each handler
dispatches a lightweight Celery task:

| Signal | Task | Queue |
|---|---|---|
| `post_save` | `bims.tasks.index_collection_record` | `search` |
| `post_delete` | `bims.tasks.delete_collection_record_from_index` | `search` |

The `schema_name` of the current tenant connection is captured in the signal
handler (not in the task) so the worker can switch to the correct schema.

Signals are connected in `bims/signals/app.py` via `connect_opensearch_signals()`.
If `opensearch-py` is not installed the signals are skipped silently.

### Bulk reindex

The management command `opensearch_reindex` and the Celery task
`bims.tasks.opensearch_reindex` perform a full reindex of all tenant schemas.

```bash
# management command (synchronous)
python manage.py opensearch_reindex [--recreate] [--chunk-size 500] [--schema tenant1]

# Celery task (dispatched by the admin UI)
opensearch_reindex.delay(run_id)
```

**`--recreate`** drops and recreates the index before indexing. Without it, the
index mapping is updated via `put_mapping` and existing documents are
overwritten in place.

**Chunked bulk indexing** (`bims/opensearch/documents.py → bulk_index`):

- Fetches record IDs first, then loads records in batches of `chunk_size` with
  all required `select_related` / `prefetch_related` to avoid N+1 queries.
- Uses `opensearchpy.helpers.bulk` for efficient batch writes.
- Accepts an optional `on_progress(total_indexed)` callback so the caller can
  write live progress to the database.

### Reindex admin page

A superuser-only page at `/opensearch-reindex/` lets you trigger a reindex
from the browser without SSH access.

- **Start form**: chunk size, schema filter (blank = all tenants), recreate toggle.
- **Run history**: last 20 runs with per-tenant status, record counts, errors, and timestamps.
- **Live progress**: the page shows `records_indexed` which is updated after each
  chunk, so you can watch it increment during a long run.

The page is protected by `UserPassesTestMixin` (`is_superuser` required).

**Models** (`bims/models/opensearch_reindex.py`):

- `OpenSearchReindexRun` - top-level run record (status, options, totals).
- `OpenSearchReindexTenantStatus` - per-tenant progress within a run.

Both models live in the **public** schema and are accessed via
`schema_context(get_public_schema_name())`.

---

## Query Builder

`bims/opensearch/query_builder.py` provides shared helpers used by all
OpenSearch-backed views and tasks.

### `build_filter_clauses(params, user, schema_name) -> list`

Converts a request params dict into a list of OpenSearch filter clauses.
Always adds a `schema_name` term filter first. Supported params:

| Param | Filter |
|---|---|
| `taxon` | `terms` on `taxonomy_id` |
| `siteId` | `terms` on `site_id` |
| `modules` | `terms` on `module_group_id` |
| `spatialFilter` | `term` on `location_context_groups` or `location_context_values` |
| `ecosystemType` | `terms` on `ecosystem_type` |
| `conservationStatus` | `terms` on `conservation_status` |
| `endemic` | `terms` on `endemism` |
| `tags` | `terms` on `tags` |
| `yearFrom` / `yearTo` | `range` on `collection_date` |
| `bbox` | `geo_bounding_box` on `location` |
| `polygon` | `geo_polygon` on `location` (also handles `UserBoundary` integer IDs) |
| `validated` | `term` on `is_validated` |

Security filters from `build_security_filter(user)` are always appended.

### `build_security_filter(user) -> list`

Enforces data access rules:

| User type | Filter applied |
|---|---|
| Anonymous | `data_type = public` AND embargo not active |
| Superuser / staff | No restriction |
| Authenticated | `data_type in [public, sensitive?, private?]` based on group membership + embargo clause allowing owner access |

Group names checked: `SensitiveDataGroup`, `PrivateDataGroup`.

### `parse_extent(geo_bounds) -> list`

Converts an OpenSearch `geo_bounds` aggregation result to
`[min_lon, min_lat, max_lon, max_lat]` (EPSG:4326, suitable for
`ol.proj.transformExtent`).

- Returns `[]` if bounds are missing or contain null coordinates.
- Pads single-point extents by ±0.01° so OpenLayers `view.fit()` does not
  throw "Cannot fit empty extent".

---

## APIs backed by OpenSearch

### Collection search

**Endpoint:** `GET /api/opensearch/collection-search/`

**View:** `bims/api_views/opensearch_search.py → OpenSearchCollectionView`

Accepts the same query parameters as `/api/collection-search/` (the legacy
PostGIS search). Returns a paginated list of records plus aggregation
summaries.

**Response fields:**

| Field | Source |
|---|---|
| `total` / `total_records` | `hits.total.value` |
| `total_sites` | `cardinality` on `site_id` |
| `total_unique_taxa` | `cardinality` on `taxonomy_id` |
| `extent` | `geo_bounds` on `location` |
| `sites` | `top_sites` terms agg (top 20 by record count) |
| `taxa` | `top_taxa` terms agg (top 50 by record count) |
| `records` | raw hits (page of documents) |
| `token` | `SearchToken` created from all matching `site_id` values |
| `fuzzy_search` | whether fuzzy matching was used |

**Search strategy** (three-pass with fallback):

1. Exact phrase (`type: phrase`)
2. All-terms required (`type: best_fields`, `operator: and`)
3. Fuzzy (`type: best_fields`, `fuzziness: AUTO`)

The first pass that returns at least one hit is used. `fuzzy_search: true`
is only set when pass 3 is reached.

---

### Location sites summary

**Endpoint:** `GET /api/location-sites-summary/`

**View:** `bims/api_views/location_site.py → LocationSitesSummary`

**Task (OS):** `bims/tasks/opensearch_location_site_summary.py → opensearch_location_site_summary`

**Task (DB fallback):** `bims.tasks.generate_location_site_summary`

This endpoint powers the main dashboard panel. When OpenSearch is available
the OS task runs a single aggregation query and returns results in the same
JSON shape as the DB task.

**What comes from OpenSearch:**

| Response field | Aggregation |
|---|---|
| `total_records` | `hits.total.value` |
| `taxa_occurrence` (per-year chart) | `date_histogram` on `collection_date` with `calendar_interval: year` |
| `taxa_occurrence` (per-date chart) | `date_histogram` on `collection_date` with `calendar_interval: day` |
| `category_summary` | `terms` on `origin` |
| `occurrence_data` (taxa table) | `terms` on `taxonomy_id` with sub-aggs for `scientific_name`, `origin`, `conservation_status`, `endemism` |
| `biodiversity_data.origin_chart` | `terms` on `origin` |
| `biodiversity_data.cons_status_chart` | `terms` on `conservation_status` |
| `biodiversity_data.cons_status_national_chart` | `terms` on `national_conservation_status` |
| `biodiversity_data.endemism_chart` | `terms` on `endemism` |
| `biodiversity_data.sampling_method_chart` | `terms` on `sampling_method` |
| `biodiversity_data.biotope_chart` | `terms` on `biotope` |
| `site_details` (multi-site) | cardinality on `site_id` and `taxonomy_id` |
| `extent` | `geo_bounds` on `location` |

**What still comes from PostgreSQL:**

- `source_references` - relational, requires joining through `source_reference`
- `chemical_records` - separate `ChemicalRecord` model
- `survey` - separate `Survey` model (top 5 most recent)
- `site_images` - separate `SiteImage` model
- `site_details` (single-site) - full site metadata from `LocationSite`

**Caching:** The result is written to a file via `SearchProcess` / `create_search_process_file`, same as the DB task. Subsequent requests with the same URL return the cached file immediately.

---

### Multi-location sites overview

**Endpoint:** `GET /api/multi-location-sites-background-overview/`

**View:** `bims/api_views/location_site_overview.py → MultiLocationSitesBackgroundOverview`

**Task (OS):** `bims/tasks/opensearch_location_sites_overview.py → opensearch_location_sites_overview`

**Task (DB fallback):** `bims.tasks.location_sites_overview`

Powers the module-group breakdown panel (occurrences / sites / taxa / endemism
/ origin / conservation status per taxon group).

**Single aggregation query structure:**

```
by_module (terms on module_group_id)
├── unique_sites       cardinality on site_id
├── unique_taxa        cardinality on taxonomy_id
├── by_endemism        terms on endemism
├── by_origin          terms on origin
└── accepted_species   filter: taxonomy_status=ACCEPTED AND taxonomy_rank in [SPECIES, SUBSPECIES, VARIETY]
    └── by_cons_status terms on conservation_status
```

**Response structure** (per module group):

```json
{
  "biodiversity_data": {
    "Fishes": {
      "module": 1,
      "occurrences": 12345,
      "sites": 234,
      "number_of_taxa": 89,
      "endemism": [{"endemism_name": "Endemic", "count": 45}],
      "origin": [{"origin_name": "Native", "name": "Native", "count": 100}],
      "cons_status": [{"iucn_category": "LC", "colour": "#009106", "count": 80, "name": "Least Concern"}]
    }
  },
  "sass_exist": false,
  "climate_exist": false
}
```

Conservation status colours are looked up from the `IUCNStatus` DB table after
aggregation (the colour is not stored in the index).

`source_references` is still fetched from PostgreSQL via a lightweight
`CollectionSearch`.

`sass_exist` and `climate_exist` are always `false` in the OS implementation
(SASS and climate data are not indexed).

---

## Fallback behaviour

Both dashboard endpoints use a `_pick_*_task()` helper that:

1. Checks `settings.OPENSEARCH_HOST` is set.
2. Calls `get_client().info()` to confirm the cluster is reachable.
3. Returns the OS task if both checks pass, otherwise returns the DB task.

This means the system degrades gracefully to full PostGIS queries if OpenSearch
is down or not configured.

---

## Adding new fields to the index

1. Add the field to `build_document()` in `bims/opensearch/documents.py`.
2. Add the field to `COLLECTIONS_MAPPING` in `bims/opensearch/indices.py`.
3. If the field requires new related data, add the model to `select_related`
   or `prefetch_related` in `bulk_index()`.
4. Call `update_mapping()` to push the new mapping to the live index without
   recreating it:

```python
from bims.opensearch.indices import update_mapping
update_mapping()
```

5. Existing documents will have `null` for the new field until a reindex is run.
   Trigger a full reindex from `/opensearch-reindex/` or via the management command.

---

## Celery queues

All OpenSearch tasks run on the `search` queue:

| Task | Trigger |
|---|---|
| `bims.tasks.index_collection_record` | `post_save` signal on `BiologicalCollectionRecord` |
| `bims.tasks.delete_collection_record_from_index` | `post_delete` signal on `BiologicalCollectionRecord` |
| `bims.tasks.opensearch_reindex` | Reindex admin page POST |
| `bims.tasks.opensearch_location_site_summary` | `GET /api/location-sites-summary/` |
| `bims.tasks.opensearch_location_sites_overview` | `GET /api/multi-location-sites-background-overview/` |

The worker must be listening on the `search` queue:

```bash
celery --app=bims.celery:app worker -Q search,update,geocontext
```
