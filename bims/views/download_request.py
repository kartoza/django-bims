
# coding=utf-8
import ast
import errno
import json
import os
from datetime import datetime
from hashlib import sha256
from urllib.parse import urlparse, parse_qs

from django.conf import settings
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect

from bims.tasks import send_csv_via_email
from bims.tasks.collection_record import download_collection_record_task
from geonode.people.models import Profile
from bims.models.download_request import DownloadRequest
from bims.permissions.api_permission import (
    user_has_permission_to_validate,
)
from preferences import preferences


def _params_from_dashboard_url(download_request):
    """
    Derive download_params and download_path from dashboard_url when they are
    missing on the DownloadRequest.
    """
    if not download_request.dashboard_url:
        return None, None

    parsed = urlparse(download_request.dashboard_url)

    # Params live in the URL fragment as  #<prefix>/<key=val&key=val...>
    # e.g. #site-detail/taxon=&siteId=123&...
    # Fall back to the regular query string if the fragment is absent.
    fragment = parsed.fragment  # e.g. "site-detail/taxon=&siteId=123&..."
    if fragment:
        # Drop any leading path segment (everything up to and including the first '/')
        sep = fragment.find('/')
        param_string = fragment[sep + 1:] if sep != -1 else fragment
    else:
        param_string = parsed.query

    qs = parse_qs(param_string, keep_blank_values=False)
    params_dict = {
        k: v[0] if len(v) == 1 else v for k, v in qs.items()
    }
    params_dict['downloadRequestId'] = str(download_request.pk)
    username = (
        download_request.requester.username
        if download_request.requester else 'unknown'
    )
    query_string = json.dumps(params_dict) + datetime.today().strftime('%Y%m%d')
    filename = sha256(query_string.encode('utf-8')).hexdigest()
    folder = settings.PROCESSED_CSV_PATH
    path_folder = os.path.join(settings.MEDIA_ROOT, folder, username)
    try:
        os.makedirs(path_folder, exist_ok=True)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
    path_file = os.path.join(path_folder, filename)
    return path_file, params_dict


def dispatch_download_if_needed(download_request):
    if (
        not download_request.request_file and
        not download_request.progress and
        download_request.download_path and
        download_request.download_params
    ):
        download_collection_record_task.delay(
            download_request.download_path,
            download_request.download_params,
            send_email=True,
            user_id=download_request.requester_id,
        )


class DownloadRequestListView(
        UserPassesTestMixin,
        LoginRequiredMixin,
        ListView):

    model = DownloadRequest
    context_object_name = 'download_requests'
    template_name = 'download_request_list.html'
    paginate_by = 20

    def test_func(self):
        return self.request.user and not self.request.user.is_anonymous

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to view download requests')
        return super(DownloadRequestListView, self).handle_no_permission()

    def post(self, request, *args, **kwargs):
        if not user_has_permission_to_validate(self.request.user):
            raise Http404('User has no permission to approve download requests')
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
                if download_request.request_file:
                    send_csv_via_email.delay(
                        user_id=download_request.requester.id,
                        csv_file=download_request.request_file.path,
                        file_name=download_request.request_category,
                        approved=approved,
                        download_request_id=download_request.id
                    )
                else:
                    download_request.processing = True

                download_request.approved = True
                download_request.rejected = False
                download_request.save()
                dispatch_download_if_needed(download_request)
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
                download_request.processing = False
                download_request.approved = False
                download_request.rejected = True
                download_request.rejection_message = rejection_message
                download_request.save()
            except DownloadRequest.DoesNotExist:
                raise Http404('The request does not exist!')
        return HttpResponseRedirect(next_url)

    def get(self, request, *args, **kwargs):
        """Check GET request parameters validity and store them"""
        self.approved_or_rejected = self.request.GET.get(
            'approved_or_rejected', 'approved')
        requester = self.request.GET.get('requester', None)
        if requester:
            self.current_requester = int(requester)
        else:
            self.current_requester = None
        self.filter_date_to = self.request.GET.get('date_to', None)
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
        ctx['has_permission_to_approve'] = user_has_permission_to_validate(self.request.user)
        ctx['enable_download_request_approval'] = (
            preferences.SiteSetting.enable_download_request_approval
        )
        ctx['approval_required'] = (
            preferences.SiteSetting.enable_download_request_approval or
            preferences.SiteSetting.max_download_records > 0
        )

        if user_has_permission_to_validate(self.request.user):
            author_ids = DownloadRequest.objects.filter(
                requester_id__isnull=False).values_list(
                'requester__id', flat=True)
            author_ids = list(set(author_ids))
            authors_order = ('first_name', 'last_name')
            filtered_authors = Profile.objects.filter(id__in=author_ids)
            ctx['requesters'] = filtered_authors.order_by(*authors_order)
        else:
            ctx['requesters'] = [self.request.user]
        return ctx

    def get_queryset(self):
        """
        Add GET requests filters
        """
        # Base queryset
        qs = super(DownloadRequestListView, self).get_queryset()
        qs = qs.filter(requester__isnull=False)
        if not user_has_permission_to_validate(self.request.user):
            qs = qs.filter(requester=self.request.user)
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


