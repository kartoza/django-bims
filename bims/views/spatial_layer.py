import uuid

from braces.views import SuperuserRequiredMixin
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from cloud_native_gis.models import (
    Layer, LayerType, LayerUpload, UploadStatus
)


class SpatialLayerUploadView(SuperuserRequiredMixin, TemplateView):
    template_name = 'spatial_layer_upload.html'
    layer_type_name = 'Spatial Layer'

    parser_classes = (Layer,)

    def test_func(self):
        return self.request.user.has_perm('bims.add_boundary')

    def get_context_data(self, **kwargs):
        context = super(
            SpatialLayerUploadView, self).get_context_data(**kwargs)
        context['title'] = self.layer_type_name
        context['upload_sessions'] = LayerUpload.objects.exclude(status=UploadStatus.SUCCESS)
        uploaded_layers = LayerUpload.objects.filter(
            status=UploadStatus.SUCCESS
        ).order_by('-created_at')
        for session in uploaded_layers:
            session.maputnik_url = session.layer.maputnik_url(self.request)
        context['uploaded_layers'] = uploaded_layers
        return context

    def post(self, request, *args, **kwargs):
        unique_id = uuid.uuid4()
        name = request.POST.get('name')
        layer = Layer.objects.create(
            unique_id=unique_id,
            layer_type=LayerType.VECTOR_TILE,
            created_by=request.user,
            name=name
        )
        instance = LayerUpload(
            created_by=request.user, layer=layer
        )
        instance.emptying_folder()

        # Handle multiple files
        files = request.FILES.getlist('files')  # Get all uploaded files
        for file in files:
            FileSystemStorage(location=instance.folder).save(file.name, file)

        instance.save()

        messages.success(
            self.request,
            'Layer and files successfully uploaded and saved.',
            extra_tags='spatial_layer_upload')

        return HttpResponseRedirect(request.path_info)


class VisualizationLayerView(TemplateView):
    template_name = 'visualization_layers.html'
