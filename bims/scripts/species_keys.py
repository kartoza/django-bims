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
SUBPHYLUM = 'SubPhylum'
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
FORMA = 'Forma'
TRIBE = 'Tribe'
SUBTRIBE = 'Sub Tribe'
SYNONYM = 'Synonym'
ACCEPTED_TAXON = 'Accepted Taxon'
SUBGENUS = 'Sub Genus'

TAXON_RANKS = [
    KINGDOM,
    PHYLUM,
    SUBPHYLUM,
    CLASS,
    SUBCLASS,
    ORDER,
    SUBORDER,
    FAMILY,
    SUBFAMILY,
    GENUS,
    SPECIES,
    SUBSPECIES,
    VARIETY,
    FORMA,
    TRIBE,
    SUBTRIBE,
    SUBGENUS,
]
ALL_TAXON_RANKS = [
    'KINGDOM',
    'PHYLUM',
    'SUBPHYLUM',
    'CLASS',
    'SUBCLASS',
    'ORDER',
    'SUBORDER',
    'FAMILY',
    'SUBFAMILY',
    'GENUS',
    'SPECIES',
    'SUBSPECIES',
    'VARIETY',
    'FORMA',
    'TRIBUE',
    'SUBTRIBE',
    'SUBGENUS',
]
PARENT_RANKS = {
    'KINGDOM': None,
    'PHYLUM': KINGDOM,
    'SUBPHYLUM': PHYLUM,
    'CLASS': PHYLUM,
    'SUBCLASS': CLASS,
    'ORDER': CLASS,
    'SUBORDER': ORDER,
    'FAMILY': ORDER,
    'SUBFAMILY': FAMILY,
    'GENUS': FAMILY,
    'SPECIES': GENUS,
    'SUBSPECIES': SPECIES,
    'VARIETY': SPECIES,
    'FORMA': SPECIES,
    'SUBTRIBE': TRIBE,
    'TRIBE': FAMILY,
    'SUBGENUS': GENUS,
}

def parent_rank(current_rank):
    current_rank = current_rank.upper()
    return PARENT_RANKS.get(current_rank)
