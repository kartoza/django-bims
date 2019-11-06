# coding=utf-8
"""CSV uploader view
"""

from django.urls import reverse_lazy
from bims.views.csv_upload import CsvUploadView as BaseCsvUploadView
from fish.models.fish_collection_record import FishCollectionRecord


class CsvUploadView(BaseCsvUploadView):
    """Csv upload view."""

    collection_record = FishCollectionRecord
    template_name = 'fish_csv_uploader.html'
    success_url = reverse_lazy('fish:fish-csv-upload')
    additional_fields = {
        'present': 'bool',
        'habitat': 'str'
    }
