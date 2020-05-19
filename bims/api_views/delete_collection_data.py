from django.views.generic.base import View
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from bims.models.biological_collection_record import BiologicalCollectionRecord


class CollectionDeleteApiView(UserPassesTestMixin, View):
    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        col_id = self.kwargs.get('col_id', None)
        if not col_id:
            return False
        return BiologicalCollectionRecord.objects.filter(
            Q(owner=self.request.user) | Q(collector_user=self.request.user),
            id=col_id).exists()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(
            CollectionDeleteApiView, self).dispatch(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        collection_record = get_object_or_404(
            BiologicalCollectionRecord,
            id=kwargs.get('col_id', None)
        )
        next_path = request.GET.get('next', reverse('map-page'))
        collection_record.delete()
        messages.success(
            request,
            'Collection record successfully deleted!',
            extra_tags='collection_record')
        redirect_url = next_path
        return HttpResponseRedirect(redirect_url)
