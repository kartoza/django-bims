from enum import Enum


class TaxonomicGroupCategory(Enum):
    """
    The taxonomic group category of taxon.
    """

    # Category based on module of collection e.g. Fish
    SPECIES_MODULE = 'Species Module'

    # Category based on class of the species e.g. Aves
    SPECIES_CLASS = 'Species Class'

    # Category for SASS Taxon Group Weight
    SASS_TAXON_GROUP = 'SASS Taxon Group'

    # Division group
    DIVISION_GROUP = 'Division Group'

    # For FADATim

    # Organism
    LEVEL_1_GROUP = 'Level 1'

    # Regions and/or ecosystem type
    LEVEL_2_GROUP = 'Level 2'

    # Country
    LEVEL_3_GROUP = 'Level 3'
