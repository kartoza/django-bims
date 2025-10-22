from enum import Enum


class TaxonomicRank(Enum):
    # ─── Top-level ──────────────────────────────────────────────────────
    DOMAIN      = "Domain"
    KINGDOM     = "Kingdom"

    # ─── Phylum ─────────────────────────────────────────────────────────
    PHYLUM      = "Phylum"
    SUBPHYLUM   = "SubPhylum"

    # ─── Class ──────────────────────────────────────────────────────────
    SUPERCLASS  = "Super Class"
    CLASS       = "Class"
    SUBCLASS    = "Sub Class"

    # ─── Order ──────────────────────────────────────────────────────────
    SUPERORDER  = "Super Order"
    ORDER       = "Order"
    SUBORDER    = "Sub Order"
    INFRAORDER  = "Infra Order"

    # ─── Family & below ────────────────────────────────────────────────
    SUPERFAMILY = "Super Family"
    FAMILY      = "Family"
    SUBFAMILY   = "Sub Family"
    TRIBE       = "Tribe"
    SUBTRIBE    = "Sub Tribe"
    GENUS       = "Genus"
    SUBGENUS    = "Sub Genus"
    SPECIES     = "Species"
    SUBSPECIES  = "Sub Species"
    VARIETY     = "Variety"
    FORMA       = "Forma"

    FORM        = "Forma"

    # ------------------------------------------------------------------ #
    #  Ordered from highest → lowest rank
    # ------------------------------------------------------------------ #
    @staticmethod
    def hierarchy():
        return [
            TaxonomicRank.DOMAIN,
            TaxonomicRank.KINGDOM,
            TaxonomicRank.PHYLUM,
            TaxonomicRank.SUBPHYLUM,
            TaxonomicRank.SUPERCLASS,
            TaxonomicRank.CLASS,
            TaxonomicRank.SUBCLASS,
            TaxonomicRank.SUPERORDER,
            TaxonomicRank.ORDER,
            TaxonomicRank.SUBORDER,
            TaxonomicRank.INFRAORDER,
            TaxonomicRank.SUPERFAMILY,
            TaxonomicRank.FAMILY,
            TaxonomicRank.SUBFAMILY,
            TaxonomicRank.TRIBE,
            TaxonomicRank.SUBTRIBE,
            TaxonomicRank.GENUS,
            TaxonomicRank.SUBGENUS,
            TaxonomicRank.SPECIES,
            TaxonomicRank.SUBSPECIES,
            TaxonomicRank.VARIETY,
            TaxonomicRank.FORMA,
        ]