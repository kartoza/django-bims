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
    KINGDOM = 'Kingdom'
    DOMAIN = 'Domain'
    LIFE = 'Life'
    CULTIVAR_GROUP = 'Cultivar Group'
    SUBORDER = 'Sub Order'
    INFRAORDER = 'Infra Order'
    SUBFAMILY = 'Sub Family'

    @staticmethod
    def hierarchy():
        return [
            TaxonomicRank.LIFE,
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
            TaxonomicRank.CULTIVAR_GROUP
        ]
