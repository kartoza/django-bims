from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.response import JsonResponse, Http404
from rest_framework.views import APIView
from preferences import preferences
from bims.models import (
    TaxonGroup,
    Taxonomy,
    BiologicalCollectionRecord,
    Survey,
    LocationSite,
    LocationContext
)


class RemoveOccurrencesApiView(UserPassesTestMixin, APIView):

    # Only superuser allow to call this api
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args):
        if not preferences.SiteSetting.enable_remove_all_occurrences_tool:
            raise Http404('Not allowed')
        taxon_module_id = request.GET.get('taxon_module', None)
        taxon_group = None
        if taxon_module_id:
            try:
                taxon_group = TaxonGroup.objects.get(id=taxon_module_id)
            except TaxonGroup.DoesNotExist:
                return JsonResponse({'error': 'Taxon group does not exist'})

        messages = {
            'success': 'OK'
        }
        if taxon_group:
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

            # -- Location Context
            location_contexts = LocationContext.objects.filter(
                site__in=sites
            )

            if collections.exists():
                collections._raw_delete(collections.db)
                messages['Collections deleted'] = total_collections

            if surveys.exists():
                surveys._raw_delete(surveys.db)
                messages['Survey deleted'] = total_surveys

            if taxa.exists():
                taxon_group.taxonomies.clear()
                taxa = taxa.filter(
                    biologicalcollectionrecord__isnull=True
                )
                taxa_with_vernacular = taxa.filter(
                    vernacular_names__isnull=False)
                for taxon_with_vernacular in taxa_with_vernacular:
                    taxon_with_vernacular.vernacular_names.clear()
                taxa._raw_delete(taxa.db)
                messages['Taxa deleted'] = total_taxa

            if sites.exists():
                location_contexts._raw_delete(location_contexts.db)
                sites = sites.filter(
                    survey__isnull=True,
                    biological_collection_record__isnull=True
                )
                sites._raw_delete(sites.db)
                messages['Sites deleted'] = total_sites

            taxon_group.delete()

        return JsonResponse(messages)
