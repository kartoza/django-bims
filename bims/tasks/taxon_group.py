# tasks.py
from celery import shared_task
from django.db.models import Count, Exists, OuterRef

from bims.cache import get_cache


@shared_task(bind=True, name='bims.tasks.delete_occurrences_by_taxon_group', queue='update')
def delete_occurrences_by_taxon_group(self, taxon_module_id):
    from bims.models.taxon_group import TaxonGroup, TAXON_GROUP_CACHE
    from bims.models.biological_collection_record import BiologicalCollectionRecord
    from bims.models.survey import Survey
    from bims.models.taxonomy import Taxonomy
    from bims.models.location_site import LocationSite
    from bims.models.location_context import LocationContext
    from bims.signals.utils import disconnect_bims_signals, connect_bims_signals

    try:
        taxon_group = TaxonGroup.objects.get(id=taxon_module_id)
    except TaxonGroup.DoesNotExist:
        return {'error': 'Taxon group does not exist'}

    disconnect_bims_signals()
    messages = {'success': 'OK'}

    # Collections associated with the taxon group
    collections = BiologicalCollectionRecord.objects.filter(module_group=taxon_group)
    total_collections = collections.count()

    # Surveys associated with the collections
    survey_ids = collections.values_list('survey_id', flat=True).distinct()

    # Taxa associated with the taxon group
    taxa_ids = taxon_group.taxonomies.all().values_list('id', flat=True)
    taxa = Taxonomy.objects.filter(id__in=taxa_ids)
    total_taxa = taxa.count()

    # Sites associated with the collections
    site_ids = list(collections.values_list('site_id', flat=True).distinct())

    def batch_delete(queryset):
        while queryset.exists():
            ids = list(queryset.values_list('id', flat=True)[:1000])
            queryset.filter(id__in=ids).delete()

    # Delete surveys
    surveys = Survey.objects.filter(id__in=survey_ids)
    total_surveys = surveys.count()
    if surveys.exists():
        batch_delete(surveys)
        messages['Surveys deleted'] = total_surveys

    # Delete collections
    if collections.exists():
        batch_delete(collections)
        messages['Collections deleted'] = total_collections

    # Clear taxon group associations
    if taxa.exists():
        taxon_group.taxonomies.clear()

        # Remove taxa with no occurrences and no child taxa
        total_taxa_deleted = 0
        # Loop to remove taxa without records and without children
        while True:
            # Find taxa with no records
            taxa_without_records = Taxonomy.objects.filter(
                id__in=taxa_ids
            ).annotate(
                num_records=Count('biologicalcollectionrecord'),
                has_children=Exists(
                    Taxonomy.objects.filter(parent=OuterRef('pk'))
                )
            ).filter(num_records=0, has_children=False)

            if not taxa_without_records.exists():
                break

            count_deleted = taxa_without_records.count()
            batch_delete(taxa_without_records)
            total_taxa_deleted += count_deleted

        if total_taxa_deleted > 0:
            messages['Taxa deleted'] = total_taxa_deleted

    # Delete sites without surveys or collections
    sites = LocationSite.objects.filter(id__in=site_ids)
    total_sites = sites.count()
    if sites.exists():
        # Filter sites that are not associated with any surveys or collections
        sites_to_delete = sites.filter(
            survey__isnull=True,
        )
        total_sites_to_delete = sites_to_delete.count()

        if sites_to_delete.exists():
            batch_delete(sites_to_delete)
            messages['Sites deleted'] = total_sites_to_delete

            # Delete associated location contexts
            location_contexts = LocationContext.objects.filter(site__in=sites_to_delete)
            batch_delete(location_contexts)

    # Delete the taxon group
    taxon_group.delete()

    connect_bims_signals()

    taxon_group_cache = get_cache(TAXON_GROUP_CACHE)
    if taxon_group_cache:
        update_taxon_group_cache(delete_first=True)

    return messages


@shared_task(bind=True, name='bims.tasks.update_taxon_group_cache', queue='update')
def update_taxon_group_cache(self, delete_first=False):
    from bims.serializers.taxon_serializer import TaxonGroupSerializer
    from bims.models.taxon_group import TaxonGroup, TAXON_GROUP_CACHE
    from bims.cache import delete_cache, set_cache
    taxa_groups_query = TaxonGroup.objects.filter(
        category='SPECIES_MODULE',
        parent__isnull=True
    ).order_by('display_order')
    taxon_groups_data = TaxonGroupSerializer(
        taxa_groups_query, many=True).data
    if delete_first:
        delete_cache(TAXON_GROUP_CACHE)
    set_cache(TAXON_GROUP_CACHE, taxon_groups_data)
