from enum import Enum


class TaxonomicRank(Enum):
    # ─── Top-level ──────────────────────────────────────────────────────
    DOMAIN      = "Domain"
    KINGDOM     = "Kingdom"
    SUBKINGDOM  = "Sub Kingdom"

    # ─── Phylum ─────────────────────────────────────────────────────────
    PHYLUM      = "Phylum"
    SUBPHYLUM   = "SubPhylum"
    INFRAPHYLUM = "Infra Phylum"

    # ─── Class ──────────────────────────────────────────────────────────
    MEGACLASS   = "Mega Class"
    GIGACLASS   = "Giga Class"
    SUPERCLASS  = "Super Class"
    CLASS       = "Class"
    SUBCLASS    = "Sub Class"
    INFRACLASS  = "Infra Class"

    # ─── Order ──────────────────────────────────────────────────────────
    SUPERORDER  = "Super Order"
    ORDER       = "Order"
    SUBORDER    = "Sub Order"
    INFRAORDER  = "Infra Order"
    PARVORDER   = "Parv Order"

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
            TaxonomicRank.SUBKINGDOM,
            TaxonomicRank.PHYLUM,
            TaxonomicRank.SUBPHYLUM,
            TaxonomicRank.INFRAPHYLUM,
            TaxonomicRank.MEGACLASS,
            TaxonomicRank.GIGACLASS,
            TaxonomicRank.SUPERCLASS,
            TaxonomicRank.CLASS,
            TaxonomicRank.SUBCLASS,
            TaxonomicRank.INFRACLASS,
            TaxonomicRank.SUPERORDER,
            TaxonomicRank.ORDER,
            TaxonomicRank.SUBORDER,
            TaxonomicRank.INFRAORDER,
            TaxonomicRank.PARVORDER,
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