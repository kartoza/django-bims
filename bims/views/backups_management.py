# coding=utf-8
"""Backups management view
"""
import os
from django.views.generic import TemplateView
from django.http import Http404, HttpResponse
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin


class BackupsManagementView(
    UserPassesTestMixin,
    LoginRequiredMixin,
    TemplateView):

    template_name = 'backups_management.html'
    empty = {
        'id': '',
        'parent': '',
        'text': ''
    },

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        backup_file_path = request.POST.get('selected-file')
        if not backup_file_path:
            raise Http404('Missing backup file')
        if not os.path.exists(backup_file_path):
            raise Http404('File does not exist')
        file_name = os.path.basename(backup_file_path)
        with open(backup_file_path, 'rb') as backup_file:
            response = HttpResponse(backup_file, content_type='text/plain')
            response['Content-Disposition'] = (
                    'attachment; filename=' + file_name
            )
            return response

    def get_all_path(self, dir_name = ''):
        tree = []
        path = '/home/web/backups'
        if dir_name:
            path = os.path.join(path, dir_name)
        for file_name in os.listdir(path):
            tree.append({
                'id': os.path.join(path, file_name),
                'parent': '#' if not dir_name else path,
                'text': file_name,
                'type': 'file' if not os.path.isdir(
                    os.path.join(path, file_name)
                ) else 'folder'
            })
            if os.path.isdir(
                    os.path.join('/home/web/backups', dir_name, file_name)):
                tree.extend(
                    self.get_all_path(os.path.join(dir_name, file_name)))
        return tree

    def get_context_data(self, **kwargs):
        context = super(BackupsManagementView, self).get_context_data(**kwargs)
        context['data'] = self.get_all_path()
        return context
