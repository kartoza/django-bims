# bims/scripts/taxa_upload_worms.py
import json
import logging
import re

from django.db import transaction
from preferences import preferences
from taggit.models import Tag

from bims.scripts.data_upload import DataCSVUpload
from bims.scripts.species_keys import *  # noqa
from bims.models import (
    Taxonomy, TaxonTag, SourceReference, SpeciesGroup
)
from bims.enums import TaxonomicRank
from .taxa_upload import TaxaProcessor  # wherever your TaxaProcessor lives

logger = logging.getLogger("bims")


HTML_TAG_RE = re.compile(r"<[^>]+>")
def _strip_html(s: str | None) -> str:
    if not s:
        return ""
    return HTML_TAG_RE.sub("", s).strip()


class WormsTaxaProcessor(TaxaProcessor):
    """Processor for WoRMS-formatted CSV rows."""

    RANK_MAP = {
        "kingdom": "KINGDOM",
        "phylum": "PHYLUM",
        "class": "CLASS",
        "infraclass": "INFRACLASS",
        "order": "ORDER",
        "family": "FAMILY",
        "subfamily": "SUBFAMILY",
        "superfamily": "SUPERFAMILY",
        "infraorder": "INFRAORDER",
        "genus": "GENUS",
        "subgenus": "SUBGENUS",
        "species": "SPECIES",
        "subspecies": "SUBSPECIES",
    }

    # WoRMS taxonomicStatus -> our taxonomy.taxonomic_status
    STATUS_MAP = {
        "accepted": "ACCEPTED",
        "unaccepted": "UNACCEPTED",
        "superseded combination": "SYNONYM",
        "alternative representation": "SYNONYM",
        "temporary name": "TEMPORARY NAME",
        "unavailable name": "UNAVAILABLE NAME",
    }

    # Column names used by WoRMS dumps (case-sensitive as they appear in files)
    C = {
        "aphia_id": "AphiaID",
        "sci_name": "ScientificName",
        "authority": "Authority",
        "aphia_id_acc": "AphiaID_accepted",
        "sci_name_acc": "ScientificName_accepted",
        "authority_acc": "Authority_accepted",
        "kingdom": "Kingdom",
        "phylum": "Phylum",
        "clazz": "Class",
        "order": "Order",
        "family": "Family",
        "subfamily": "Subfamily",
        "genus": "Genus",
        "subgenus": "Subgenus",
        "species": "Species",
        "subspecies": "Subspecies",
        "rank": "taxonRank",
        "marine": "Marine",
        "brackish": "Brackish",
        "fresh": "Fresh",
        "terrestrial": "Terrestrial",
        "status": "taxonomicStatus",
        "quality": "Qualitystatus",
        "unaccept_reason": "Unacceptreason",
        "date_modified": "DateLastModified",
        "lsid": "LSID",
        "parent_aphia": "Parent AphiaID",
        "path": "Storedpath",
        "citation": "Citation",
    }

    HABITAT_TAGS = [
        ("Marine", "Marine"),
        ("Brackish", "Brackish"),
        ("Fresh", "Freshwater"),
        ("Terrestrial", "Terrestrial"),
    ]

    def _boolish(self, v):
        """WoRMS habitat flags come as 1/0/''."""
        if v is None:
            return False
        s = str(v).strip().lower()
        return s in {"1", "true", "yes", "y"}

    def _map_rank(self, worms_rank: str | None) -> str | None:
        if not worms_rank:
            return None
        return self.RANK_MAP.get(worms_rank.strip().lower())

    def _compose_worms_scientific(self, row: dict, target_rank: str) -> tuple[str, str]:
        """Return (canonical_name, scientific_name) for the row."""
        sci = (self.row_value(row, self.C["sci_name"]) or "").strip()
        auth = _strip_html(row.get(self.C["authority"]))
        genus = (row.get(self.C["genus"]) or "").strip()
        species = (row.get(self.C["species"]) or "").strip()
        subspecies = (row.get(self.C["subspecies"]) or "").strip()

        # If rank is species/subspecies WoRMS often splits epithet; normalise
        if target_rank in {"SPECIES", "SUBSPECIES"}:
            base = sci or " ".join([p for p in [genus, species] if p])
            if target_rank == "SUBSPECIES" and subspecies:
                if subspecies not in base:
                    base = f"{base} {subspecies}"
            canonical = base
        else:
            canonical = sci or genus or (row.get(self.C["family"]) or "").strip()

        scientific = canonical
        # Append author if not already present
        if auth and auth not in scientific:
            scientific = f"{scientific} {auth}"

        return canonical, scientific

    def _ensure_parent_chain(self, row: dict, for_rank: str) -> Taxonomy | None:
        """
        Build/find parents up to immediate parent of `for_rank`.
        Returns the immediate parent Taxonomy or None.
        """
        # Ordered lineage from high to low
        lineage = [
            ("KINGDOM", row.get(self.C["kingdom"])),
            ("PHYLUM", row.get(self.C["phylum"])),
            ("CLASS", row.get(self.C["clazz"])),
            ("INFRACLASS", row.get(self.C["clazz"]) and None),  # optional slot
            ("ORDER", row.get(self.C["order"])),
            ("FAMILY", row.get(self.C["family"])),
            ("SUBFAMILY", row.get(self.C["subfamily"])),
            ("GENUS", row.get(self.C["genus"])),
            ("SUBGENUS", row.get(self.C["subgenus"])),
            ("SPECIES", row.get(self.C["species"])),
        ]

        # We only need up to the immediate parent rank of the target
        # Build a dict for quick position lookup
        idx = {r: i for i, (r, _) in enumerate(lineage)}
        if for_rank not in idx:
            return None
        stop_at = idx[for_rank] - 1  # parent slot
        if stop_at < 0:
            return None

        parent = None
        # Walk from top to the parent slot, creating/finding nodes
        for i in range(stop_at + 1):
            rank, name = lineage[i]
            if not name:
                continue
            name = str(name).strip()
            t = Taxonomy.objects.filter(
                canonical_name__iexact=name,
                rank=rank
            ).first()
            if not t:
                # Create placeholder
                t = Taxonomy.objects.create(
                    canonical_name=name,
                    scientific_name=name,
                    legacy_canonical_name=name,
                    rank=rank,
                    parent=parent
                )
            else:
                if t.parent_id != (parent.id if parent else None):
                    t.parent = parent
                    t.save()
            parent = t

        return parent

    def _attach_habitat_tags(self, taxonomy: Taxonomy, row: dict):
        """Turn habitat flags into tags."""
        for col, tag_label in self.HABITAT_TAGS:
            val = row.get(col) if col in row else row.get(self.C[col.lower()])
            if self._boolish(val):
                tag, _ = Tag.objects.get_or_create(name=tag_label)
                taxonomy.tags.add(tag)

    def _attach_citation(self, taxonomy: Taxonomy, row: dict):
        citation = _strip_html(row.get(self.C["citation"]))
        if not citation:
            return
        ref = SourceReference.create_source_reference(
            category=None, source_id=None, note=citation
        )
        taxonomy.source_reference = ref

    def process_worms_data(self, row: dict, taxon_group):
        """
        Process a single WoRMS CSV row into Taxonomy without using GBIF.
        """
        # Map rank
        worms_rank = row.get(self.C["rank"])
        rank = self._map_rank(worms_rank)
        if not rank:
            self.handle_error(row, f"Unsupported/empty taxonRank: {worms_rank}")
            return

        status_raw = (row.get(self.C["status"]) or "").strip()
        taxonomic_status = self.STATUS_MAP.get(status_raw.lower(), status_raw.upper() or None)

        # Accepted / synonym handling
        is_accepted = status_raw.lower() == "accepted"
        accepted_name = (row.get(self.C["sci_name_acc"]) or "").strip()
        accepted_auth = _strip_html(row.get(self.C["authority_acc"]))
        accepted_full = f"{accepted_name} {accepted_auth}".strip() if accepted_name else ""

        # Compose names
        canonical_name, scientific_name = self._compose_worms_scientific(row, rank)

        # Guard: parent must not be identical to child
        parent = self._ensure_parent_chain(row, rank)
        if parent and parent.canonical_name.lower() == canonical_name.lower():
            self.handle_error(row, "Parent cannot have the same name as the taxon")
            return

        # Create/find the main taxon
        taxonomy = Taxonomy.objects.filter(
            canonical_name__iexact=canonical_name
        ).first()
        if not taxonomy:
            taxonomy = Taxonomy.objects.create(
                canonical_name=canonical_name,
                scientific_name=scientific_name,
                legacy_canonical_name=canonical_name,
                rank=rank,
                parent=parent
            )
        else:
            # Update basics
            taxonomy.rank = rank
            if parent and taxonomy.parent_id != parent.id:
                taxonomy.parent = parent

        # Author
        authority = _strip_html(row.get(self.C["authority"]))
        if authority:
            taxonomy.author = authority

        # Taxonomic status
        if taxonomic_status:
            taxonomy.taxonomic_status = taxonomic_status

        # Accepted taxonomy linkage if not accepted
        if not is_accepted and accepted_name:
            acc = Taxonomy.objects.filter(
                canonical_name__iexact=accepted_name
            ).first()
            if not acc:
                # create minimal accepted node (parent chain will be filled on its own row later)
                acc = Taxonomy.objects.create(
                    canonical_name=accepted_name,
                    scientific_name=accepted_full or accepted_name,
                    legacy_canonical_name=accepted_name,
                    rank=rank
                )
            taxonomy.accepted_taxonomy = acc

        # Habitat tags (Marine/Brackish/Fresh/Terrestrial)
        self._attach_habitat_tags(taxonomy, row)

        # Source / citation
        self._attach_citation(taxonomy, row)

        # Extra metadata (keep Aphia/LSID/etc)
        extras = dict(row)
        taxonomy.additional_data = json.dumps(extras)

        taxonomy.save()

        # Add to group (respect auto-validate setting)
        auto_validate = preferences.SiteSetting.auto_validate_taxa_on_upload
        self.add_taxon_to_taxon_group(taxonomy, taxon_group, validated=auto_validate)

        # Hook for per-row finishing and success file
        self.finish_processing_row(row, taxonomy)


class WormsTaxaCSVUpload(DataCSVUpload, WormsTaxaProcessor):
    """
    CSV uploader that expects WoRMS columns and feeds them through WormsTaxaProcessor.
    Reuses success/error handling from your existing TaxaCSVUpload.
    """
    model_name = "taxonomy"

    def handle_error(self, row, message):
        self.error_file(error_row=row, error_message=message)

    def finish_processing_row(self, row, taxonomy):
        # mirror your TaxaCSVUpload.finish_processing_row
        taxon_group = self.upload_session.module_group
        if not taxon_group.taxonomies.filter(id=taxonomy.id).exists():
            taxon_group.taxonomies.add(taxonomy)
        taxonomy.import_date = self.upload_session.uploaded_at.date()
        taxonomy.save()
        self.success_file(row, taxonomy.id)

    def process_row(self, row):
        taxon_group = self.upload_session.module_group
        with transaction.atomic():
            self.process_worms_data(row, taxon_group)
