from django.db import transaction, IntegrityError
from django.db.models import ForeignKey
from django.apps import apps
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from rest_framework import status
from bims.models.location_site import LocationSite
from bims.models.search_process import SearchProcess


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
        Update all FKs to LocationSite from secondary_sites to primary_site.
        Special-case LocationContext to avoid (site, group) unique collisions.
        """
        updated_counts = {}

        with transaction.atomic():
            try:
                from bims.models.location_context import LocationContext

                primary_groups = list(
                    LocationContext.objects.filter(site=primary_site)
                    .values_list('group_id', flat=True)
                )

                if primary_groups:
                    deleted, _ = LocationContext.objects.filter(
                        site__in=secondary_sites,
                        group_id__in=primary_groups
                    ).delete()
                    if deleted:
                        updated_counts['bims.LocationContext (duplicates_deleted)'] = deleted

                moved = LocationContext.objects.filter(
                    site__in=secondary_sites
                ).update(site=primary_site)
                if moved:
                    updated_counts['bims.LocationContext'] = moved
            except Exception:
                pass

            for model in apps.get_models():
                if model._meta.label == 'bims.LocationContext':
                    continue

                for field in model._meta.get_fields():
                    if isinstance(field, ForeignKey) and getattr(field.remote_field, 'model', None) is LocationSite:
                        site_field = field.name
                        qs = model.objects.filter(**{f'{site_field}__in': secondary_sites})

                        if not qs.exists():
                            continue

                        try:
                            cnt = qs.update(**{site_field: primary_site})
                        except IntegrityError:
                            cnt = 0
                            skipped = 0
                            for pk in qs.values_list('pk', flat=True):
                                try:
                                    model.objects.filter(pk=pk).update(**{site_field: primary_site})
                                    cnt += 1
                                except IntegrityError:
                                    skipped += 1
                            if skipped:
                                updated_counts[f'{model._meta.label} (skipped_due_to_conflict)'] = skipped

                        if cnt:
                            updated_counts[model._meta.label] = updated_counts.get(model._meta.label, 0) + cnt

        return updated_counts

    def put(self, request, *args, **kwargs):
        primary_site_id = request.data.get('primary_site')
        merged_site_ids = request.data.get('merged_sites')
        query_url = request.data.get('query_url')

        if query_url:
            parts = query_url.split('#search//')
            if len(parts) > 1:
                SearchProcess.objects.filter(query__contains=parts[1]).delete()

        if not primary_site_id or not merged_site_ids:
            return Response('Missing primary or secondary sites', status=status.HTTP_400_BAD_REQUEST)

        try:
            primary_site = LocationSite.objects.get(id=primary_site_id)
        except LocationSite.DoesNotExist:
            return Response('Primary site does not exist', status=status.HTTP_400_BAD_REQUEST)

        ids = [i.strip() for i in str(merged_site_ids).split(',') if i.strip()]
        secondary_sites = LocationSite.objects.filter(id__in=ids).exclude(id=primary_site.id)

        if not secondary_sites.exists():
            return Response('Secondary sites do not exist', status=status.HTTP_400_BAD_REQUEST)

        update_results = self.update_sites(primary_site, list(secondary_sites))

        sites_removed = secondary_sites.count()
        secondary_sites.delete()
        update_results['sites_removed'] = sites_removed

        return Response(update_results, status=status.HTTP_200_OK)
