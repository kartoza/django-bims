# coding=utf-8
"""
Physico-chemical uploader view
"""
from bims.views.data_upload import DataUploadView
from bims.tasks.physico_chemical_upload import physico_chemical_upload


class PhysicoChemicalUploadView(DataUploadView):
    """Physico-chemical upload view."""
    template_name = 'physico_chemical_uploader.html'
    upload_task = physico_chemical_upload
    category = 'physico_chemical'
