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
    def update_sites(Model, site_identifier, primary_site, secondary_sites):
        """
        Query and then update the location site
        :param Model: Model to be updated
        :param site_identifier: The location_site field name in the Model
        :param primary_site: The one that becomes the site
        :param secondary_sites: Sites that will be merged to primary
        :return: Total records updated
        """
        secondary_sites_query = {
            f'{site_identifier}__in': secondary_sites
        }
        primary_site_query = {
            f'{site_identifier}': primary_site
        }
        merged_data = Model.objects.filter(
            **secondary_sites_query
        )
        merged_data_count = merged_data.count()
        merged_data.update(
            **primary_site_query
        )
        return merged_data_count

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

        # Update collection records
        collection_records_count = self.update_sites(
            BiologicalCollectionRecord,
            'site',
            location_site,
            merged_sites
        )

        # Update chemical records
        chemical_records_count = self.update_sites(
            ChemicalRecord,
            'location_site',
            location_site,
            merged_sites
        )

        # Update survey
        surveys_count = self.update_sites(
            Survey,
            'site',
            location_site,
            merged_sites
        )

        # Update site image
        site_images_count = self.update_sites(
            SiteImage,
            'site',
            location_site,
            merged_sites
        )

        # Update SASS site visit
        sass_site_visits_count = self.update_sites(
            SiteVisit,
            'location_site',
            location_site,
            merged_sites
        )

        sites_removed = merged_sites.count()
        merged_sites.delete()

        return Response({
            'records_updated': collection_records_count,
            'chemical_records_updated': chemical_records_count,
            'surveys_updated': surveys_count,
            'site_images_updated': site_images_count,
            'sass_site_visits_updated': sass_site_visits_count,
            'sites_removed': sites_removed
        }, status=status.HTTP_200_OK)
