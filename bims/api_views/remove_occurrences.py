from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.response import JsonResponse, Http404
from rest_framework.views import APIView
from preferences import preferences
from bims.models import (
    TaxonGroup,
)
from bims.tasks.taxon_group import delete_occurrences_by_taxon_group


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

        task = delete_occurrences_by_taxon_group.delay(taxon_module_id)

        return JsonResponse({'status': 'Task initiated', 'task_id': task.id})
