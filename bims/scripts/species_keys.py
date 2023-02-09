ON_GBIF = 'On GBIF'
GBIF_LINK = 'GBIF Link'
GBIF_URL = 'GBIF URL'
TAXON = 'Taxon'
SPECIES = 'Species'
GENUS = 'Genus'
SUBFAMILY = 'SubFamily'
SUBORDER = 'SubOrder'
SUBCLASS = 'SubClass'
SUBSPECIES = 'SubSpecies'
FAMILY = 'Family'
ORDER = 'Order'
CLASS = 'Class'
PHYLUM = 'Phylum'
KINGDOM = 'Kingdom'
DIVISION = 'Division'
GROWTH_FORM = 'Growth form'
SCIENTIFIC_NAME = 'Scientific name and authority'
FORMER_SPECIES_NAME = 'Former scientific name'
COMMON_NAME = 'Common Name'
ENDEMISM = 'Endemism'
CONSERVATION_STATUS = 'Conservation status'
CONSERVATION_STATUS_GLOBAL = 'Conservation status global'
CONSERVATION_STATUS_NATIONAL = 'Conservation status national'
ORIGIN = 'Origin'
TAXON_RANK = 'Taxon Rank'
TAXONOMIC_STATUS = 'Taxonomic status'
VARIETY = 'Variety'

TAXON_RANKS = [
    KINGDOM,
    PHYLUM,
    CLASS,
    SUBCLASS,
    ORDER,
    SUBORDER,
    FAMILY,
    SUBFAMILY,
    GENUS,
    SPECIES,
    SUBSPECIES,
    VARIETY
]
ALL_TAXON_RANKS = [
    'KINGDOM',
    'PHYLUM',
    'CLASS',
    'SUBCLASS',
    'ORDER',
    'SUBORDER',
    'FAMILY',
    'SUBFAMILY',
    'GENUS',
    'SPECIES',
    'SUBSPECIES',
    'VARIETY'
]

def parent_rank(current_rank):
    if current_rank == KINGDOM:
        return None
    if current_rank == VARIETY:
        return SPECIES
    if current_rank == GENUS:
        return FAMILY
    if current_rank == FAMILY:
        return ORDER
    if current_rank == ORDER:
        return CLASS
    return TAXON_RANKS[TAXON_RANKS.index(current_rank) - 1]
