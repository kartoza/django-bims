
# coding=utf-8
import ast
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from geonode.people.models import Profile
from bims.models.download_request import DownloadRequest
from bims.permissions.api_permission import (
    user_has_permission_to_validate,
)


class DownloadRequestListView(
        UserPassesTestMixin,
        LoginRequiredMixin,
        ListView):

    model = DownloadRequest
    context_object_name = 'download_requests'
    template_name = 'download_request_list.html'
    paginate_by = 10

    def test_func(self):
        return user_has_permission_to_validate(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to approve download request')
        return super(DownloadRequestListView, self).handle_no_permission()

    def post(self, request, *args, **kwargs):
        approved = ast.literal_eval(
            request.POST.get('approved', 'False')
        )
        next_url = request.POST.get('next', '/')
        if approved:
            approved_id = request.POST.get('approved_id')
            if not approved_id:
                raise Http404('Missing approved id!')
            try:
                download_request = DownloadRequest.objects.get(
                    id=int(approved_id)
                )
                download_request.approved = True
                download_request.rejected = False
                download_request.save()
            except DownloadRequest.DoesNotExist:
                raise Http404('The request does not exist!')
        else:
            rejected_id = request.POST.get('rejected_id')
            rejection_message = request.POST.get('rejection_message', '')
            if not rejected_id:
                raise Http404('Missing rejected id!')
            try:
                download_request = DownloadRequest.objects.get(
                    id=int(rejected_id)
                )
                download_request.approved = False
                download_request.rejected = True
                download_request.rejection_message = rejection_message
                download_request.save()
            except DownloadRequest.DoesNotExist:
                raise Http404('The request does not exist!')
        return HttpResponseRedirect(next_url)

    def get(self, request, *args, **kwargs):
        """Check GET request parameters validity and store them"""

        # -- Filter approved or rejected
        self.approved_or_rejected = self.request.GET.get(
            'approved_or_rejected', None)

        # -- Requester
        requester = self.request.GET.get('requester', None)
        if requester:
            self.current_requester = int(requester)
        else:
            self.current_requester = None

        # -- Date to
        self.filter_date_to = self.request.GET.get('date_to', None)

        # -- Date from
        self.filter_date_from = self.request.GET.get('date_from', None)

        return super(DownloadRequestListView, self).get(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Get the context data which is passed to a template.

        :param kwargs: Any arguments to pass to the superclass.
        :type kwargs: dict

        :returns: Context data which will be passed to the template.
        :rtype: dict
        """
        ctx = super(
            DownloadRequestListView, self).get_context_data(**kwargs)
        ctx['approved_or_rejected'] = self.approved_or_rejected
        ctx['current_requester'] = self.current_requester

        # Requester (from selected entries)
        author_ids = DownloadRequest.objects.filter(
            requester_id__isnull=False).values_list(
            'requester__id', flat=True)
        author_ids = list(set(author_ids))
        authors_order = ('first_name', 'last_name')
        filtered_authors = Profile.objects.filter(id__in=author_ids)
        ctx['requesters'] = filtered_authors.order_by(*authors_order)

        return ctx

    def get_queryset(self):
        """
        Add GET requests filters
        """
        # Base queryset
        qs = super(DownloadRequestListView, self).get_queryset()

        if (
                self.approved_or_rejected is not None and
                self.approved_or_rejected != ''
        ):
            if self.approved_or_rejected == 'approved':
                qs = qs.filter(approved=True)
            elif self.approved_or_rejected == 'rejected':
                qs = qs.filter(rejected=True)
        else:
            qs = qs.filter(approved=False, rejected=False)
        if self.current_requester is not None:
            qs = qs.filter(requester__id=self.current_requester)
        if self.filter_date_from:
            qs = qs.filter(request_date__gte=self.filter_date_from)
        if self.filter_date_to:
            qs = qs.filter(request_date__lte=self.filter_date_to)

        # Return filtered queryset
        return qs
