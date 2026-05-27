# Harvest BIMS Species

This document describes how the BIMS-to-BIMS species harvester works: its purpose,
the components involved, the step-by-step flow, and the read-only taxon group feature.

---

## Purpose

The harvester allows a BIMS instance to import validated species (taxa) from another
remote BIMS instance. The remote instance is treated as an upstream data source.
Species are matched against local records to avoid duplication, and new records are
created when no match is found. On re-harvest, taxa whose upstream payload has not
changed are skipped entirely via checksum comparison.

---

## Permission

Access to the harvester requires the `bims.can_harvest_species` permission. Users
without this permission cannot reach the UI or the supporting API endpoints.

---

## Components

| Component | Location |
|---|---|
| UI view | `bims/views/harvest_bims_species.py` — `HarvestBimsSpeciesView` |
| Template | `bims/templates/harvest_bims_species.html` |
| Celery task | `bims/tasks/harvest_bims_species.py` — `harvest_bims_species` |
| Remote fetch utilities | `bims/utils/bims_instance.py` |
| Fetch groups API | `bims/api_views/bims_fetch_taxon_groups.py` — `BimsFetchTaxonGroupsView` |
| Harvest status API | `bims/views/harvest_collection_data.py` — `HarvestSessionStatusView` |
| Session model | `bims/models/harvest_session.py` — `HarvestSession` |
| Taxon group model | `bims/models/taxon_group.py` — `TaxonGroup` |
| Membership through model | `bims/models/taxon_group_taxonomy.py` — `TaxonGroupTaxonomy` |

---

## UI Flow

### Step 1 — Enter the remote BIMS URL

The user enters the base URL of the remote BIMS instance
(e.g. `https://freshwaterbiodiversity.org`) and clicks **Fetch Taxon Groups**.

This triggers an AJAX `GET` to `/api/bims-fetch-taxon-groups/?base_url=<url>`,
which calls `GET <remote>/api/module-list/` and returns the list of available
species-module taxon groups on that instance.

### Step 2 — Select a remote taxon group

The returned groups populate a dropdown. Selecting one stores the remote group's
`id` and `name` in hidden form fields.

### Step 3 — Choose import mode

**Use existing taxon group** *(default)*
Species are imported into an existing local taxon group chosen from a second
dropdown. Only this local group selector is shown.

