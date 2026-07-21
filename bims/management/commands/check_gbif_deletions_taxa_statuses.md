# Taxa check: status and detail reference

The taxa check queries the GBIF v2 `/species/match` API for each taxon
that has a `gbif_key` and belongs to at least one taxon group. It compares
the current GBIF backbone resolution against the locally stored `gbif_key`.

GBIF backbone keys are **not stable** across backbone rebuilds. The
`/species/{key}` endpoint keeps serving stale keys without any `deleted`
flag, so the check re-matches by name and compares the result.

A taxon produces no finding (is skipped) when GBIF confirms the stored key
is still the current backbone usage. Only mismatches and ambiguities are
reported.

---

## Statuses

### `stale_key`

The stored `gbif_key` no longer matches what GBIF considers the current
backbone usage for this taxon.

| Detail pattern | Cause |
|---|---|
| `Current backbone usageKey=<N> (matchType=<T>).` | Name matched cleanly (EXACT, FUZZY, etc.) but to a different key. The backbone was rebuilt and the taxon was reassigned a new key. |
| `Multiple equally-confident name matches; key lookup returned usageKey=<N>.` | GBIF could not pick one match by name (ambiguous). A direct key lookup resolved to a different key, confirming the stored one is superseded. |
| `HIGHERRANK match to "<name>"; key lookup returned usageKey=<N>.` | GBIF matched at a higher rank and the matched name is different from the local name. A direct key lookup resolved to a different key. |

**What to do:** Update `gbif_key` to the new `usageKey` shown in the
detail, then re-fetch `gbif_data` from the new key.

---

### `unresolved`

GBIF returned no usable backbone usage for this taxon. The stored key
cannot be confirmed as current or stale.

| Detail pattern | Cause |
|---|---|
| `GBIF /species/match returned no usage for the name.` | `/species/match` returned `matchType: NONE` without a special flag. The name is not recognised in the current backbone at all (e.g. the taxon was lumped into a synonym and the name was retired). |
| `Multiple equally-confident name matches; key lookup returned no usage.` | GBIF found multiple equally-confident name matches (`MULTIPLE_MATCHES_SAME_CONFIDENCE`) and could not decide. A direct key lookup by the stored key also returned nothing, so the stored key is no longer indexed. |
| `HIGHERRANK match to "<name>"; key lookup returned no usage.` | GBIF matched at a higher rank with a different name, and a direct key lookup by the stored key returned nothing either. |

**What to do:** These require manual review. The taxon may have been
synonymised, split, or retired from the backbone. Search GBIF directly for
the scientific name to find the current treatment.

---

## How the check works (decision tree)

```
match by scientific name
        |
        v
matchType == NONE?
   |
   +-- processingFlag MULTIPLE_MATCHES_SAME_CONFIDENCE?
   |      |
   |      +-- match by stored gbif_key
   |             |
   |             +-- key == stored key  --> skip (key still valid)
   |             +-- key != stored key  --> stale_key
   |             +-- no key returned    --> unresolved
   |
   +-- (no flag)  --> unresolved
        |
matchType == HIGHERRANK?
   |
   +-- matched name same/similar to local name?
   |      |
   |      +-- yes  --> skip (higher-rank match, name consistent)
   |      +-- no   --> match by stored gbif_key
   |                      |
   |                      +-- key == stored key  --> skip
   |                      +-- key != stored key  --> stale_key
   |                      +-- no key returned    --> unresolved
        |
matchType is anything else (EXACT, FUZZY, etc.)
   |
   +-- returned key == stored key  --> skip
   +-- returned key != stored key  --> stale_key
```
