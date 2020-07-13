# coding=utf-8
"""Taxa uploader view
"""
from bims.views.data_upload import DataUploadView
from bims.tasks.taxa_upload import taxa_upload


class TaxaUploadView(DataUploadView):
    """Taxa upload view."""
    template_name = 'taxa_uploader.html'
    upload_task = taxa_upload
    category = 'taxa'
