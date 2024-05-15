from enum import Enum


class TaxonomicRank(Enum):

    SUBSPECIES = 'Sub Species'
    SPECIES = 'Species'
    GENUS = 'Genus'
    FAMILY = 'Family'
    SUPERFAMILY = 'Super Family'
    ORDER = 'Order'
    CLASS = 'Class'
    SUBCLASS = 'Sub Class'
    PHYLUM = 'Phylum'
    SUBPHYLUM = 'SubPhylum'
    KINGDOM = 'Kingdom'
    DOMAIN = 'Domain'
    SUBORDER = 'Sub Order'
    INFRAORDER = 'Infra Order'
    SUBFAMILY = 'Sub Family'
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
            TaxonomicRank.SPECIES,
            TaxonomicRank.SUBSPECIES,
            TaxonomicRank.VARIETY
        ]
