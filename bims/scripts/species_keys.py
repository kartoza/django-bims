ON_GBIF = 'On GBIF'
GBIF_LINK = 'GBIF Link'
GBIF_URL = 'GBIF URL'
TAXON = 'Taxon'
SPECIES = 'Species'
SPECIES_GROUP = 'Species group'
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
VERNACULAR_NAME = 'Vernacular name(s)'
VERNACULAR_NAME_LANG = 'Language'
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
AUTHORS = 'Author(s)'
BIOGRAPHIC_DISTRIBUTIONS = [
    'ANT', 'AT', 'AU', 'NA',
    'NT', 'OL', 'PA', 'PAC'
]
REFERENCES = 'References'

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
    'SUBGENUS': GENUS,
    'SPECIES_GROUP': GENUS,
    'SPECIES': GENUS,
    'SUBSPECIES': SPECIES,
    'VARIETY': SPECIES,
    'FORMA': SPECIES,
    'TRIBE': FAMILY,
    'SUBTRIBE': TRIBE,
}

ALL_TAXON_RANKS = list(
    PARENT_RANKS.keys()
)


def parent_rank(current_rank):
    current_rank = current_rank.upper()
    parent_rank_value = PARENT_RANKS.get(current_rank)
    if not parent_rank_value:
        parent_rank_value = ''
    return parent_rank_value
