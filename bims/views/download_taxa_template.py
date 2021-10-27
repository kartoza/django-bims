import csv
import os

import io

from bims.models.taxon_extra_attribute import TaxonExtraAttribute
from bims.models.taxon_group import TaxonGroup
from django.http.response import HttpResponseNotFound, HttpResponse
from preferences import preferences

from core.settings.utils import absolute_path


def download_taxa_template(request):
    # Download csv taxa template

    taxa_template = preferences.SiteSetting.taxonomic_upload_template
    taxon_group_id = request.GET.get('taxon_group', None)
    taxon_extra_attributes = None
    taxon_group_name = ''

    if taxon_group_id:
        try:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
            taxon_group_name = taxon_group.name + '_'
            taxon_extra_attributes = list(TaxonExtraAttribute.objects.filter(
                taxon_group=taxon_group
            ).values_list('name', flat=True))
        except TaxonGroup.DoesNotExist:
            pass

    if not taxa_template:
        # Use static data
        taxa_template = os.path.join(
            absolute_path('bims', 'static'),
            'data',
            'taxa_sample.csv'
        )
    else:
        taxa_template = taxa_template.path

    if os.path.exists(taxa_template):
        with open(taxa_template, 'r') as fh:
            reader = csv.reader(fh)
            header = next(reader)

            if taxon_extra_attributes:
                for taxon_extra_attribute in taxon_extra_attributes:
                    if taxon_extra_attribute not in header:
                        header.append(taxon_extra_attribute)

            s = io.StringIO()
            csv.writer(s).writerow(header)
            s.seek(0)

            response = HttpResponse(
                s.read(),
                content_type="application/vnd.ms-excel")
            response[
                'Content-Disposition'] = (
                    'inline; filename={module}{filename}'.format(
                        module=taxon_group_name,
                        filename=os.path.basename(
                            taxa_template
                        ))
                )
            return response

    return HttpResponseNotFound('Template not found')
