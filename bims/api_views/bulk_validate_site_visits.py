# coding=utf-8
from bims.models.survey import Survey
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils.safestring import mark_safe
from django.db import transaction


class BulkValidateSiteVisits(UserPassesTestMixin, LoginRequiredMixin, APIView):
    """
    API view to validate multiple site visits at once.
    """

    def test_func(self):
        return self.request.user.has_perm('bims.can_validate_site_visit')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to validate collection data')
        return super(BulkValidateSiteVisits, self).handle_no_permission()

    def post(self, request):
        site_visit_ids = request.POST.getlist('site_visit_ids[]')

        if not site_visit_ids:
            return HttpResponse(
                'No site visits selected',
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_count = 0
        failed_count = 0
        failed_ids = []

        with transaction.atomic():
            for site_visit_id in site_visit_ids:
                try:
                    site_visit = Survey.objects.get(pk=site_visit_id)
                    if not site_visit.can_be_validated:
                        failed_count += 1
                        failed_ids.append(site_visit_id)
                        continue
                    site_visit.validate()
                    validated_count += 1
                except Survey.DoesNotExist:
                    failed_count += 1
                    failed_ids.append(site_visit_id)

        response_message = f'{validated_count} site visit(s) validated successfully.'
        if failed_count > 0:
            response_message += f' {failed_count} site visit(s) could not be validated.'

        messages.success(
            self.request,
            mark_safe(response_message),
            extra_tags='site_visit_validation'
        )

        return JsonResponse({
            'status': 'success',
            'validated_count': validated_count,
            'failed_count': failed_count,
            'failed_ids': failed_ids
        })


class BulkRejectSiteVisits(UserPassesTestMixin, LoginRequiredMixin, APIView):
    """
    API view to reject multiple site visits at once.
    """

    def test_func(self):
        return self.request.user.has_perm('bims.can_validate_site_visit')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to reject site visits')
        return super(BulkRejectSiteVisits, self).handle_no_permission()

    def post(self, request):
        site_visit_ids = request.POST.getlist('site_visit_ids[]')
        rejection_message = request.POST.get('rejection_message', '')

        if not site_visit_ids:
            return HttpResponse(
                'No site visits selected',
                status=status.HTTP_400_BAD_REQUEST
            )

        rejected_count = 0
        failed_count = 0
        failed_ids = []

        with transaction.atomic():
            for site_visit_id in site_visit_ids:
                try:
                    survey = Survey.objects.get(pk=site_visit_id)
                    survey.ready_for_validation = False
                    survey.reject(rejection_message=rejection_message)
                    survey.save()
                    rejected_count += 1
                except Survey.DoesNotExist:
                    failed_count += 1
                    failed_ids.append(site_visit_id)

        response_message = f'{rejected_count} site visit(s) rejected successfully.'
        if failed_count > 0:
            response_message += f' {failed_count} site visit(s) could not be rejected.'

        messages.success(
            self.request,
            mark_safe(response_message),
            extra_tags='site_visit_validation'
        )

        return JsonResponse({
            'status': 'success',
            'rejected_count': rejected_count,
            'failed_count': failed_count,
            'failed_ids': failed_ids
        })
