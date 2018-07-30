from braces.views import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from django.http import HttpResponseForbidden


class CollectionUploadView(View, LoginRequiredMixin):

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseForbidden()

        try:
            species_name = request.POST['ud_species_name']
            location_site = request.POST['ud_location_site']
            collection_date = request.POST['udx_collection_date']
            collector = request.POST['ud_collector']
            category = request.POST['ud_category']
            notes = request.POST['ud_notes']
            return JsonResponse({
                'status':'success',
                'message': 'OK'})
        except KeyError as e:
            return JsonResponse({
                'status':'failed',
                'message': 'KeyError : ' + str(e)})
