from bims.models.taxonomy import Taxonomy


def fix_taxa_without_modules():
    """
    This script will assign the species/taxon to the appropriate taxon group.
    This is based on the taxon group of their occurrences.
    """
    taxa = Taxonomy.objects.filter(
        taxongroup__isnull=True,
        biologicalcollectionrecord__module_group__isnull=False
    ).distinct()

    for index, taxon in enumerate(taxa, start=1):
        print(f'Updating {taxon} {index}/{len(taxa)}')
        taxon_group = taxon.biologicalcollectionrecord_set.first().module_group

        if taxon_group is not None:
            taxon_group.taxonomies.add(taxon)
        else:
            print(f'No taxon group found for {taxon}')
