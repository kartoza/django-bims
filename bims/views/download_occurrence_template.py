import csv
import os

import io

from bims.models.taxon_extra_attribute import TaxonExtraAttribute
from bims.models.taxon_group import TaxonGroup
from django.http.response import HttpResponseNotFound, HttpResponse
from preferences import preferences

from core.settings.utils import absolute_path


def download_occurrence_template(request):
    # Download csv occurrence template

    occurrence_template = preferences.SiteSetting.occurrence_upload_template
    taxon_group_id = request.GET.get('taxon_group', None)
    taxon_group_name = ''

    if taxon_group_id:
        try:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
            taxon_group_name = taxon_group.name
            if taxon_group.occurrence_upload_template:
                occurrence_template = taxon_group.occurrence_upload_template
        except TaxonGroup.DoesNotExist:
            pass

    if not occurrence_template:
        # Use static data
        occurrence_template = os.path.join(
            absolute_path('bims', 'static'),
            'data',
            'data_example.csv'
        )
    else:
        occurrence_template = occurrence_template.path

    if os.path.exists(occurrence_template):
        if occurrence_template.endswith('.csv'):
            open_mode = 'r'
        else:
            open_mode = 'rb'

        with open(occurrence_template, open_mode) as fh:
            data = fh.read()
            response = HttpResponse(
                data,
                content_type="application/vnd.ms-excel")
            response[
                'Content-Disposition'] = (
                    'inline; filename={module}-{filename}'.format(
                        module=taxon_group_name,
                        filename=os.path.basename(
                            occurrence_template
                        ))
                )
            return response

    return HttpResponseNotFound('Template not found')
