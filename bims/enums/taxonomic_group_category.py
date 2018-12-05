from enum import Enum


class TaxonomicGroupCategory(Enum):
    """
    The taxonomic group category of taxon.
    """

    # Category based on module of collection e.g. Fish
    SPECIES_MODULE = 'Species Module'

    # Category based on class of the species e.g. Aves
    SPECIES_CLASS = 'Species Class'
