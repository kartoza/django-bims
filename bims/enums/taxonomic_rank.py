from enum import Enum


class TaxonomicRank(Enum):

    DOMAIN = 'Domain'
    KINGDOM = 'Kingdom'
    PHYLUM = 'Phylum'
    SUBPHYLUM = 'SubPhylum'
    CLASS = 'Class'
    SUBCLASS = 'Sub Class'
    ORDER = 'Order'
    SUBORDER = 'Sub Order'
    INFRAORDER = 'Infra Order'
    SUPERFAMILY = 'Super Family'
    FAMILY = 'Family'
    SUBFAMILY = 'Sub Family'
    TRIBE = 'Tribe'
    SUBTRIBE = 'Sub Tribe'
    GENUS = 'Genus'
    SUBGENUS = 'Sub Genus'
    SPECIES = 'Species'
    SUBSPECIES = 'Sub Species'
    VARIETY = 'Variety'
    FORMA = 'Forma'

    @staticmethod
    def hierarchy():
        return [
            TaxonomicRank.DOMAIN,
            TaxonomicRank.KINGDOM,
            TaxonomicRank.PHYLUM,
            TaxonomicRank.CLASS,
            TaxonomicRank.ORDER,
            TaxonomicRank.SUBORDER,
            TaxonomicRank.INFRAORDER,
            TaxonomicRank.SUPERFAMILY,
            TaxonomicRank.FAMILY,
            TaxonomicRank.GENUS,
            TaxonomicRank.SUBGENUS,
            TaxonomicRank.SPECIES,
            TaxonomicRank.SUBSPECIES,
            TaxonomicRank.VARIETY
        ]
