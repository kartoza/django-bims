# tasks.py
from celery import shared_task



@shared_task(bind=True, name='bims.tasks.delete_occurrences_by_taxon_group', queue='update')
def delete_occurrences_by_taxon_group(self, taxon_module_id):
    from bims.models.taxon_group import (
        TaxonGroup,
    )
    from bims.models.biological_collection_record import (
        BiologicalCollectionRecord
    )
    from bims.models.survey import Survey
    from bims.models.taxonomy import Taxonomy
    from bims.models.location_site import LocationSite
    from bims.models.location_context import LocationContext

    from bims.signals.utils import (
        disconnect_bims_signals,
        connect_bims_signals
    )

    try:
        taxon_group = TaxonGroup.objects.get(id=taxon_module_id)
    except TaxonGroup.DoesNotExist:
        return {'error': 'Taxon group does not exist'}

    disconnect_bims_signals()
    messages = {
        'success': 'OK'
    }

    collections = (
        BiologicalCollectionRecord.objects.filter(
            module_group=taxon_group
        )
    )
    total_collections = collections.count()

    # -- Survey
    survey_ids = list(
        collections.values_list(
            'survey_id', flat=True).distinct('survey')
    )
    surveys = Survey.objects.filter(id__in=survey_ids)
    total_surveys = surveys.count()

    # -- Taxonomy
    taxa_ids = list(taxon_group.taxonomies.all().values_list(
        'id', flat=True
    ))
    taxa = Taxonomy.objects.filter(id__in=taxa_ids)
    total_taxa = taxa.count()

    # -- Sites
    site_ids = list(
        collections.values_list('site_id', flat=True).distinct('site'))
    sites = LocationSite.objects.filter(
        id__in=site_ids
    )
    total_sites = sites.count()

    def batch_delete(queryset):
        while queryset.exists():
            ids = list(queryset.values_list('id', flat=True)[:1000])
            queryset.filter(id__in=ids).delete()

    if collections.exists():
        batch_delete(collections)
        messages['Collections deleted'] = total_collections

    if surveys.exists():
        batch_delete(surveys)
        messages['Survey deleted'] = total_surveys

    if taxa.exists():
        taxon_group.taxonomies.clear()

    if sites.exists():
        sites = sites.filter(
            survey__isnull=True,
            biological_collection_record__isnull=True
        )
        batch_delete(sites)

        # -- Location Context
        location_contexts = LocationContext.objects.filter(
            site__in=sites
        )
        batch_delete(location_contexts)
        messages['Sites deleted'] = total_sites

    taxon_group.delete()

    connect_bims_signals()
    return messages