class DownloadRequestDetailView(
        LoginRequiredMixin,
        UserPassesTestMixin,
        DetailView):

    model = DownloadRequest
    context_object_name = 'download_request'
    template_name = 'download_request_detail.html'

    def test_func(self):
        user = self.request.user
        if user.is_anonymous:
            return False
        obj = self.get_object()
        return user.is_staff or user.is_superuser or obj.requester == user

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to view this download request')
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['has_permission_to_approve'] = user_has_permission_to_validate(
            self.request.user)
        ctx['enable_download_request_approval'] = (
            preferences.SiteSetting.enable_download_request_approval
        )
        ctx['approval_required'] = (
            preferences.SiteSetting.enable_download_request_approval or
            preferences.SiteSetting.max_download_records > 0
        )
        referer = self.request.META.get('HTTP_REFERER', '')
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        if parsed.path == '/download-request/':
            back_url = parsed.path
            if parsed.query:
                back_url += '?' + parsed.query
        else:
            back_url = '/download-request/'
        ctx['back_url'] = back_url
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', '')
        download_request = self.get_object()

        if action == 'restart':
            if not (request.user.is_staff or request.user.is_superuser):
                raise Http404('User has no permission to restart downloads')
            if (
                download_request.resource_name != 'Occurrence Data' or
                download_request.resource_type not in ('CSV', 'XLS')
            ):
                raise Http404('Restart is only supported for Occurrence Data CSV/XLS downloads')

            try:
                if download_request.download_path and os.path.exists(
                        download_request.download_path):
                    os.remove(download_request.download_path)
            except OSError:
                pass

            download_request.progress = None
            download_request.progress_updated_at = None
            download_request.processing = True
            download_request.approved = True
            download_request.rejected = False
            download_request.rejection_message = ''
            download_request.save(
                update_fields=[
                    'progress', 'progress_updated_at', 'processing',
                    'approved', 'rejected', 'rejection_message'
                ])

            path_file = download_request.download_path
            params = download_request.download_params

            if not path_file or not params:
                path_file, params = _params_from_dashboard_url(download_request)
                if path_file and params:
                    download_request.download_path = path_file
                    download_request.download_params = params
                    download_request.save(
                        update_fields=['download_path', 'download_params'])

            if path_file and params:
                download_collection_record_task.delay(
                    path_file,
                    params,
                    send_email=True,
                    user_id=download_request.requester_id,
                )
            return HttpResponseRedirect(request.path)

        if not user_has_permission_to_validate(request.user):
            raise Http404('User has no permission to approve download requests')
        approved = ast.literal_eval(request.POST.get('approved', 'False'))
        if approved:
            if download_request.request_file:
                send_csv_via_email.delay(
                    user_id=download_request.requester.id,
                    csv_file=download_request.request_file.path,
                    file_name=download_request.request_category,
                    approved=True,
                    download_request_id=download_request.id
                )
            else:
                download_request.processing = True
            download_request.approved = True
            download_request.rejected = False
            download_request.save()
            dispatch_download_if_needed(download_request)
        else:
            rejection_message = request.POST.get('rejection_message', '')
            download_request.processing = False
            download_request.approved = False
            download_request.rejected = True
            download_request.rejection_message = rejection_message
            download_request.save()
        return HttpResponseRedirect(request.path)