**Import as new taxon group**
A new local taxon group is created automatically using the remote group's name.
A **Mark as read-only** checkbox is shown (see [Read-only groups](#read-only-taxon-groups)).

### Step 4 — Start harvesting

The form `POST`s to `/harvest-bims/`. The view validates the inputs, creates a
`HarvestSession` record (category `'bims'`), writes an empty log file under
`MEDIA_ROOT/harvest-bims-session-log/<id>-<timestamp>.txt`, and dispatches the
`harvest_bims_species` Celery task. The page then shows a live progress panel that
polls `/api/harvest-status/<session_id>/` every second, displaying the last 50 lines
of the log file.

### Previous configs

The UI shows a **Previous config** dropdown pre-populated from the last distinct
`(base_url, remote_group_id, local_group, import_mode)` combination seen in finished
sessions. Selecting a previous config pre-fills all form fields, making repeated
harvests from the same source one-click.

---

## Celery Task: `harvest_bims_species`

**Queue:** `update`
**Signature:** `harvest_bims_species(session_id: int, schema_name: str)`

The `schema_name` argument enables multi-tenant operation via
`django_tenants.utils.schema_context`.

### Constants

| Constant | Value | Meaning |
|---|---|---|
| `REQUEST_TIMEOUT` | `30` | HTTP socket timeout (seconds) |
| `RETRY_ATTEMPTS` | `3` | Max retries per remote call |
| `PAGE_SIZE` | `100` | Taxa per page from remote API |
| `save_interval` | `50` | How often `session.status` is updated |

### Task flow

```
1.  Load HarvestSession by session_id (within schema context)
2.  Extract config from session.additional_data:
      base_url, remote_group_id, remote_group_name, import_mode, mark_readonly
3.  Disconnect BIMS signals (prevents cascade side-effects during bulk saves)
4.  Resolve the local target TaxonGroup (see Import Modes)
5.  Call get_all_taxa(base_url, remote_group_id) — paginated generator
6.  For each remote taxon:
      a. Compute SHA-256 checksum of canonical fields
      b. If TaxonGroupTaxonomy row exists with matching upstream_taxon_id
         AND upstream_checksum is unchanged → log [SKIP] and continue
      c. Call _find_or_create_taxonomy() to get or create a local Taxonomy
      d. Add the Taxonomy to target_group.taxonomies with through_defaults
         (upstream_taxon_id, upstream_checksum, last_synced_at)
      e. Update through model row (checksum, synced_at, is_validated)
      f. Check for cancellation after each taxon
7.  Reconnect BIMS signals
8.  Update HarvestSession: status, finished=True, additional_data (totals)
```

---

## Import Modes

### `existing` mode

The session's `module_group` (set from the form's local taxon group selector)
is used directly as the target.

If the target group is **read-only** and has `upstream_url` / `upstream_id` set,
the task validates that the harvest source matches exactly. If the URL or group ID
differs, the task aborts with status `"Failed: upstream source mismatch for
read-only group"`. See [Read-only taxon groups](#read-only-taxon-groups).

### `new` mode

The task looks up or creates a local `TaxonGroup` by the remote group's name:

```python
TaxonGroup.objects.get_or_create(
    name=group_name,
    defaults={
        'category': 'SPECIES_MODULE',
        'site': Site.objects.get_current(),
        'is_readonly': mark_readonly,          # from form checkbox
        'upstream_url': base_url,              # if mark_readonly
        'upstream_id': str(remote_group_id),   # if mark_readonly
    }
)
```

If the group already exists (matched by name) and `mark_readonly` is `True`, the
task also fills in any missing `upstream_url` / `upstream_id` and sets
`is_readonly = True` on the existing group.

---

## Remote API Calls

All remote calls go through `bims/utils/bims_instance.py`.

| Function | Remote endpoint | Purpose |
|---|---|---|
| `normalize_bims_base_url(base_url)` | — | Strips trailing slashes |
| `get_taxon_groups(base_url)` | `GET /api/module-list/` | List available taxon groups |
| `get_taxa_page(base_url, group_id, page)` | `GET /api/taxa-list/` | One page of validated taxa |
| `get_all_taxa(base_url, group_id)` | (generator over `get_taxa_page`) | All taxa across pages |
| `get_taxon_by_id(base_url, taxon_id)` | `GET /api/taxon/<id>/` | Single taxon (for parent resolution) |

`get_taxa_page` always requests `validated=True&page_size=100`, so only validated
taxa are imported.

**Retry policy:** every call uses `_get_with_retry()`, which retries up to 3 times
with exponential back-off (`2^attempt` seconds) on any `requests.RequestException`.
A `REQUEST_TIMEOUT` of 30 seconds is applied to each attempt.

---

## Checksum-based Change Detection

Each taxon's canonical fields are hashed on every harvest run:

```python
def _compute_taxon_checksum(taxon_data) -> str:
    """SHA-256 of canonical_name, rank, author, taxonomic_status,
       gbif_key, parent, additional_data, tag_list."""
```

When a `TaxonGroupTaxonomy` row already exists with a matching `upstream_taxon_id`
and the stored `upstream_checksum` equals the newly computed value, the taxon is
logged as `[SKIP]` and no DB writes are performed. This makes re-harvests of
unchanged upstream data very cheap.

---

## Taxonomy Matching: `_find_or_create_taxonomy`

For each remote taxon dict the task calls `_find_or_create_taxonomy()`.

### Matching priority

1. **`upstream_taxon_id`** in `TaxonGroupTaxonomy` — if a target group is provided,
   look for an existing membership row whose `upstream_taxon_id` matches the remote
   taxon's `id`. This is the primary key for re-harvest matching.
2. **`gbif_key`** — if the remote taxon has a GBIF key, search for a local
   `Taxonomy` with the same key.
3. **`canonical_name + rank`** — case-insensitive exact match.
4. **Create** — if no match is found, a minimal `Taxonomy` record is created.

### Parent resolution

If the remote taxon has a `parent` field (remote taxon ID), the task fetches the
parent via `get_taxon_by_id()` and resolves it recursively (depth-first) before
saving the child. A `remote_cache` dict (`remote_id → local Taxonomy`) is shared
across the entire harvest run to avoid redundant API calls and infinite recursion.

An existing local taxonomy that is missing its `parent` is back-filled if the
remote provides one. For read-only groups the parent is always updated to match
upstream.

### `additional_data` merging

Conflict resolution differs by group type:

| Field | Non-readonly group | Read-only group |
|---|---|---|
| `additional_data` | Local values win; remote adds new keys only | Remote wins; overridden local keys logged as `[DIVERGENCE]` |
| `canonical_name`, `author`, `taxonomic_status` | Never updated after creation | Updated when remote differs; change is logged |
| `parent` | Back-filled only when missing locally | Always updated to match upstream |
| Tags | Additive only (never removed) | Additive only (never removed) |

### Tags

Remote `tag_list` (comma-separated, optionally with `(#RRGGBB)` colour suffixes)
is parsed by `_parse_tag_list()` using the regex `\s*\(#([0-9A-Fa-f]{3,6})\)\s*$`
and applied via `_apply_tags()`:

- Tags are always additive — existing local tags are never removed.
- If a tag carries a colour, the task finds or creates a `TagGroup` with that
  colour and associates the tag. Hex codes are normalised to uppercase `#RRGGBB`.

Example tag list: `"aquatic (#51FF3E), freshwater (#FF5733), endemic"`

---

## Read-only Taxon Groups

A taxon group can be marked as **read-only** to indicate that its species are
managed exclusively by harvesting from an upstream BIMS instance and must not
be edited locally.

### Fields on `TaxonGroup`

| Field | Type | Purpose |
|---|---|---|
| `is_readonly` | `BooleanField` | Blocks local editing of species in this group |
| `upstream_url` | `URLField(max_length=500)` | Base URL of the upstream BIMS instance |
| `upstream_id` | `CharField(max_length=100)` | ID of the corresponding taxon group on the upstream instance |

### Effect on editing

`EditTaxonView.test_func()` returns `False` (→ HTTP 403) for any taxon group
where `is_readonly=True`, regardless of whether the user is a superuser or an
expert. Neither GET nor POST is allowed.

### Effect on harvesting

In `existing` mode, if the target group is read-only and has upstream metadata,
the task compares:

- `target_group.upstream_url.rstrip('/')` vs `base_url.rstrip('/')`
- `target_group.upstream_id` vs `str(remote_group_id)`

If either differs, the task aborts immediately without importing any taxa.

### Setting a group as read-only

**Via the UI (new mode):** tick the **Mark as read-only** checkbox before
starting the harvest. The `mark_readonly` flag is stored in
`HarvestSession.additional_data` and applied when the new group is created.

**Via admin:** set `is_readonly`, `upstream_url`, and `upstream_id` directly on
the `TaxonGroup` record in the Django admin.

---

## TaxonGroupTaxonomy Through Model

The M2M relationship between `TaxonGroup` and `Taxonomy` uses the explicit through
model `TaxonGroupTaxonomy`. The harvester populates extra fields on this model for
each membership it creates or updates.

| Field | Type | Purpose |
|---|---|---|
| `upstream_taxon_id` | `CharField(max_length=100, db_index=True)` | Remote taxon `id`; primary re-harvest match key |
| `upstream_checksum` | `CharField(max_length=64)` | SHA-256 of canonical upstream payload at last harvest |
| `last_synced_at` | `DateTimeField(nullable)` | Timestamp of last harvest that touched this row |
| `is_validated` | `BooleanField(db_index=True)` | Driven by `SiteSetting.auto_validate_taxa_on_upload` |

`Meta.unique_together = ('taxongroup', 'taxonomy')`

---

## Session Lifecycle

`HarvestSession` records track every harvest run.

| Field | Meaning |
|---|---|
| `category` | Always `'bims'` for BIMS harvests |
| `harvester` | The user who started the harvest |
| `module_group` | The local `TaxonGroup` taxa are imported into |
| `is_fetching_species` | Set to `True` on creation |
| `status` | Human-readable progress string, updated every 50 taxa |
| `finished` | `True` when the task completes normally |
| `canceled` | `True` if the user clicks Cancel |
| `log_file` | Path to `harvest-bims-session-log/<id>-<timestamp>.txt` |
| `additional_data` | Config + final counts (see below) |
| `trigger` | `'manual'` (default) or `'scheduled'` |

### `additional_data` keys

| Key | Set by | Content |
|---|---|---|
| `base_url` | View (on submit) | Remote instance URL |
| `remote_group_id` | View | Remote group ID |
| `remote_group_name` | View | Remote group name |
| `import_mode` | View | `'existing'` or `'new'` |
| `mark_readonly` | View | `true`/`false` for new-mode groups |
| `finished_at` | Task (on finish) | ISO timestamp |
| `total_processed` | Task (on finish) | Number of taxa imported/updated |
| `total_skipped` | Task (on finish) | Number of taxa skipped (checksum unchanged) |

### Cancellation

The UI shows a **Cancel** button while a session is in progress. Clicking it
POSTs `cancel=True` and `canceled_session_id=<id>`. The view sets
`session.canceled = True`. After each taxon the task queries
`HarvestSession.objects.filter(id=session_id, canceled=True).exists()` and
stops the loop when the flag is set.

### Duration display

The finished-sessions list shown in the UI includes a `duration_display` field
computed from `session.start_time` and `additional_data['finished_at']`, formatted
as `Xh Ym Zs`.

---

## Auto-validation

When a new taxon membership is created the `is_validated` flag on the
`TaxonGroupTaxonomy` row is set according to
`preferences.SiteSetting.auto_validate_taxa_on_upload`. If that setting is `True`
the taxon is immediately marked as validated; otherwise it remains unvalidated
until reviewed.

---

## Data Flow Diagram

```
Browser
  │
  │  POST /harvest-bims/
  ▼
HarvestBimsSpeciesView.post()
  │  Creates HarvestSession (category='bims', is_fetching_species=True)
  │  Writes empty log file → MEDIA_ROOT/harvest-bims-session-log/<id>-<ts>.txt
  │
  │  .delay()
  ▼
harvest_bims_species (Celery, queue=update)
  │
  ├─ disconnect_bims_signals()
  ├─ Resolve TaxonGroup (existing or new)
  │
  ├─ get_all_taxa(base_url, remote_group_id)
  │     └─ GET <remote>/api/taxa-list/?taxonGroup=N&page=1…N&validated=True
  │
  └─ For each taxon:
        _compute_taxon_checksum() → SHA-256
        if TaxonGroupTaxonomy.upstream_checksum matches → [SKIP]
        else:
          _find_or_create_taxonomy()
            1. upstream_taxon_id lookup in TaxonGroupTaxonomy
            2. gbif_key lookup
            3. canonical_name + rank lookup
            4. create
          └─ GET <remote>/api/taxon/<parent_id>/  (if parent needed)
          target_group.taxonomies.add(taxonomy, through_defaults={…})
          TaxonGroupTaxonomy.objects.filter(…).update(checksum, synced_at, is_validated)
        check session.canceled
  │
  ├─ connect_bims_signals()
  └─ session.finished = True; write totals to additional_data

Browser polls GET /api/harvest-status/<id>/ every 1s
  └─ returns { status, log (last 50 lines), finished, module_group, start_time }
```
