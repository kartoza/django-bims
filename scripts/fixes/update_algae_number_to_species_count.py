from bims.models import BiologicalCollectionRecord


bio = BiologicalCollectionRecord.objects.filter(
    module_group__name__iexact='algae',
    abundance_type__iexact='number'
)

print('Updating {} records'.format(bio.count()))

bio.update(abundance_type='species_valve_per_frustule_count')

print('Finished')
