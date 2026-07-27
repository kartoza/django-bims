import os

from django.http import HttpResponse, HttpResponseNotFound
from preferences import preferences

from core.settings.utils import absolute_path


def download_water_temperature_template(request):
    template = preferences.SiteSetting.water_temperature_upload_template

    if template:
        template_path = template.path
    else:
        template_path = os.path.join(
            absolute_path('bims', 'static'),
            'data',
            'water_temperature_template.csv'
        )

    if not os.path.exists(template_path):
        return HttpResponseNotFound('Template not found')

    with open(template_path, 'rb') as fh:
        data = fh.read()

    response = HttpResponse(data, content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename=water_temperature_template.csv'
    )
    return response
