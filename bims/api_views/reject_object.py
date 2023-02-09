# coding=utf-8
from bims.models.survey import Survey

from bims.models.taxonomy import Taxonomy

from bims.models.location_site import LocationSite
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.permissions.api_permission import AllowedTaxon


class RejectCollectionData(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        allowed_taxon = AllowedTaxon()
        taxon_list = allowed_taxon.get(self.request.user)
        collection_pk = self.request.GET.get('pk', None)
        if not collection_pk:
            return False
        collection = BiologicalCollectionRecord.objects.get(pk=collection_pk)
        return collection.taxonomy in taxon_list

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to validate collection data')
        return super(RejectCollectionData, self).handle_no_permission()

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        rejection_message = request.GET.get('rejection_message', None)
        try:
            collection = BiologicalCollectionRecord.objects.get(pk=object_pk)
            collection.reject(
                rejection_message=rejection_message
            )
            return JsonResponse({'status': 'success'})
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )


class RejectSiteVisit(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        return self.request.user.has_perm('bims.can_validate_site_visit')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to reject site vist')
        return super(RejectSiteVisit, self).handle_no_permission()

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        rejection_message = request.GET.get('rejection_message', None)
        try:
            survey = Survey.objects.get(pk=object_pk)
            survey.ready_for_validation = False
            survey.reject(
                rejection_message=rejection_message
            )
            survey.save()

            return JsonResponse({'status': 'success'})
        except Survey.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )


class RejectSite(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        site_pk = self.request.GET.get('pk', None)
        if not site_pk:
            return False
        site = LocationSite.objects.get(pk=site_pk)
        return site

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to validate location site')
        return super(RejectSite, self).handle_no_permission()

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        rejection_message = request.GET.get('rejection_message', None)
        try:
            site = LocationSite.objects.get(pk=object_pk)
            site.reject(
                rejection_message=rejection_message
            )
            return JsonResponse({'status': 'success'})
        except LocationSite.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )


class RejectTaxon(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        taxon_pk = self.request.GET.get('pk', None)
        if not taxon_pk:
            return False
        taxon = Taxonomy.objects.get(pk=taxon_pk)
        return taxon

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        rejection_message = request.GET.get('rejection_message', None)
        try:
            taxon = Taxonomy.objects.get(pk=object_pk)
            taxon.reject(
                rejection_message=rejection_message,
                show_redirect_url=False
            )
            # Check if taxon is associated with new site visit
            site_visits = Survey.objects.filter(
                id__in=taxon.biologicalcollectionrecord_set.values('survey')
            )
            unvalidated_site_visits = site_visits.filter(
                validated=False
            )

            if unvalidated_site_visits.exists():
                for unvalidated_site_visit in unvalidated_site_visits:
                    unvalidated_site_visit.reject('Taxon is rejected')

            # Check if taxon is not referenced to validated collection records
            if not site_visits.filter(
                validated=True
            ).exists():
                taxon.biologicalcollectionrecord_set.all().delete()
                taxon.delete()
            return JsonResponse({'status': 'success'})
        except LocationSite.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
