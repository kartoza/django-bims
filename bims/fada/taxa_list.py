# coding=utf-8
"""
FADA-specific taxa list export configuration and utilities.
"""
from bims.scripts.species_keys import BIOGRAPHIC_DISTRIBUTIONS

# FADA-only additional_data keys (column names)
FADA_ADDITIONAL_KEYS = [
    'Taxonomic Comments',
    'Taxonomic References',
    'Biogeographic Comments',
    'Biogeographic References',
    'Environmental Comments',
    'Environmental References',
    'Conservation Comments',
    'Conservation References',
]

# Columns to exclude for FADA exports
FADA_EXCLUDED_COLUMNS = [
    'variety', 'Variety',
    'origin', 'Origin',
    'endemism', 'Endemism',
    'invasion', 'Invasion',
    'conservation_status_global', 'Conservation status global',
    'conservation_status_national', 'Conservation status national',
    'gbif_coordinate_uncertainty_m', 'Gbif coordinate uncertainty m',
    'gbif_coordinate_precision', 'Gbif coordinate precision',
    'cites_listing', 'Cites listing', 'CITES listing',
    # Scientific name and authority is excluded for FADA (author is separate)
    'scientific_name_and_authority', 'Scientific name and authority',
]

# Biogeographic distributions in alphabetical order
FADA_BIOGRAPHIC_ORDER = sorted(BIOGRAPHIC_DISTRIBUTIONS)


def get_environmental_tags_order():
    """
    Get the ordered list of environmental tag names from TagGroup.
    Tags are ordered by their TagGroup's order, then by the tag name within each group.
    """
    from bims.models import TagGroup

    ordered_tags = []
    for tag_group in TagGroup.objects.prefetch_related('tags').order_by('order'):
        for tag in tag_group.tags.all().order_by('name'):
            if tag.name not in ordered_tags:
                ordered_tags.append(tag.name)
    return ordered_tags


def reorder_headers_for_fada(headers):
    """
    Reorder headers for FADA export
    """
    headers = [h for h in headers if h not in FADA_EXCLUDED_COLUMNS]

    # Get environmental tags order from TagGroup
    environmental_tags_order = get_environmental_tags_order()

    biogeographic_comments = ['Biogeographic References', 'Biogeographic Comments']
    environmental_comments = ['Environmental References', 'Environmental Comments']
    # Taxonomic Reference before Taxonomic Comments
    taxonomic_comments = ['Taxonomic References', 'Taxonomic Comments']
    conservation_comments = ['Conservation Comments', 'Conservation References']

    base_headers = []
    biographic_headers = []
    environmental_headers = []

    for h in headers:
        if h in FADA_BIOGRAPHIC_ORDER:
            biographic_headers.append(h)
        elif h in environmental_tags_order:
            environmental_headers.append(h)
        elif h in FADA_ADDITIONAL_KEYS:
            continue
        else:
            base_headers.append(h)

    if 'fada_id' in base_headers and 'taxon_rank' in base_headers:
        taxon_rank_idx = base_headers.index('taxon_rank')
        base_headers.remove('fada_id')
        base_headers.insert(taxon_rank_idx, 'fada_id')

    if 'species_group' in base_headers and 'species' in base_headers:
        species_idx = base_headers.index('species')
        base_headers.remove('species_group')
        base_headers.insert(species_idx, 'species_group')

    if 'author' in base_headers and 'taxon' in base_headers:
        taxon_idx = base_headers.index('taxon')
        base_headers.remove('author')
        base_headers.insert(taxon_idx + 1, 'author')

    if 'accepted_taxon' in base_headers and 'taxonomic_status' in base_headers:
        taxonomic_status_idx = base_headers.index('taxonomic_status')
        base_headers.remove('accepted_taxon')
        base_headers.insert(taxonomic_status_idx + 1, 'accepted_taxon')

    biographic_headers = sorted(biographic_headers)

    # Sort environmental headers according to TagGroup order
    env_order_map = {tag: idx for idx, tag in enumerate(environmental_tags_order)}
    environmental_headers = sorted(
        environmental_headers,
        key=lambda x: env_order_map.get(x, len(environmental_tags_order))
    )

    result = []

    for h in base_headers:
        result.append(h)
        if h == 'accepted_taxon':
            for tc in taxonomic_comments:
                if tc in headers:
                    result.append(tc)
        if h == 'gbif_link':
            result.extend(biographic_headers)
            for bc in biogeographic_comments:
                if bc in headers:
                    result.append(bc)

    if 'fada_id' not in base_headers:
        result.extend(biographic_headers)
        for bc in biogeographic_comments:
            if bc in headers:
                result.append(bc)
    result.extend(environmental_headers)
    for ec in environmental_comments:
        if ec in headers:
            result.append(ec)

    for cc in conservation_comments:
        if cc in headers:
            result.append(cc)

    return result
