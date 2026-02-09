# coding=utf-8
"""Taxa validation uploader view."""
from bims.views.data_upload import DataUploadView
from bims.tasks.taxa_validation import taxa_validation_task


class TaxaValidationUploadView(DataUploadView):
    """Taxa validation upload view.

    This view allows users to upload taxa CSV/XLS files for validation
    without actually importing them. It checks for:
    - Duplicate GBIF keys within the file
    - Duplicate FADA IDs within the file
    - Existing GBIF keys in the database
    - Existing FADA IDs in the database

    The output is a validated CSV with a _validation_status column.
    """
    template_name = 'taxa_validation_uploader.html'
    upload_task = taxa_validation_task
    category = 'taxa_validation'
