from django.db.models import ForeignKey
from django.apps import apps
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from rest_framework import status
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.chemical_record import ChemicalRecord
from bims.models.survey import Survey
from bims.models.site_image import SiteImage
from bims.models.search_process import SearchProcess
from sass.models.site_visit import SiteVisit


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class MergeSites(APIView):
    """
    Merge multiple sites into one site
    """
    permission_classes = (IsSuperUser, )

    @staticmethod
    def update_sites(primary_site, secondary_sites):
        """
        Automatically finds models with a ForeignKey to LocationSite and updates them.
        :param primary_site: The site that remains after the merge.
        :param secondary_sites: List of sites to be merged into the primary site.
        :return: A dictionary with counts of updated records for each model.
        """
        updated_counts = {}
        models = apps.get_models()

        for model in models:
            for field in model._meta.get_fields():
                if isinstance(field, ForeignKey) and field.related_model == LocationSite:
                    site_identifier = field.name
                    secondary_sites_query = {f'{site_identifier}__in': secondary_sites}
                    primary_site_query = {f'{site_identifier}': primary_site}
                    merged_data = model.objects.filter(**secondary_sites_query)
                    count = merged_data.update(**primary_site_query)
                    if count > 0:
                        updated_counts[model._meta.label] = count

        return updated_counts

    def put(self, request, *args):
        primary_site_id = request.data.get('primary_site', None)
        merged_site_ids = request.data.get('merged_sites', None)
        query_url = request.data.get('query_url', None)

        if query_url:
            query_params = query_url.split('#search//')
            if len(query_params) > 1:
                SearchProcess.objects.filter(
                    query__contains=query_params[1]
                ).delete()

        if not primary_site_id or not merged_site_ids:
            return Response(
                'Missing primary or secondary sites',
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            location_site = LocationSite.objects.get(
                id=primary_site_id
            )
        except LocationSite.DoesNotExist:
            return Response(
                'Primary site does not exist',
                status=status.HTTP_400_BAD_REQUEST
            )

        merged_sites = LocationSite.objects.filter(
            id__in=merged_site_ids.split(',')
        ).exclude(
            id=location_site.id
        )

        if merged_sites.count() < 1:
            return Response(
                'Secondary sites do not exist',
                status=status.HTTP_400_BAD_REQUEST
            )

        update_results = self.update_sites(location_site, list(merged_sites))

        sites_removed = merged_sites.count()
        merged_sites.delete()

        update_results['sites_removed'] = sites_removed

        return Response(update_results, status=status.HTTP_200_OK)
